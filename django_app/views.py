from business_logic.domain.commands import CreateOrderCommand, CancelOrderCommand
from business_logic.service_layer.message_bus import MessageBus
from business_logic.handlers.handlers import EVENT_HANDLERS, COMMAND_HANDLERS
from django_app.django_uow import DjangoUnitOfWork


def place_order_command(person_id):
    message_bus = MessageBus(
        DjangoUnitOfWork,
        EVENT_HANDLERS,
        COMMAND_HANDLERS
    )
    message_bus.handle(CreateOrderCommand(person_id))


def cancel_order_command(person_id, order_id):
    message_bus = MessageBus(
        DjangoUnitOfWork,
        EVENT_HANDLERS,
        COMMAND_HANDLERS
    )
    message_bus.handle(CancelOrderCommand(person_id, order_id))