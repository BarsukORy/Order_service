from collections import deque
from abc import ABC, abstractmethod
from typing import Deque
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
        self.seen: Deque[BaseAggregate] = deque()

    def _add_aggregate_to_seen(self, aggregate: BaseAggregate) -> None:
        self.seen.append(aggregate)


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


class AbstractInventoryItemRepository(AbstractAggregateRepository):

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

    @abstractmethod
    def create_allocation(self, allocation: Allocation) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_allocation_by_order_id(self, order_id: str) -> Allocation:
        raise NotImplementedError

    @abstractmethod
    def save_allocation(self, allocation: Allocation) -> None:
        raise NotImplementedError