from django.db.models import Q, Sum, F, Value
from django.db.models.functions import Coalesce
from business_logic.domain.exceptions import DomainDoesNotExist, CartDoesNotExist
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
                               AllocationModel)
from django_app.adapters.mappers import (person_to_domain,
                                         product_to_domain,
                                         cart_to_domain,
                                         order_to_domain,
                                         inventory_items_to_domain,
                                         allocation_to_domain,
                                         status_to_db)


def get_object_or_raise_except(model, **filters):
    try:
        return model.objects.get(**filters)
    except model.DoesNotExist as exc:
        entities = ", ".join(f'{k}={v}' for k, v in filters.items())
        raise DomainDoesNotExist(f'{model.__name__} does not exist: {entities}') from exc


"""Раздел магазина."""


class DjangoPersonRepository(AbstractPersonRepository):

    def get_person_by_id(self, person_id) -> Person:
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

    def get_product_by_sku(self, sku) -> Product:
        product_orm = get_object_or_raise_except(ProductModel, sku=sku)
        return product_to_domain(product_orm)

    def save_product(self, product: Product) -> None:
        product_orm = get_object_or_raise_except(ProductModel, sku=product.sku)
        product_orm.sku = product.sku
        product_orm.name = product.name
        product_orm.unit_price = product.unit_price
        product_orm.save()


class DjangoCartRepository(AbstractCartRepository):

    @classmethod
    def _create_cart(cls, cart: Cart) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=cart.person_id)
        cart_orm = CartModel.objects.create(person=person_orm)

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

    def get_cart_by_person(self, person_id) -> Cart:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=person_id)
        cart_orm = CartModel.objects.filter(person=person_orm).first()

        if cart_orm is None:
            raise CartDoesNotExist(person_id)

        cart_lines_orm = CartLineModel.objects.filter(cart=cart_orm).select_related('product')

        return cart_to_domain(person_orm, cart_lines_orm)

    def save_cart(self, cart: Cart) -> None:
        self._add(cart)
        cart_orm = CartModel.objects.filter(person__domain_id=cart.person_id).first()

        if cart_orm is None:
            self._create_cart(cart)
            return

        existing_lines = {
            line_orm.product.sku: line_orm
            for line_orm in CartLineModel.objects.filter(cart=cart_orm).select_related('product')
        }

        prefer_lines = {
            line.product.sku: line for line in cart.cart_lines.values()
        }

        for sku, line_orm in existing_lines.items():
            if sku not in prefer_lines:
                line_orm.delete()

        for sku, line in prefer_lines.items():
            if sku not in existing_lines:
                product_orm = get_object_or_raise_except(ProductModel, sku=sku)
                CartLineModel.objects.create(cart=cart_orm, product=product_orm, quantity=line.quantity)
            else:
                line_orm = existing_lines[sku]
                if line_orm.quantity != line.quantity:
                    line_orm.quantity = line.quantity
                    line_orm.save()


class DjangoOrderRepository(AbstractOrderRepository):

    @classmethod
    def _create_order(cls, order: Order) -> None:
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

    def get_order_by_id(self, order_id) -> Order:
        order_orm = get_object_or_raise_except(OrderModel, domain_id=order_id)
        order_lines_orm = OrderLineModel.objects.filter(order=order_orm)
        return order_to_domain(order_orm, order_lines_orm)

    def save_order(self, order: Order) -> None:
        """При существующем заказе у него может меняться только поле статуса. """
        self._add(order)
        order_orm = OrderModel.objects.filter(domain_id=order.order_id).first()

        if order_orm is None:
            self._create_order(order)
            return

        order_orm.status = status_to_db(order.status)
        order_orm.save()


"""Раздел склада."""


class DjangoInventoryItemRepository(AbstractInventoryItemRepository):

    def get_inv_items_by_sku(self, sku_list: list[str]) -> dict[tuple[str, str], InventoryItem]:
        items_orm = InventoryItemModel.objects.filter(sku__in=sku_list)
        return inventory_items_to_domain(items_orm)

    def save_inv_items(self, inventory_items: dict[tuple[str, str], InventoryItem]) -> None:
        q = Q()
        for sku, warehouse_id in inventory_items.keys():
            q |= Q(sku=sku, warehouse_id=warehouse_id)
        items_orm = InventoryItemModel.objects.filter(q)
        for item in items_orm:
            item.physical_quantity = inventory_items[(item.sku, item.warehouse_id)].physical_quantity
            item.reserved_quantity = inventory_items[(item.sku, item.warehouse_id)].reserved_quantity
        InventoryItemModel.objects.bulk_update(items_orm, fields=['physical_quantity', 'reserved_quantity'])

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
            reserved_inventory_items: tuple[ReservedInventoryItem]) -> None:
        res_items_orm = {
            (item_orm.sku, item_orm.warehouse_id): item_orm
            for item_orm in ReservedInventoryItemModel.objects.filter(allocation=allocation_orm)
        }
        for res_item in reserved_inventory_items:
            res_items_orm[res_item.key].status = status_to_db(res_item.status)

        ReservedInventoryItemModel.objects.bulk_update(res_items_orm.values(), fields=['status'])

    @classmethod
    def _create_allocation(cls, allocation: Allocation) -> None:
        allocation_orm = AllocationModel.objects.create(order_id=allocation.order_id)
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

    def get_allocation_by_order_id(self, order_id: str) -> Allocation:
        allocation_orm = get_object_or_raise_except(AllocationModel, order_id=order_id)
        res_inv_items_orm = ReservedInventoryItemModel.objects.filter(allocation=allocation_orm)
        return allocation_to_domain(allocation_orm, res_inv_items_orm)

    def save_allocation(self, allocation: Allocation) -> None:
        self._add(allocation)
        allocation_orm = AllocationModel.objects.filter(order_id=allocation.order_id).first()

        if allocation_orm is None:
            self._create_allocation(allocation)
            return

        self._save_reserved_inventory_items(allocation_orm, allocation.reserved_inv_items)