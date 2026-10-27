from typing import Callable
from business_logic.domain.commands import Command, CreateOrderCommand, CancelOrderCommand
from business_logic.domain.events import Event, OrderCreated, OrderAllocated
from business_logic.service_layer.uow import AbstractUnitOfWork
from business_logic.service_layer.use_cases import OrderService, InventoryItemService


def create_order_handler(cmd: CreateOrderCommand, uow: AbstractUnitOfWork):
    with uow:
        order = OrderService(cmd.person_id, uow).place_order()
        item = InventoryItemService(uow)
        item.reserve_item(order)
        uow.commit()


def cancel_order_handler(cmd: CancelOrderCommand, uow: AbstractUnitOfWork):
    with uow:
        order = OrderService(cmd.person_id, uow)
        order.cancel_order(cmd.order_id)
        uow.commit()


def order_created_handler(event: OrderCreated) -> None:
    print('Order created with ID: ' + event.order_id)


def order_allocated_handler(event: OrderAllocated) -> None:
    print('Order allocated with ID: ' + event.order_id)


EVENT_HANDLERS: dict[type[Event], list[Callable]] = {
    OrderCreated: [order_created_handler],
    OrderAllocated: [order_allocated_handler]
}


COMMAND_HANDLERS: dict[type[Command], Callable] = {
    CreateOrderCommand: create_order_handler,
    CancelOrderCommand: cancel_order_handler,
}