from abc import ABC, abstractmethod
from business_logic.domain.models import (Person,
                                          Product,
                                          Cart,
                                          Order,
                                          InventoryItem,
                                          Allocation,
                                          BaseAggregate)


class AbstractRepository(ABC):
    pass


class AbstractAggregateRepository(AbstractRepository):

    def __init__(self):
        super().__init__()
        self.seen: set[BaseAggregate] = set()

    def _add_aggregate_to_seen(self, aggregate: BaseAggregate):
        self.seen.add(aggregate)


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


class AbstractCartRepository(AbstractAggregateRepository):
    """
    Адаптер также должен реализовать внутренний метод для сохранения товаров:
        def _save_cart_lines(cls, cart: Cart, cart_orm: CartModel) -> None:
    """
    @abstractmethod
    def create_cart(self, cart: Cart) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_cart_by_person(self, person_id: str) -> Cart:
        raise NotImplementedError

    @abstractmethod
    def save_cart(self, cart: Cart) -> None:
        raise NotImplementedError


class AbstractOrderRepository(AbstractAggregateRepository):

    @abstractmethod
    def create_order(self, order: Order) -> None:
        raise NotImplementedError

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


class AbstractAllocationRepository(AbstractAggregateRepository):
    """
    Адаптер также должен реализовать внутренний метод для сохранения товаров:
    def _save_reserved_inventory_items(
                    cls,
                    allocation_orm: AllocationModel,
                    reserved_inventory_items: tuple[ReservedInventoryItem]) -> None:
    """
    @abstractmethod
    def create_allocation(self, allocation: Allocation) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_allocation_by_order_id(self, order_id: str) -> Allocation:
        raise NotImplementedError

    @abstractmethod
    def save_allocation(self, allocation: Allocation) -> None:
        raise NotImplementedError