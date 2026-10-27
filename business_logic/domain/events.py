from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str


@dataclass(frozen=True)
class OrderAllocated(Event):
    order_id: str