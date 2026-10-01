from typing import Iterable
from business_logic.domain.models import Person, Order, Cart, Product, InventoryItem
from business_logic.domain.exceptions import DomainDoesNotExist
from django_app.models import (PersonModel,
                               ProductModel,
                               CartLineModel,
                               CartModel,
                               OrderLineModel,
                               OrderModel,
                               InventoryItemModel)
from django_app.adapters.mappers import (person_to_domain,
                                         product_to_domain,
                                         cart_to_domain,
                                         order_to_domain,
                                         inventory_item_to_domain,
                                         inventory_items_to_domain)
from business_logic.service_layer.ports.repositories import (AbstractPersonRepository,
                                                             AbstractOrderRepository,
                                                             AbstractCartRepository,
                                                             AbstractProductRepository,
                                                             AbstractInventoryItemRepository)


def get_object_or_raise_except(model, **filters):
    try:
        return model.objects.get(**filters)
    except model.DoesNotExist as exc:
        entities = ", ".join(f'{k}={v}' for k, v in filters.items())
        raise DomainDoesNotExist(f'{model.__name__} does not exist: {entities}') from exc


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

    def create_cart(self, cart: Cart) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=cart.person_id)
        cart_orm = CartModel.objects.create(person=person_orm)

        for cart_line in cart.cart_lines:
            product_orm = get_object_or_raise_except(ProductModel, sku=cart_line.product.sku)
            CartLineModel.objects.create(
                cart=cart_orm,
                product=product_orm,
                quantity=cart_line.quantity)

    def get_cart_by_person(self, person_id) -> Cart:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=person_id)
        cart_orm = CartModel.objects.filter(person=person_orm).first()

        if cart_orm is None:
            return Cart(person=person_to_domain(person_orm), cart_lines=dict())

        cart_lines_orm = CartLineModel.objects.filter(cart=cart_orm).select_related('product')

        return cart_to_domain(person_orm, cart_lines_orm)

    def save_cart(self, cart: Cart) -> None:
        cart_orm = CartModel.objects.filter(person__domain_id=cart.person_id).first()

        if cart_orm is None:
            self.create_cart(cart)
            return

        existing_lines = {
            line_orm.product.sku: line_orm
            for line_orm in CartLineModel.objects.filter(cart=cart_orm).select_related('product')
        }

        prefer_lines = {
            line.product.sku: line for line in cart.cart_lines
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

    def get_order_by_id(self, order_id) -> Order:
        order_orm = get_object_or_raise_except(OrderModel, domain_id=order_id)
        order_lines_orm = OrderLineModel.objects.filter(order=order_orm)
        return order_to_domain(order_orm, order_lines_orm)

    def create_order(self, order: Order) -> None:
        person_orm = get_object_or_raise_except(PersonModel, domain_id=order.person_id)

        order_orm = OrderModel.objects.create(
            domain_id=order.order_id,
            person=person_orm,
            final_price=order.final_price)

        for order_line in order.order_lines:
            OrderLineModel.objects.create(
                order=order_orm,
                product_sku=order_line.product_sku,
                product_name=order_line.product_name,
                quantity=order_line.quantity,
                line_price=order_line.line_price)


class DjangoInventoryItemRepository(AbstractInventoryItemRepository):

    def get_item_by_sku(self, sku: str) -> InventoryItem:
        item_orm = get_object_or_raise_except(InventoryItemModel, sku=sku)
        return inventory_item_to_domain(item_orm)

    def get_items_by_sku(self, sku_list: Iterable[str]) -> dict[str, InventoryItem]:
        items_orm = InventoryItemModel.objects.filter(sku__in=sku_list)
        return inventory_items_to_domain(items_orm)

    def save_item(self, inventory_item: InventoryItem) -> None:
        item_orm = get_object_or_raise_except(InventoryItemModel, sku=inventory_item.sku)
        item_orm.sku = inventory_item.sku
        item_orm.quantity = inventory_item.quantity_of_item
        item_orm.save()

    def save_items(self, inventory_items: dict[str, InventoryItem]) -> None:
        items_orm = InventoryItemModel.objects.filter(sku__in=inventory_items.keys())
        for item in items_orm:
            item.quantity = inventory_items[item.sku].quantity_of_item
        InventoryItemModel.objects.bulk_update(items_orm, fields=['quantity'])