from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Iterable

from business_logic.domain.exceptions import (TheOrderLinesDoesNotExist,
                                              ProductDoesNotExistInCart,
                                              InvalidQuantityForTheOperation)


@dataclass(frozen=True)
class Person:
    person_id: str
    first_name: str
    last_name: str
    email: str


class InventoryItem:

    def __init__(self, sku: str, quantity: int) -> None:
        self.sku = sku
        if quantity < 0:
            raise ValueError("The quantity value must be greater or equal zero.")
        else:
            self._quantity = quantity

    @property
    def quantity_of_item(self) -> int:
        return self._quantity

    def has_enough(self, quantity) -> bool:
        return self._quantity >= quantity

    def increase_quantity(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        self._quantity += quantity

    def decrease_quantity(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        if not self.has_enough(quantity):
            raise ValueError("There is a shortage of stock in the warehouse.")
        self._quantity -= quantity


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.unit_price <= 0:
            raise ValueError("Unit price must be greater than zero")

    def increase_price(self, price: Decimal) -> "Product":
        if price <= 0:
            raise ValueError("To increase the price, the value must be greater than zero.")
        return replace(self, unit_price=self.unit_price + price)

    def decrease_price(self, price: Decimal) -> "Product":
        if price <= 0:
            raise ValueError("To decrease the price, the value must be greater than zero.")
        elif self.unit_price - price <= 0:
            raise ValueError("The result unit_price value must be greater than zero.")
        return replace(self, unit_price=self.unit_price - price)


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int

    @property
    def cart_line_price(self) -> Decimal:
        return self.product.unit_price * self.quantity

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")

    def increase_quantity(self, quantity: int) -> "CartLine":
        if quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        return replace(self, quantity=self.quantity + quantity)

    def decrease_quantity(self, quantity: int) -> "CartLine":
        if quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        elif self.quantity - quantity <= 0:
            raise ValueError("The result quantity value must be greater than zero.")
        return replace(self, quantity=self.quantity - quantity)


class Cart:

    def __init__(self, person: Person, cart_lines: dict[str, CartLine]):
        self._person = person
        self._cart_lines = cart_lines

    @property
    def person_id(self) -> str:
        return self._person.person_id

    @property
    def all_sku(self) -> Iterable[str]:
        return list(self._cart_lines.keys())

    @property
    def cart_lines(self) -> Iterable[CartLine]:
        return self._cart_lines.values()

    @property
    def price_of_cart(self) -> Decimal:
        return Decimal(sum(line.cart_line_price for line in self._cart_lines.values()))

    def get_quantity_of_product(self, sku: str) -> int:
        line = self._cart_lines.get(sku)
        return line.quantity if line else 0

    def add_product(self, product: Product, quantity: int) -> None:
        if product.sku not in self._cart_lines:
            self._cart_lines[product.sku] = CartLine(product, quantity)
        else:
            self._cart_lines[product.sku] = self._cart_lines[product.sku].increase_quantity(quantity)

    def remove_product(self, product: Product, quantity: int) -> None:
        if product.sku in self._cart_lines:
            line = self._cart_lines.get(product.sku)
            if line.quantity == quantity:
                del self._cart_lines[product.sku]
            else:
                if line.quantity > quantity:
                    self._cart_lines[product.sku] = line.decrease_quantity(quantity)
                else:
                    raise InvalidQuantityForTheOperation()
        else:
            raise ProductDoesNotExistInCart()

    def clear_product(self, product: Product) -> None:
        if product.sku in self._cart_lines:
            del self._cart_lines[product.sku]
        else:
            raise ProductDoesNotExistInCart()

    def clear_cart(self) -> None:
        self._cart_lines.clear()


@dataclass(frozen=True)
class OrderLine:
    product_sku: str
    product_name: str
    quantity: int
    line_price: Decimal

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        if self.line_price <= Decimal(0):
            raise ValueError("The line_price value must be greater than zero.")


class Order:

    def __init__(
            self,
            order_id: str,
            person: Person,
            order_lines: dict[str, OrderLine]):
        self._order_id = order_id
        self._person = person
        self._order_lines = order_lines
        self._final_price: Decimal = Order.calculate_final_price(self._order_lines)

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def person_id(self) -> str:
        return self._person.person_id

    @property
    def final_price(self) -> Decimal:
        return self._final_price

    @property
    def order_lines(self) -> Iterable[OrderLine]:
        return self._order_lines.values()

    @staticmethod
    def calculate_final_price(order_lines) -> Decimal:
        if not order_lines:
            raise TheOrderLinesDoesNotExist()
        return Decimal(sum(line.line_price for line in order_lines.values()))