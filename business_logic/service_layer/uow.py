from abc import ABC, abstractmethod
from business_logic.service_layer.ports.repositories import (AbstractCartRepository,
                                                             AbstractOrderRepository,
                                                             AbstractProductRepository,
                                                             AbstractPersonRepository,
                                                             AbstractInventoryItemRepository,
                                                             AbstractAllocationRepository,
                                                             AbstractAggregateRepository)


class AbstractUnitOfWork(ABC):

    person_repo: AbstractPersonRepository
    product_repo: AbstractProductRepository
    cart_repo: AbstractCartRepository
    order_repo: AbstractOrderRepository
    inventory_item_repo: AbstractInventoryItemRepository
    allocation_repo: AbstractAllocationRepository

    def commit(self):
        self._commit()

    def collect_new_messages(self):
        for repo in vars(self).values():
            if isinstance(repo, AbstractAggregateRepository):
                for aggregate in repo.seen:
                    while aggregate.events:
                        message = aggregate.events.popleft()
                        yield message

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError