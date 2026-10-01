from typing import Iterable
from business_logic.domain.models import Person, Product, CartLine, Cart, OrderLine, Order, InventoryItem
from django_app.models import PersonModel, ProductModel, CartLineModel, OrderLineModel, OrderModel, InventoryItemModel


def person_to_domain(person_orm: PersonModel) -> Person:
    return Person(
        person_id=person_orm.domain_id,
        first_name=person_orm.first_name,
        last_name=person_orm.last_name,
        email=person_orm.email
    )


def product_to_domain(product_orm: ProductModel) -> Product:
    return Product(
        sku=product_orm.sku,
        name=product_orm.name,
        unit_price=product_orm.unit_price
    )


def cart_line_to_domain(cart_line_orm: CartLineModel) -> CartLine:
    return CartLine(
        product=product_to_domain(cart_line_orm.product),
        quantity=cart_line_orm.quantity
    )


def cart_to_domain(person_orm: PersonModel, cart_lines_orm: Iterable[CartLineModel]) -> Cart:
    cart_line_dm = {
        cart_line.product.sku: cart_line
        for cart_line in (cart_line_to_domain(orm_line) for orm_line in cart_lines_orm)
    }
    return Cart(
        person=person_to_domain(person_orm),
        cart_lines=cart_line_dm
    )


def order_line_to_domain(order_line_orm: OrderLineModel) -> OrderLine:
    return OrderLine(
        product_sku=order_line_orm.product_sku,
        product_name=order_line_orm.product_name,
        quantity=order_line_orm.quantity,
        line_price=order_line_orm.line_price
    )


def order_to_domain(order_orm: OrderModel, order_lines_orm: Iterable[OrderLineModel]) -> Order:
    order_lines_dm = {
        order_line.product_sku: order_line
        for order_line in (order_line_to_domain(orm_line) for orm_line in order_lines_orm)
    }
    return Order(
        order_id=order_orm.domain_id,
        person=person_to_domain(order_orm.person),
        order_lines=order_lines_dm
    )


def inventory_item_to_domain(inventory_item_orm: InventoryItemModel) -> InventoryItem:
    return InventoryItem(
        sku=inventory_item_orm.sku,
        quantity=inventory_item_orm.quantity
    )


def inventory_items_to_domain(inventory_items_orm: Iterable[InventoryItemModel]) -> dict[str, InventoryItem]:
    items = {
        item.sku: item
        for item in (inventory_item_to_domain(item_orm) for item_orm in inventory_items_orm)
    }
    return items