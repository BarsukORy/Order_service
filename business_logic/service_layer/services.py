from business_logic.domain.models import OrderLine, Order, CartLine, InventoryItem, Cart
from business_logic.domain.services import AbstractIdGenerator
from business_logic.domain.exceptions import InsufficientStockInTheWarehouse, ItemsCannotBeOrdered
from business_logic.service_layer.ports.repositories import (AbstractPersonRepository,
                                                             AbstractOrderRepository,
                                                             AbstractCartRepository,
                                                             AbstractProductRepository,
                                                             AbstractInventoryItemRepository)


def add_product_to_cart(
        product_sku: str,
        quantity_product: int,
        person_id: str,
        product_repo: AbstractProductRepository,
        cart_repo: AbstractCartRepository,
        inventory_item_repo: AbstractInventoryItemRepository):

    cart = cart_repo.get_cart_by_person(person_id)
    product = product_repo.get_product_by_sku(product_sku)
    inventory_item = inventory_item_repo.get_item_by_sku(product_sku)

    total_quan = cart.get_quantity_of_product(product_sku) + quantity_product

    if inventory_item.has_enough(total_quan):
        cart.add_product(product, quantity_product)
    else:
        raise InsufficientStockInTheWarehouse()

    cart_repo.save_cart(cart)


class PlaceOrder:

    def __init__(
            self,
            person_id: str,
            person_repo: AbstractPersonRepository,
            cart_repo: AbstractCartRepository,
            order_repo: AbstractOrderRepository,
            inventory_item_repo: AbstractInventoryItemRepository,
            id_generator: AbstractIdGenerator):

        self.person_id = person_id
        self.person_repo = person_repo
        self.cart_repo = cart_repo
        self.order_repo = order_repo
        self.inventory_item_repo = inventory_item_repo
        self.id_generator = id_generator

        self._order_lines: dict[str, OrderLine] = dict()
        self._inventory_items_for_change: dict[str, tuple[InventoryItem, int]] = dict()
        self._not_available_for_order: dict[str, CartLine] = dict()

    @property
    def person(self):
        return self.person_repo.get_person_by_id(self.person_id)

    def generate_order_lines(self, cart: Cart):

        list_inventory_items = self.inventory_item_repo.get_items_by_sku(cart.all_sku)

        for cart_line in cart.cart_lines:

            if list_inventory_items[cart_line.product.sku].has_enough(cart_line.quantity):

                order_line = OrderLine(
                    product_sku=cart_line.product.sku,
                    product_name=cart_line.product.name,
                    quantity=cart_line.quantity,
                    line_price=cart_line.cart_line_price
                )
                self._order_lines[cart_line.product.sku] = order_line

                self._inventory_items_for_change[cart_line.product.sku] = (list_inventory_items[cart_line.product.sku],
                                                                           cart_line.quantity)

            else:

                self._not_available_for_order[cart_line.product.sku] = cart_line

        return self._not_available_for_order.values()

    def _change_quantity_items(self) -> dict[str, InventoryItem]:
        inventory_items = dict()
        for sku, (item, quan) in self._inventory_items_for_change.items():
            item.decrease_quantity(quan)
            inventory_items[sku] = item
        return inventory_items

    def place_order(self):

        cart = self.cart_repo.get_cart_by_person(self.person_id)

        if self.generate_order_lines(cart):
            raise ItemsCannotBeOrdered(f'Some items cannot be ordered at the moment.',
                                       self._not_available_for_order)

        order = Order(
            order_id=self.id_generator.generate_id(),
            person=self.person,
            order_lines=self._order_lines)

        self.order_repo.create_order(order)

        self.inventory_item_repo.save_items(self._change_quantity_items())

        cart.clear_cart()

        self.cart_repo.save_cart(cart)