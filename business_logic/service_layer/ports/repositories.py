from abc import ABC, abstractmethod
from business_logic.domain.models import (Person,
                                          Product,
                                          Cart,
                                          Order,
                                          InventoryItem,
                                          Allocation)


class AbstractRepository(ABC):
    pass


"""Раздел магазина."""


class AbstractPersonRepository(AbstractRepository):

    @abstractmethod
    def get_person_by_id(self, person_id: str) -> Person:
        raise NotImplementedError

    @abstractmethod
    def save_person(self, person: Person) -> None:
        raise NotImplementedError


class AbstractProductRepository(AbstractRepository):

    @abstractmethod
    def get_product_by_sku(self, sku: str) -> Product:
        raise NotImplementedError

    @abstractmethod
    def save_product(self, product: Product) -> None:
        raise NotImplementedError


class AbstractCartRepository(AbstractRepository):
    """
    Адаптер также должен реализовать внутренний метод создания корзины:
    def _create_cart(cls, cart: Cart) -> None
    """

    @abstractmethod
    def get_cart_by_person(self, person_id: str) -> Cart:
        raise NotImplementedError

    @abstractmethod
    def save_cart(self, cart: Cart) -> None:
        raise NotImplementedError


class AbstractOrderRepository(AbstractRepository):
    """
    Адаптер также должен реализовать внутренний метод создания заказа:
    def _create_order(cls, order: Order) -> None
    """

    @abstractmethod
    def save_order(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_order_by_id(self, order_id: str) -> Order:
        raise NotImplementedError


"""Раздел Склада."""


class AbstractInventoryItemRepository(AbstractRepository):

    @abstractmethod
    def get_inv_items_by_sku(self, sku_list: list[str]) -> dict[tuple[str, str], InventoryItem]:
        raise NotImplementedError

    @abstractmethod
    def save_inv_items(self, inventory_items: dict[tuple[str, str], InventoryItem]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_available_quantity_items_by_sku(self, sku_list: list[str]) -> dict[str, int]:
        raise NotImplementedError


class AbstractAllocationRepository(AbstractRepository):
    """
    Адаптер также должен реализовать внутренний метод для сохранения товаров:
    def _save_reserved_inventory_items(
                    cls,
                    allocation_orm: AllocationModel,
                    reserved_inventory_items: tuple[ReservedInventoryItem]) -> None:
    def _create_allocation(cls, allocation: Allocation) -> None:
    """

    @abstractmethod
    def get_allocation_by_order_id(self, order_id: str) -> Allocation:
        raise NotImplementedError

    @abstractmethod
    def save_allocation(self, allocation: Allocation) -> None:
        raise NotImplementedError