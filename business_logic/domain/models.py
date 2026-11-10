import enum
import uuid
from collections import deque
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Deque, Any
from types import MappingProxyType
from business_logic.domain.events import Event
from business_logic.domain.exceptions import (TheOrderLinesDoesNotExist,
                                              ProductDoesNotExistInCart,
                                              InvalidValueForTheOperation,
                                              InvalidStatusTransition,
                                              InsufficientStockInTheWarehouse)


class BaseAggregate:

    def __init__(self, version_number: int) -> None:
        self.events: Deque[Event] = deque()
        self._version_number = version_number

    @property
    def version_number(self) -> int:
        return self._version_number

    def increment_version(self) -> None:
        self._version_number += 1


def check_positive(obj: Any, value: int | Decimal) -> None:
    if value <= 0:
        raise InvalidValueForTheOperation(obj, value)


def transition_to_new_status(
        old_status: enum.Enum,
        new_status: enum.Enum,
        status_lifecycle: dict[enum.Enum, tuple[enum.Enum, ...]]) -> None:
    if new_status not in status_lifecycle[old_status]:
        raise InvalidStatusTransition(old_status, new_status)


"""
Раздел склада
"""


class InventoryItem(BaseAggregate):

    def __init__(
            self,
            sku: str,
            warehouse_id: str,
            physical_quantity: int,
            reserved_quantity: int,
            version_number: int) -> None:
        """Объекты создаются и получаются через cls-методы: create, restore."""
        super().__init__(version_number)

        if physical_quantity < 0:
            raise ValueError("The physical quantity value must be greater or equal zero.")
        if reserved_quantity < 0:
            raise ValueError("The reserved quantity value must be greater or equal zero.")
        if reserved_quantity > physical_quantity:
            raise ValueError("The reserved quantity value must be less than the physical quantity.")

        self._sku = sku
        self._warehouse_id = warehouse_id
        self._physical_quantity = physical_quantity
        self._reserved_quantity = reserved_quantity

    @classmethod
    def create(
            cls,
            sku: str,
            warehouse_id: str,
            physical_quantity: int) -> "InventoryItem":
        return cls(
            sku=sku,
            warehouse_id=warehouse_id,
            physical_quantity=physical_quantity,
            reserved_quantity=0,
            version_number=0
        )

    @classmethod
    def restore(
            cls,
            sku: str,
            warehouse_id: str,
            physical_quantity: int,
            reserved_quantity: int,
            version_number: int) -> "InventoryItem":
        return cls(
            sku=sku,
            warehouse_id=warehouse_id,
            physical_quantity=physical_quantity,
            reserved_quantity=reserved_quantity,
            version_number=version_number
        )

    @property
    def key(self) -> tuple[str, str]:
        return self._sku, self._warehouse_id

    @property
    def available_quantity(self) -> int:
        return self._physical_quantity - self._reserved_quantity

    @property
    def physical_quantity(self) -> int:
        return self._physical_quantity

    @property
    def reserved_quantity(self) -> int:
        return self._reserved_quantity

    def increase_quantity(self, quantity: int) -> None:
        check_positive(self, quantity)
        self._physical_quantity += quantity

    def decrease_quantity(self, quantity: int) -> None:
        check_positive(self, quantity)
        if quantity > self._physical_quantity:
            raise InvalidValueForTheOperation(self, quantity)
        self._physical_quantity -= quantity

    def reserve(self, quantity: int) -> None:
        check_positive(self, quantity)
        if quantity > self.available_quantity:
            raise InvalidValueForTheOperation(self, quantity)
        self._reserved_quantity += quantity

    def cancel_reserve(self, quantity: int) -> None:
        check_positive(self, quantity)
        if quantity > self._reserved_quantity:
            raise InvalidValueForTheOperation(self, quantity)
        self._reserved_quantity -= quantity

    def shipment(self, quantity: int) -> None:
        check_positive(self, quantity)
        if quantity > self._reserved_quantity:
            raise InvalidValueForTheOperation(self, quantity)
        self._physical_quantity -= quantity
        self._reserved_quantity -= quantity


