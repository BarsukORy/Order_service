from business_logic.service_layer.uow import AbstractUnitOfWork
from django_app.adapters.repositories import (DjangoCartRepository,
                                              DjangoOrderRepository,
                                              DjangoProductRepository,
                                              DjangoPersonRepository,
                                              DjangoInventoryItemRepository,
                                              DjangoAllocationRepository)
from django.db import transaction


class DjangoUnitOfWork(AbstractUnitOfWork):

    def __init__(self):
        self.person_repo = DjangoPersonRepository()
        self.product_repo = DjangoProductRepository()
        self.cart_repo = DjangoCartRepository()
        self.order_repo = DjangoOrderRepository()
        self.inventory_item_repo = DjangoInventoryItemRepository()
        self.allocation_repo = DjangoAllocationRepository()

        self.atomic = None
        self._finished = False

    def _commit(self):
        if self._finished:
            raise RuntimeError('UnitOfWork already finished')
        self._finished = True
        self.atomic.__exit__(None, None, None)

    def __enter__(self):
        self.atomic = transaction.atomic()
        self.atomic.__enter__()
        self._finished = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._finished:
            self.atomic.__exit__(exc_type, exc_val, exc_tb)