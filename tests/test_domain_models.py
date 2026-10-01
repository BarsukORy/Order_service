import unittest
from decimal import Decimal

from business_logic.domain.models import (Person, Product, CartLine, Cart,
                                          OrderLine, Order, InventoryItem)
from business_logic.domain.exceptions import TheOrderLinesDoesNotExist


def make_person(person_id="p-1"):
    return Person(
        person_id=person_id,
        first_name="Ivan",
        last_name="Petrov",
        email="ivan@example.com",
    )


def make_product(sku="sku-1", name="Table", price=Decimal("1500")):
    return Product(sku=sku, name=name, unit_price=price)


def make_cart(*lines):
    cart_lines = {line.product.sku: line for line in lines}
    return Cart(person=make_person(), cart_lines=cart_lines)


def make_cart_line(sku="sku-1", price=Decimal("1500"), quantity=1):
    return CartLine(product=make_product(sku=sku, price=price), quantity=quantity)


class TestInventoryItem(unittest.TestCase):

    def test_cannot_be_created_with_negative_quantity(self):
        with self.assertRaises(ValueError):
            InventoryItem(sku="sku-1", quantity=-1)

    def test_zero_quantity_is_allowed(self):
        item = InventoryItem(sku="sku-1", quantity=0)
        self.assertEqual(0, item.quantity_of_item)

    def test_has_enough_is_inclusive_on_boundary(self):
        item = InventoryItem(sku="sku-1", quantity=5)
        self.assertTrue(item.has_enough(5))
        self.assertFalse(item.has_enough(6))

    def test_increase_and_decrease_quantity_change_state(self):
        item = InventoryItem(sku="sku-1", quantity=5)
        item.increase_quantity(2)
        self.assertEqual(7, item.quantity_of_item)
        item.decrease_quantity(3)
        self.assertEqual(4, item.quantity_of_item)

    def test_increase_by_non_positive_value_is_rejected(self):
        item = InventoryItem(sku="sku-1", quantity=5)
        with self.assertRaises(ValueError):
            item.increase_quantity(0)

    def test_decrease_below_stock_is_rejected(self):
        item = InventoryItem(sku="sku-1", quantity=5)
        with self.assertRaises(ValueError):
            item.decrease_quantity(6)
        self.assertEqual(5, item.quantity_of_item)


class TestProduct(unittest.TestCase):

    def test_cannot_be_created_with_non_positive_price(self):
        with self.assertRaises(ValueError):
            make_product(price=Decimal("0"))

    def test_price_change_returns_new_object_and_keeps_old_one(self):
        product = make_product(price=Decimal("1500"))
        changed = product.increase_price(Decimal("500"))
        self.assertEqual(Decimal("2000"), changed.unit_price)
        self.assertEqual(Decimal("1500"), product.unit_price)

    def test_discount_below_zero_is_rejected(self):
        product = make_product(price=Decimal("1500"))
        with self.assertRaises(ValueError):
            product.decrease_price(Decimal("1500"))

    def test_negative_delta_is_rejected(self):
        product = make_product(price=Decimal("1500"))
        with self.assertRaises(ValueError):
            product.increase_price(Decimal("-100"))


class TestCartLine(unittest.TestCase):

    def test_cannot_be_created_with_zero_quantity(self):
        with self.assertRaises(ValueError):
            CartLine(product=make_product(), quantity=0)

    def test_line_price_is_price_times_quantity(self):
        line = make_cart_line(price=Decimal("1500"), quantity=3)
        self.assertEqual(Decimal("4500"), line.cart_line_price)

    def test_quantity_change_returns_new_object(self):
        line = make_cart_line(quantity=3)
        increased = line.increase_quantity(2)
        self.assertEqual(5, increased.quantity)
        self.assertEqual(3, line.quantity)

    def test_decrease_to_zero_is_rejected(self):
        line = make_cart_line(quantity=3)
        with self.assertRaises(ValueError):
            line.decrease_quantity(3)


class TestCart(unittest.TestCase):

    def test_empty_cart_price_is_zero(self):
        self.assertEqual(Decimal("0"), make_cart().price_of_cart)

    def test_price_sums_all_lines(self):
        cart = make_cart(
            make_cart_line(sku="a", price=Decimal("100"), quantity=2),
            make_cart_line(sku="b", price=Decimal("50"), quantity=3),
        )
        self.assertEqual(Decimal("350"), cart.price_of_cart)

    def test_quantity_of_absent_product_is_zero(self):
        self.assertEqual(0, make_cart().get_quantity_of_product("missing"))

    def test_add_new_product_creates_line(self):
        cart = make_cart()
        cart.add_product(make_product(sku="a"), 2)
        self.assertEqual(2, cart.get_quantity_of_product("a"))

    def test_add_same_product_twice_merges_quantities(self):
        cart = make_cart()
        cart.add_product(make_product(sku="a"), 2)
        cart.add_product(make_product(sku="a"), 3)
        self.assertEqual(5, cart.get_quantity_of_product("a"))
        self.assertEqual(["a"], list(cart.all_sku))

    def test_add_merges_over_existing_line_from_storage(self):
        cart = make_cart(make_cart_line(sku="a", quantity=2))
        cart.add_product(make_product(sku="a"), 1)
        self.assertEqual(3, cart.get_quantity_of_product("a"))

    def test_remove_partial_quantity_keeps_line(self):
        cart = make_cart(make_cart_line(sku="a", quantity=5))
        cart.remove_product(make_product(sku="a"), 2)
        self.assertEqual(3, cart.get_quantity_of_product("a"))

    def test_remove_full_quantity_deletes_line(self):
        cart = make_cart(make_cart_line(sku="a", quantity=5))
        cart.remove_product(make_product(sku="a"), 5)
        self.assertEqual([], list(cart.all_sku))

    def test_removing_absent_product_does_nothing(self):
        cart = make_cart(make_cart_line(sku="a", quantity=5))
        cart.remove_product(make_product(sku="zzz"), 1)
        self.assertEqual(["a"], list(cart.all_sku))

    def test_clear_product_removes_line_whole(self):
        cart = make_cart(make_cart_line(sku="a", quantity=5))
        cart.clear_product(make_product(sku="a"))
        self.assertEqual([], list(cart.all_sku))

    def test_clear_cart_removes_everything(self):
        cart = make_cart(
            make_cart_line(sku="a", quantity=1),
            make_cart_line(sku="b", quantity=1),
        )
        cart.clear_cart()
        self.assertEqual(Decimal("0"), cart.price_of_cart)


class TestOrder(unittest.TestCase):

    @staticmethod
    def make_order_lines():
        return {
            "a": OrderLine(product_sku="a", product_name="Table",
                           quantity=2, line_price=Decimal("3000")),
            "b": OrderLine(product_sku="b", product_name="Chair",
                           quantity=1, line_price=Decimal("500")),
        }

    def test_final_price_sums_order_lines(self):
        order = Order(order_id="o-1", person=make_person(),
                      order_lines=self.make_order_lines())
        self.assertEqual(Decimal("3500"), order.final_price)

    def test_order_without_lines_cannot_be_created(self):
        with self.assertRaises(TheOrderLinesDoesNotExist):
            Order(order_id="o-1", person=make_person(), order_lines=dict())

    def test_order_keeps_identifiers(self):
        order = Order(order_id="o-1", person=make_person(person_id="p-42"),
                      order_lines=self.make_order_lines())
        self.assertEqual("o-1", order.order_id)
        self.assertEqual("p-42", order.person_id)

    def test_order_line_is_price_snapshot_not_reference(self):
        line = OrderLine(product_sku="a", product_name="Table",
                         quantity=2, line_price=Decimal("3000"))
        self.assertEqual(Decimal("3000"), line.line_price)
        self.assertFalse(hasattr(line, "product"))


if __name__ == "__main__":
    unittest.main()