@dataclass(frozen=True)
class ReservedInventoryItem:
    """Объекты создаются и получаются через cls-методы: create, restore."""

    @enum.unique
    class ReservedInventoryItemStatus(enum.Enum):
        reserved = "Reserved"
        shipped = "Shipped"
        cancelled = "Cancelled"
        returned = "Returned"

    _STATUS_LIFECYCLE = {
        ReservedInventoryItemStatus.reserved: (ReservedInventoryItemStatus.shipped,
                                               ReservedInventoryItemStatus.cancelled),
        ReservedInventoryItemStatus.shipped: (ReservedInventoryItemStatus.returned,),
        ReservedInventoryItemStatus.cancelled: (),
        ReservedInventoryItemStatus.returned: (),
    }

    sku: str
    warehouse_id: str
    quantity: int
    status: ReservedInventoryItemStatus

    @classmethod
    def create(
            cls,
            sku: str,
            warehouse_id: str,
            quantity: int) -> "ReservedInventoryItem":
        return cls(
            sku=sku,
            warehouse_id=warehouse_id,
            quantity=quantity,
            status=cls.ReservedInventoryItemStatus.reserved,
        )

    @classmethod
    def restore(
            cls,
            sku: str,
            warehouse_id: str,
            quantity: int,
            status: ReservedInventoryItemStatus) -> "ReservedInventoryItem":
        return cls(
            sku=sku,
            warehouse_id=warehouse_id,
            quantity=quantity,
            status=status,
        )

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("The quantity value must be greater zero.")

    @property
    def key(self) -> tuple[str, str]:
        return self.sku, self.warehouse_id

    def _transition_to_new_status(self, status: ReservedInventoryItemStatus) -> "ReservedInventoryItem":
        try:
            transition_to_new_status(self.status, status, self._STATUS_LIFECYCLE)
            return replace(self, status=status)
        except InvalidStatusTransition:
            raise

    def shipped_status(self) -> "ReservedInventoryItem":
        return self._transition_to_new_status(self.ReservedInventoryItemStatus.shipped)

    def cancelled_status(self) -> "ReservedInventoryItem":
        return self._transition_to_new_status(self.ReservedInventoryItemStatus.cancelled)

    def returned_status(self) -> "ReservedInventoryItem":
        return self._transition_to_new_status(self.ReservedInventoryItemStatus.returned)


class Allocation(BaseAggregate):

    def __init__(
            self,
            order_id: str,
            reserved_inv_items: list[ReservedInventoryItem],
            version_number: int):
        """Объекты создаются и получаются через cls-методы: create, restore."""
        super().__init__(version_number)
        self._order_id = order_id
        self._reserved_inv_items = reserved_inv_items

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def reserved_inv_items(self) -> tuple[ReservedInventoryItem, ...]:
        return tuple(self._reserved_inv_items)

    @property
    def reserved_quantity_for_key(self) -> dict[tuple[str, str], int]:
        return {(item.sku, item.warehouse_id): item.quantity for item in self._reserved_inv_items}

    @classmethod
    def create(
            cls,
            order_id: str,
            required_items: dict[str, int],
            inv_items_list: dict[tuple[str, str], int]) -> "Allocation":

        reserved_inv_items: list[ReservedInventoryItem] = []

        for sku, quan in required_items.items():
            inv_items = {
                (key_sku, key_warehouse_id): available_quan
                for (key_sku, key_warehouse_id), available_quan in inv_items_list.items()
                if key_sku == sku
            }

            """Политика сортировки."""
            inv_items = dict(sorted(inv_items.items(), key=lambda inv_item: inv_item[1]))

            for (key_sku, key_warehouse_id), available_quan in inv_items.items():
                if available_quan >= quan:
                    res_item = ReservedInventoryItem.create(
                        sku=key_sku,
                        warehouse_id=key_warehouse_id,
                        quantity=quan
                    )
                    reserved_inv_items.append(res_item)
                    quan = 0
                    break
                elif 0 < available_quan < quan:
                    res_item = ReservedInventoryItem.create(
                        sku=key_sku,
                        warehouse_id=key_warehouse_id,
                        quantity=available_quan
                    )
                    quan -= available_quan
                    reserved_inv_items.append(res_item)

            if quan > 0:
                raise InsufficientStockInTheWarehouse(sku)

        return cls(
            order_id=order_id,
            reserved_inv_items=reserved_inv_items,
            version_number=0
        )

    @classmethod
    def restore(
            cls,
            order_id: str,
            reserved_inv_items: list[ReservedInventoryItem],
            version_number: int) -> "Allocation":
        return cls(
            order_id=order_id,
            reserved_inv_items=reserved_inv_items,
            version_number=version_number
        )

    # def ship_items(self) -> None:
    #     for i, res_item in enumerate(self.reserved_inv_items):
    #         self._reserved_inv_items[i] = self._reserved_inv_items[i].shipped_status()
    #
    # def cancel_items_reservation(self) -> None:
    #     for i, res_item in enumerate(self.reserved_inv_items):
    #         self._reserved_inv_items[i] = res_item.cancelled_status()

    # def return_items(self) -> None:
    #     for i, res_item in enumerate(self.reserved_inv_items):
    #         self._reserved_inv_items[i] = res_item.returned_status()


