from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    pass


@dataclass(frozen=True)
class CreateOrderCommand(Command):
    person_id: str


@dataclass(frozen=True)
class CancelOrderCommand(Command):
    person_id: str
    order_id: str