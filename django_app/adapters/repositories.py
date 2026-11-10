from django.db import IntegrityError
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from business_logic.domain.exceptions import (DomainDoesNotExist,
                                              CartDoesNotExist,
                                              OptimisticLockError,
                                              CartAlreadyExist,
                                              OrderDoesNotExist,
                                              AllocationDoesNotExist,
                                              AllocationAlreadyExist)
from business_logic.domain.models import (Person,
                                          Order,
                                          Cart,
                                          Product,
                                          InventoryItem,
                                          Allocation,
                                          ReservedInventoryItem)
from business_logic.service_layer.ports.repositories import (AbstractPersonRepository,
                                                             AbstractOrderRepository,
                                                             AbstractCartRepository,
                                                             AbstractProductRepository,
                                                             AbstractInventoryItemRepository,
                                                             AbstractAllocationRepository)
from django_app.models import (PersonModel,
                               ProductModel,
                               CartLineModel,
                               CartModel,
                               OrderLineModel,
                               OrderModel,
                               InventoryItemModel,
                               ReservedInventoryItemModel,
                               AllocationModel, BaseAggregateModel)
from django_app.adapters.mappers import (person_to_domain,
                                         product_to_domain,
                                         cart_to_domain,
                                         order_to_domain,
                                         inventory_items_to_domain,
                                         allocation_to_domain,
                                         status_to_db)


def get_object_or_raise_except(model, select_related_fields=None, **filters):
    queryset = model.objects.all()

    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)

    try:
        return queryset.get(**filters)
    except model.DoesNotExist as exc:
        entities = ", ".join(f'{k}={v}' for k, v in filters.items())
        raise DomainDoesNotExist(f'{model.__name__} does not exist: {entities}') from exc


def apply_optimistic_lock(aggregate_model: type[BaseAggregateModel], current_version: int, **filters):
    next_version = current_version + 1
    affected_rows = (aggregate_model.objects
                     .filter(version_number=current_version, **filters)
                     .update(version_number=next_version))

    if affected_rows == 0:
        raise OptimisticLockError()


"""Раздел магазина."""


class DjangoPersonRepository(AbstractPersonRepository):

    def get_person_by_id(self, person_id: str) -> Person:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=person_id)
        return person_to_domain(person_orm)

    def save_person(self, person: Person) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=person.person_id)
        person_orm.domain_id = person.person_id
        person_orm.first_name = person.first_name
        person_orm.last_name = person.last_name
        person_orm.email = person.email
        person_orm.save()


class DjangoProductRepository(AbstractProductRepository):

    def get_product_by_sku(self, sku: str) -> Product:
        product_orm = get_object_or_raise_except(ProductModel, sku=sku)
        return product_to_domain(product_orm)

    def save_product(self, product: Product) -> None:
        product_orm = get_object_or_raise_except(ProductModel, sku=product.sku)
        product_orm.sku = product.sku
        product_orm.name = product.name
        product_orm.unit_price = product.unit_price
        product_orm.save()


class DjangoCartRepository(AbstractCartRepository):

    def create_cart(self, cart: Cart) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=cart.person.person_id)

        try:
            cart_orm = CartModel.objects.create(person=person_orm)
        except IntegrityError:
            raise CartAlreadyExist(cart.person.person_id)

        if cart.cart_lines:
            model_lines = []
            for cart_line in cart.cart_lines.values():
                product_orm = get_object_or_raise_except(ProductModel, sku=cart_line.product.sku)
                model_lines.append(
                    CartLineModel(
                        cart=cart_orm,
                        product=product_orm,
                        quantity=cart_line.quantity
                    )
                )
            CartLineModel.objects.bulk_create(model_lines)

        self._add_aggregate_to_seen(cart)

    def get_cart_by_person(self, person_id: str) -> Cart:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=person_id)

        try:
            cart_orm = get_object_or_raise_except(CartModel, person=person_orm)
        except DomainDoesNotExist:
            raise CartDoesNotExist(person_id)

        cart_lines_orm = CartLineModel.objects.filter(cart=cart_orm).select_related('product')

        return cart_to_domain(person_orm, cart_orm, cart_lines_orm)

    @classmethod
    def _save_cart_lines(cls, cart: Cart, cart_orm: CartModel) -> None:
        existing_lines = {
            line_orm.product.sku: line_orm
            for line_orm in CartLineModel.objects.filter(cart=cart_orm).select_related('product')
        }

        preferred_lines = {
            line.product.sku: line
            for line in cart.cart_lines.values()
        }

        CartLineModel.objects.filter(cart=cart_orm).exclude(product__sku__in=preferred_lines.keys()).delete()

        line_for_created = []
        line_for_updated = []

        for sku, line in preferred_lines.items():
            if sku not in existing_lines:
                product_orm = get_object_or_raise_except(ProductModel, sku=sku)
                line_orm_new = CartLineModel(cart=cart_orm, product=product_orm, quantity=line.quantity)
                line_for_created.append(line_orm_new)
            else:
                line_orm = existing_lines[sku]
                if line_orm.quantity != line.quantity:
                    line_orm.quantity = line.quantity
                    line_for_updated.append(line_orm)
        if line_for_created:
            CartLineModel.objects.bulk_create(line_for_created)
        CartLineModel.objects.bulk_update(line_for_updated, fields=['quantity'])

    def save_cart(self, cart: Cart) -> None:
        try:
            cart_orm = get_object_or_raise_except(CartModel, person__domain_id=cart.person.person_id)
        except DomainDoesNotExist:
            raise CartDoesNotExist(cart.person.person_id)

        try:
            apply_optimistic_lock(CartModel, cart.version_number, person__domain_id=cart.person.person_id)
        except OptimisticLockError:
            raise OptimisticLockError()

        cart_orm.refresh_from_db()
        self._save_cart_lines(cart, cart_orm)

        cart.increment_version()
        self._add_aggregate_to_seen(cart)


