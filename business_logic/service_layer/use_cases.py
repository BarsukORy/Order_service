from business_logic.domain.events import OrderCreated, OrderAllocated
from business_logic.domain.models import (OrderLine,
                                          Order,
                                          InventoryItem,
                                          Cart,
                                          Allocation)
from business_logic.domain.exceptions import (TheOrderLinesDoesNotExist,
                                              CartDoesNotExist)
from business_logic.service_layer.uow import AbstractUnitOfWork


class InventoryItemService:

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def has_enough_items(self, required_items: dict[str, int]) -> bool:
        inv_items = self.uow.inventory_item_repo.get_available_quantity_items_by_sku(list(required_items.keys()))
        for sku, quan in required_items.items():
            item_quan = inv_items.get(sku, 0)
            if quan > item_quan or item_quan == 0:
                return False
        return True

    def get_items(self, required_items: list[str]) -> dict[tuple[str, str], InventoryItem]:
        return self.uow.inventory_item_repo.get_inv_items_by_sku(required_items)

    def get_items_for_update(self, required_items: list[str]) -> dict[tuple[str, str], InventoryItem]:
        return self.uow.inventory_item_repo.get_inv_items_by_sku(required_items)

    def reserve_item(self, items_for_reserve: dict[tuple[str, str], int]) -> None:
        inv_items = self.get_items([keys[0] for keys in items_for_reserve.keys()])
        for (sku, wh_id), quan in items_for_reserve.items():
            inv_items[(sku, wh_id)].reserve(quan)
        self.uow.inventory_item_repo.save_inv_items(inv_items)


class AllocationService:

    def __init__(self, uow: AbstractUnitOfWork, inventory_item_service: InventoryItemService):
        self.uow = uow
        self.inventory_item_service = inventory_item_service

    def place_allocation(self, order: Order):
        inventory_items = self.inventory_item_service.get_items_for_update(order.all_sku)
        inventory_items = {(sku, wh_id): item.available_quantity for (sku, wh_id), item in inventory_items.items()}

        allocation = Allocation.create(order.order_id, order.quantity_for_sku, inventory_items)
        allocation.events.append(OrderAllocated(allocation.order_id))
        self.uow.allocation_repo.create_allocation(allocation)

        self.inventory_item_service.reserve_item(allocation.reserved_quantity_for_key)


class CartService:

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def _create_cart(self, person_id: str) -> Cart:
        person = self.uow.person_repo.get_person_by_id(person_id)
        cart = Cart.create(person=person)
        self.uow.cart_repo.create_cart(cart)
        return cart

    def get_or_create_cart(self, person_id: str) -> Cart:
        try:
            cart = self.uow.cart_repo.get_cart_by_person(person_id)
        except CartDoesNotExist:
            cart = self._create_cart(person_id)
        return cart


class OrderService:

    def __init__(
            self,
            person_id: str,
            uow: AbstractUnitOfWork):

        self.person_id = person_id
        self.uow = uow

    @classmethod
    def _generate_order_lines(cls, cart: Cart):
        order_lines: dict[str, OrderLine] = dict()

        for sku, cart_line in cart.cart_lines.items():

            order_line = OrderLine(
                product_sku=cart_line.product.sku,
                product_name=cart_line.product.name,
                quantity=cart_line.quantity,
                line_price=cart_line.cart_line_price
            )
            order_lines[sku] = order_line

        return order_lines

    def place_order(self) -> Order:
        try:
            cart = self.uow.cart_repo.get_cart_by_person(self.person_id)
        except CartDoesNotExist:
            raise

        order_lines = self._generate_order_lines(cart)

        try:
            order = Order.create(
                person=cart.person,
                order_lines=order_lines
            )
        except TheOrderLinesDoesNotExist:
            raise

        order.events.append(OrderCreated(order.order_id))
        self.uow.order_repo.create_order(order)
        cart.clear_cart()
        self.uow.cart_repo.save_cart(cart)

        return order

    def cancel_order(self, order_id: str):
        order = self.uow.order_repo.get_order_by_id(order_id)
        order.cancel_order()
        self.uow.order_repo.save_order(order)