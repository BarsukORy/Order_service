import enum
from decimal import Decimal
from typing import Any


class DomainException(Exception):
    pass


class DomainDoesNotExist(DomainException):
    """Сущность отсутствует в базе данных."""
    def __init__(self, message: str) -> None:
        super().__init__(message)


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


class InvalidStatusTransition(DomainException):
    """Недопустимый переход статуса."""
    def __init__(self, old_status: enum.Enum, new_status: enum.Enum) -> None:
        super().__init__(f"Status transition {old_status.name} -> {new_status.name} is not allowed")
        self.old_status = old_status
        self.new_status = new_status


class CartDoesNotExist(DomainDoesNotExist):
    """Корзина отсутствует."""
    def __init__(self, person_id: str):
        super().__init__(f"Cart for this user {person_id} does not exist.")
        self.person_id = person_id


class CartAlreadyExist(DomainException):
    """Корзина для этого пользователя уже существует."""
    def __init__(self, person_id: str):
        super().__init__(f"Cart for this user {person_id} already exist.")
        self.person_id = person_id


class OptimisticLockError(DomainException):
    """Оптимистичная блокировка, т.к. агрегат уже был обновлен."""
    def __init__(self):
        super().__init__(f'Optimistic lock error.')


class OrderDoesNotExist(DomainDoesNotExist):
    """Заказа с таким id не существует."""
    def __init__(self, order_id: str):
        super().__init__(f"Order {order_id} does not exist.")
        self.order_id = order_id


class AllocationDoesNotExist(DomainDoesNotExist):
    """Размещения для такого заказа не существует."""
    def __init__(self, order_id: str):
        super().__init__(f"Allocation {order_id} does not exist.")
        self.order_id = order_id


class AllocationAlreadyExist(DomainException):
    """Размещения для такого заказа уже существует."""
    def __init__(self, order_id: str):
        super().__init__(f"Allocation {order_id} already exist.")