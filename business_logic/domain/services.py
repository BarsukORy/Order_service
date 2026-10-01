from abc import ABC, abstractmethod


class AbstractIdGenerator(ABC):

    @abstractmethod
    def generate_id(self) -> str:
        raise NotImplementedError