"""
Раздел магазина
"""


@dataclass(frozen=True)
class Person:
    person_id: str
    first_name: str
    last_name: str
    email: str


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.unit_price <= 0:
            raise ValueError("Unit price must be greater than zero")

    def increase_price(self, price: Decimal) -> "Product":
        check_positive(self, price)
        return replace(self, unit_price=self.unit_price + price)

    def decrease_price(self, price: Decimal) -> "Product":
        check_positive(self, price)
        if self.unit_price - price <= 0:
            raise InvalidValueForTheOperation(self, price)
        return replace(self, unit_price=self.unit_price - price)


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int

    @property
    def cart_line_price(self) -> Decimal:
        return self.product.unit_price * self.quantity

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")

    def increase_quantity(self, quantity: int) -> "CartLine":
        check_positive(self, quantity)
        return replace(self, quantity=self.quantity + quantity)

    def decrease_quantity(self, quantity: int) -> "CartLine":
        check_positive(self, quantity)
        if self.quantity - quantity <= 0:
            raise InvalidValueForTheOperation(self, quantity)
        return replace(self, quantity=self.quantity - quantity)


class Cart(BaseAggregate):

    def __init__(
            self,
            person: Person,
            cart_lines: dict[str, CartLine],
            version_number: int):
        """Объекты создаются и получаются через cls-методы: create, restore."""
        super().__init__(version_number)
        self._person = person
        self._cart_lines = cart_lines

    @classmethod
    def create(cls, person: Person) -> "Cart":
        return cls(
            person=person,
            cart_lines=dict(),
            version_number=0
        )

    @classmethod
    def restore(
            cls,
            person: Person,
            cart_lines: dict[str, CartLine],
            version_number: int) -> "Cart":
        return cls(
            person=person,
            cart_lines=cart_lines,
            version_number=version_number
        )

    @property
    def person(self) -> Person:
        return self._person

    @property
    def all_sku(self) -> list[str]:
        return list(self._cart_lines.keys())

    @property
    def cart_lines(self) -> dict[str, CartLine]:
        return MappingProxyType(self._cart_lines)

    @property
    def price_of_cart(self) -> Decimal:
        return Decimal(sum(line.cart_line_price for line in self._cart_lines.values()))

    def add_product(self, product: Product, quantity: int) -> None:
        if product.sku not in self._cart_lines:
            self._cart_lines[product.sku] = CartLine(product=product, quantity=quantity)
        else:
            self._cart_lines[product.sku] = self._cart_lines[product.sku].increase_quantity(quantity)

    def remove_product(self, product: Product, quantity: int) -> None:
        if product.sku in self._cart_lines:
            line = self._cart_lines.get(product.sku)
            if line.quantity == quantity:
                del self._cart_lines[product.sku]
            else:
                if line.quantity > quantity:
                    self._cart_lines[product.sku] = line.decrease_quantity(quantity)
                else:
                    raise InvalidValueForTheOperation(line, quantity)
        else:
            raise ProductDoesNotExistInCart(product, self)

    def clear_product(self, product: Product) -> None:
        if product.sku in self._cart_lines:
            del self._cart_lines[product.sku]
        else:
            raise ProductDoesNotExistInCart(product, self)

    def clear_cart(self) -> None:
        self._cart_lines.clear()


