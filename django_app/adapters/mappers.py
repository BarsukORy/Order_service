from typing import Iterable, Union
from business_logic.domain.models import (Person,
                                          Product,
                                          CartLine,
                                          Cart,
                                          OrderLine,
                                          Order,
                                          InventoryItem,
                                          ReservedInventoryItem,
                                          Allocation)
from django_app.models import (PersonModel,
                               ProductModel,
                               CartLineModel,
                               OrderLineModel,
                               OrderModel,
                               InventoryItemModel,
                               ReservedInventoryItemModel,
                               AllocationModel,
                               CartModel)


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


def cart_to_domain(
        person_orm: PersonModel,
        cart_orm: CartModel,
        cart_lines_orm: Iterable[CartLineModel] = None) -> Cart:

    if cart_lines_orm is None:
        cart_lines_dm = dict()
    else:
        cart_lines_dm = {
            cart_line.product.sku: cart_line
            for cart_line in (cart_line_to_domain(orm_line) for orm_line in cart_lines_orm)
        }
    return Cart.restore(
        person=person_to_domain(person_orm),
        cart_lines=cart_lines_dm,
        version_number=cart_orm.version_number
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
    return Order.restore(
        order_id=order_orm.domain_id,
        person=person_to_domain(order_orm.person),
        order_lines=order_lines_dm,
        final_price=order_orm.final_price,
        status=Order.OrderStatus[order_orm.status],
        version_number=order_orm.version_number
    )


"""Раздел склада."""


def inventory_item_to_domain(inventory_item_orm: InventoryItemModel) -> InventoryItem:
    return InventoryItem.restore(
        sku=inventory_item_orm.sku,
        warehouse_id=inventory_item_orm.warehouse_id,
        physical_quantity=inventory_item_orm.physical_quantity,
        reserved_quantity=inventory_item_orm.reserved_quantity,
        version_number=inventory_item_orm.version_number
    )


def inventory_items_to_domain(inventory_items_orm: Iterable[InventoryItemModel]) -> dict[tuple[str, str], InventoryItem]:
    items = {
        item.key: item
        for item in (inventory_item_to_domain(item_orm) for item_orm in inventory_items_orm)
    }
    return items


def reserved_inventory_item_to_domain(res_inventory_item_orm: ReservedInventoryItemModel) -> ReservedInventoryItem:
    return ReservedInventoryItem.restore(
        sku=res_inventory_item_orm.sku,
        warehouse_id=res_inventory_item_orm.warehouse_id,
        quantity=res_inventory_item_orm.quantity,
        status=ReservedInventoryItem.ReservedInventoryItemStatus[res_inventory_item_orm.status]
    )


def allocation_to_domain(
        allocation_orm: AllocationModel,
        res_inv_items_orm: Iterable[ReservedInventoryItemModel]) -> Allocation:
    reserved_inventory_items = [reserved_inventory_item_to_domain(inv_item) for inv_item in res_inv_items_orm]
    return Allocation.restore(
        order_id=allocation_orm.order_id,
        reserved_inv_items=reserved_inventory_items,
        version_number=allocation_orm.version_number
    )


def status_to_db(status: Union[Order.OrderStatus, ReservedInventoryItem.ReservedInventoryItemStatus]) -> str:
    return status.name