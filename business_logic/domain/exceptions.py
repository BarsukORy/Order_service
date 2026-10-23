from decimal import Decimal
from typing import Any


class DomainException(Exception):
    pass


class DomainDoesNotExist(DomainException):
    """Сущность отсутствует в базе данных."""
    def __init__(self, domain) -> None:
        super().__init__(f"Domain '{domain.__class__.__name__}' does not exist.")


class ProductDoesNotExistInCart(DomainException):
    """Товар отсутствует в корзине."""
    def __init__(self, product, cart) -> None:
        super().__init__(f"Product '{product}' does not exist in cart '{cart}'")
        self.product = product
        self.cart = cart


class InvalidValueForTheOperation(DomainException):
    """Некорректное значение для совершения операции."""
    def __init__(self, obj: Any, value: int | Decimal) -> None:
        super().__init__(f"Value {value} is invalid for the operation on {type(obj).__name__}")
        self.obj = obj
        self.value = value


class InsufficientStockInTheWarehouse(DomainException):
    """Недостаточное количество товара на складе."""
    def __init__(self, sku: str) -> None:
        super().__init__(f"Not enough stock in the warehouse for sku={sku}")
        self.sku = sku


class TheOrderLinesDoesNotExist(DomainException):
    """Нельзя оформить заказ, т.к. товарные позиции заказа отсутствуют."""
    def __init__(self) -> None:
        super().__init__("The Order Line does not exist.")


class ItemsCannotBeOrdered(DomainException):
    """Некоторые товары нельзя заказать в данный момент."""
    def __init__(self, sku: str) -> None:
        super().__init__(f"Not enough stock in the warehouse for sku={sku}")
        self.sku = sku


class InvalidStatusTransition(DomainException):
    """Недопустимый переход статуса."""
    def __init__(self, old_status: ..., new_status: ...) -> None:
        super().__init__(f"Status transition {old_status.name} -> {new_status.name} is not allowed")
        self.old_status = old_status
        self.new_status = new_status


class CartDoesNotExist(DomainException):
    """Корзина отсутствует."""
    def __init__(self, person_id: str):
        super().__init__(f"Cart for this user {person_id} does not exist.")
        self.person_id = person_id