class DjangoOrderRepository(AbstractOrderRepository):

    def create_order(self, order: Order) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=order.person_id)

        order_orm = OrderModel.objects.create(
            domain_id=order.order_id,
            person=person_orm,
            final_price=order.final_price,
            status=status_to_db(order.status)
        )

        model_lines = []
        for order_line in order.order_lines.values():
            model_lines.append(
                OrderLineModel(
                    order=order_orm,
                    product_sku=order_line.product_sku,
                    product_name=order_line.product_name,
                    quantity=order_line.quantity,
                    line_price=order_line.line_price
                )
            )
        OrderLineModel.objects.bulk_create(model_lines)

        self._add_aggregate_to_seen(order)

    def get_order_by_id(self, order_id: str) -> Order:
        order_orm = get_object_or_raise_except(OrderModel, select_related_fields=['person'], domain_id=order_id)
        order_lines_orm = OrderLineModel.objects.filter(order=order_orm)
        return order_to_domain(order_orm, order_lines_orm)

    def save_order(self, order: Order) -> None:
        """При существующем заказе у него может меняться только поле статуса. """
        try:
            order_orm = get_object_or_raise_except(OrderModel, domain_id=order.order_id)
        except DomainDoesNotExist:
            raise OrderDoesNotExist(order.order_id)

        try:
            apply_optimistic_lock(OrderModel, order.version_number, domain_id=order.order_id)
        except OptimisticLockError:
            raise OptimisticLockError()

        order_orm.refresh_from_db()
        order_orm.status = status_to_db(order.status)
        order_orm.save()

        order.increment_version()
        self._add_aggregate_to_seen(order)


"""Раздел склада."""


class DjangoInventoryItemRepository(AbstractInventoryItemRepository):

    def get_inv_items_by_sku(self, sku_list: list[str]) -> dict[tuple[str, str], InventoryItem]:
        items_orm = InventoryItemModel.objects.filter(sku__in=sku_list)
        return inventory_items_to_domain(items_orm)

    def get_inv_items_by_sku_for_update(self,  sku_list: list[str]) -> dict[tuple[str, str], InventoryItem]:
        items_orm = InventoryItemModel.objects.select_for_update().filter(sku__in=sku_list)
        return inventory_items_to_domain(items_orm)

    def save_inv_items(self, inventory_items: dict[tuple[str, str], InventoryItem]) -> None:
        rows = [
            InventoryItemModel(
                sku=sku, warehouse_id=wh_id,
                physical_quantity=item.physical_quantity,
                reserved_quantity=item.reserved_quantity,
                version_number=item.version_number + 1
            )
            for (sku, wh_id), item in inventory_items.items()
        ]
        InventoryItemModel.objects.bulk_update(rows,
                                               fields=['physical_quantity', 'reserved_quantity', 'version_number'])
        for item in inventory_items.values():
            item.increment_version()

    def get_available_quantity_items_by_sku(self, sku_list: list[str]) -> dict[str, int]:
        inv_items = (InventoryItemModel.objects.filter(sku__in=sku_list).values('sku').annotate(
            available_quantity=Coalesce(
                Sum(F('physical_quantity') - F('reserved_quantity')), Value(0))
            )
        )
        return {item['sku']: item['available_quantity'] for item in inv_items}


class DjangoAllocationRepository(AbstractAllocationRepository):

    @classmethod
    def _save_reserved_inventory_items(
            cls,
            allocation_orm: AllocationModel,
            reserved_inventory_items: tuple[ReservedInventoryItem, ...]) -> None:
        res_items_orm = {
            (item_orm.sku, item_orm.warehouse_id): item_orm
            for item_orm in ReservedInventoryItemModel.objects.filter(allocation=allocation_orm)
        }
        for res_item in reserved_inventory_items:
            res_items_orm[res_item.key].status = status_to_db(res_item.status)

        ReservedInventoryItemModel.objects.bulk_update(res_items_orm.values(), fields=['status'])

    def create_allocation(self, allocation: Allocation) -> None:
        try:
            allocation_orm = AllocationModel.objects.create(order_id=allocation.order_id)
        except IntegrityError:
            raise AllocationAlreadyExist(allocation.order_id)

        res_items_orm = []
        for item in allocation.reserved_inv_items:
            res_item = ReservedInventoryItemModel(
                allocation=allocation_orm,
                sku=item.sku,
                warehouse_id=item.warehouse_id,
                quantity=item.quantity,
                status=status_to_db(item.status)
            )
            res_items_orm.append(res_item)
        ReservedInventoryItemModel.objects.bulk_create(res_items_orm)

        self._add_aggregate_to_seen(allocation)

    def get_allocation_by_order_id(self, order_id: str) -> Allocation:
        allocation_orm = get_object_or_raise_except(AllocationModel, order_id=order_id)
        res_inv_items_orm = ReservedInventoryItemModel.objects.filter(allocation=allocation_orm)
        return allocation_to_domain(allocation_orm, res_inv_items_orm)

    def save_allocation(self, allocation: Allocation) -> None:
        try:
            allocation_orm = get_object_or_raise_except(AllocationModel, order_id=allocation.order_id)
        except DomainDoesNotExist:
            raise AllocationDoesNotExist(allocation.order_id)

        try:
            apply_optimistic_lock(AllocationModel, allocation.version_number, order_id=allocation.order_id)
        except OptimisticLockError:
            raise OptimisticLockError()

        allocation_orm.refresh_from_db()

        self._save_reserved_inventory_items(allocation_orm, allocation.reserved_inv_items)

        allocation.increment_version()
        self._add_aggregate_to_seen(allocation)