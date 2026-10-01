class DomainException(Exception):
    pass


class DomainDoesNotExist(DomainException):
    """Сущность отсутствует в базе данных."""
    pass


class ProductDoesNotExistInCart(DomainException):
    """Товар отсутствует в корзине."""
    pass


class InvalidQuantityForTheOperation(DomainException):
    """Некорректное количество для совершения операции."""
    pass


class InsufficientStockInTheWarehouse(DomainException):
    """Недостаточное количество товара на складе."""
    pass


class TheOrderLinesDoesNotExist(DomainException):
    """Нельзя оформить заказ, т.к. товарные позиции заказа отсутствуют."""
    pass


class ItemsCannotBeOrdered(DomainException):
    """Некоторые товары нельзя заказать в данный момент."""
    pass