@dataclass(frozen=True)
class OrderLine:
    product_sku: str
    product_name: str
    quantity: int
    line_price: Decimal

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("The quantity value must be greater than zero.")
        if self.line_price <= Decimal(0):
            raise ValueError("The line_price value must be greater than zero.")


class Order(BaseAggregate):

    @enum.unique
    class OrderStatus(enum.Enum):
        in_progress = "In progress"
        en_route = "En route"
        delivered = "Delivered"
        cancelled = "Cancelled"
        returned = "Returned"

    _STATUS_LIFECYCLE: dict[OrderStatus, tuple[OrderStatus, ...]] = {
        OrderStatus.in_progress: (OrderStatus.en_route, OrderStatus.cancelled),
        OrderStatus.en_route: (OrderStatus.delivered, OrderStatus.cancelled),
        OrderStatus.delivered: (OrderStatus.returned,),
        OrderStatus.cancelled: (),
        OrderStatus.returned: (),
    }

    def __init__(
            self,
            order_id: str,
            person: Person,
            order_lines: dict[str, OrderLine],
            final_price: Decimal,
            status: OrderStatus,
            version_number: int):
        """Объекты создаются и получаются через cls-методы: create, restore."""
        super().__init__(version_number)

        if not order_lines:
            raise TheOrderLinesDoesNotExist()

        self._order_id = order_id
        self._person = person
        self._order_lines = order_lines
        self._final_price = final_price
        self._status = status

    @classmethod
    def create(
            cls,
            person: Person,
            order_lines: dict[str, OrderLine]) -> "Order":
        return cls(
            order_id=str(uuid.uuid4()),
            person=person,
            order_lines=order_lines,
            final_price=cls.calculate_final_price(order_lines),
            status=cls.OrderStatus.in_progress,
            version_number=0
        )

    @classmethod
    def restore(
            cls,
            order_id: str,
            person: Person,
            order_lines: dict[str, OrderLine],
            final_price: Decimal,
            status: OrderStatus,
            version_number: int) -> "Order":
        return cls(
            order_id=order_id,
            person=person,
            order_lines=order_lines,
            final_price=final_price,
            status=status,
            version_number=version_number
        )

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def person_id(self) -> str:
        return self._person.person_id

    @property
    def final_price(self) -> Decimal:
        return self._final_price

    @property
    def order_lines(self) -> dict[str, OrderLine]:
        return MappingProxyType(self._order_lines)

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def all_sku(self) -> list[str]:
        return list(self._order_lines.keys())

    @property
    def quantity_for_sku(self) -> dict[str, int]:
        return {sku: line.quantity for sku, line in self._order_lines.items()}

    @staticmethod
    def calculate_final_price(order_lines: dict[str, OrderLine]) -> Decimal:
        return Decimal(sum(line.line_price for line in order_lines.values()))

    def _transition_to_new_status(self, status: OrderStatus) -> None:
        try:
            transition_to_new_status(self._status, status, self._STATUS_LIFECYCLE)
            self._status = status
        except InvalidStatusTransition:
            raise

    def en_route_order(self) -> None:
        self._transition_to_new_status(self.OrderStatus.en_route)

    def cancel_order(self) -> None:
        self._transition_to_new_status(self.OrderStatus.cancelled)

    def deliver_order(self) -> None:
        self._transition_to_new_status(self.OrderStatus.delivered)

    def return_order(self) -> None:
        self._transition_to_new_status(self.OrderStatus.returned)