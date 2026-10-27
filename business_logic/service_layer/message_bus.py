import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Callable, Union, Deque
from business_logic.domain.events import Event
from business_logic.domain.commands import Command
from business_logic.service_layer.uow import AbstractUnitOfWork
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential


Message = Union[Command, Event]


class AbstractMessageBus(ABC):

    @abstractmethod
    def handle(self, message: Message) -> None:
        raise NotImplementedError

    @abstractmethod
    def handle_commands(self, message: Message, queue: Deque, uow: AbstractUnitOfWork) -> None:
        raise NotImplementedError

    @abstractmethod
    def handle_events(self, message: Message, queue: Deque, uow: AbstractUnitOfWork) -> None:
        raise NotImplementedError


class MessageBus(AbstractMessageBus):

    def __init__(
            self,
            uow_factory: Callable[[], AbstractUnitOfWork],
            handlers_event: dict[type[Event], list[Callable]] | None = None,
            handlers_command: dict[type[Command], Callable] | None = None) -> None:

        self.queue: Deque[Message] = deque()
        self.uow_factory = uow_factory
        self.handlers_event = handlers_event if handlers_event is not None else {}
        self.handlers_command = handlers_command if handlers_command is not None else {}

    def handle(self, message: Message):
        self.queue.append(message)
        while self.queue:
            message = self.queue.popleft()
            if isinstance(message, Command):
                self.handle_commands(message, self.queue, self.uow_factory())
            elif isinstance(message, Event):
                self.handle_events(message, self.queue, self.uow_factory())
            else:
                raise Exception(f'{message} was not an Event or Command')

    def handle_commands(self, command: Command, queue: Deque[Message], uow: AbstractUnitOfWork) -> None:
        logging.debug(f'Handling command: {command}')
        try:
            handler = self.handlers_command.get(type(command))
            if handler is None:
                raise Exception(f'{command} was not a Command')
            else:
                handler(command, uow)
                queue.extend(uow.collect_new_messages())
        except Exception as e:
            logging.error(e)
            raise e

    def handle_events(self, event: Event, queue: Deque[Message], uow: AbstractUnitOfWork) -> None:
        for handler in self.handlers_event.get(type(event), []):
            try:
                for attempt in Retrying(stop=stop_after_attempt(3), wait=wait_exponential()):
                    with attempt:
                        logging.debug('handling event %s with handler %s', event, handler)
                        handler(event)
                        queue.extend(uow.collect_new_messages())
            except RetryError as retry_ex:
                logging.error('Failed to process the event %s once, refusal!',
                              retry_ex.last_attempt.attempt_number)
                continue