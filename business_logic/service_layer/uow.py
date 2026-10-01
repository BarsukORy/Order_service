from abc import ABC, abstractmethod
from business_logic.service_layer.ports.repositories import (AbstractCartRepository,
                                                             AbstractOrderRepository,
                                                             AbstractProductRepository,
                                                             AbstractPersonRepository,
                                                             AbstractInventoryItemRepository)


class AbstractUnitOfWork(ABC):

    person_repo: AbstractPersonRepository
    product_repo: AbstractProductRepository
    cart_repo: AbstractCartRepository
    order_repo: AbstractOrderRepository
    inventory_item_repo: AbstractInventoryItemRepository

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError