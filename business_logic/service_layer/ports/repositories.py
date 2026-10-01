from abc import ABC, abstractmethod
from typing import Iterable
from business_logic.domain.models import Person, Product, Cart, Order, InventoryItem


class AbstractRepository(ABC):
    pass


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

    @abstractmethod
    def create_cart(self, cart: Cart) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_cart_by_person(self, person_id: str) -> Cart:
        raise NotImplementedError

    @abstractmethod
    def save_cart(self, cart: Cart) -> None:
        raise NotImplementedError


class AbstractOrderRepository(AbstractRepository):

    @abstractmethod
    def create_order(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_order_by_id(self, order_id: str) -> Order:
        raise NotImplementedError


class AbstractInventoryItemRepository(AbstractRepository):

    @abstractmethod
    def get_item_by_sku(self, sku: str) -> InventoryItem:
        raise NotImplementedError

    @abstractmethod
    def get_items_by_sku(self, sku_list: Iterable[str]) -> dict[str, InventoryItem]:
        raise NotImplementedError

    @abstractmethod
    def save_item(self, inventory_item: InventoryItem) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_items(self, inventory_items: dict[str, InventoryItem]) -> None:
        raise NotImplementedError