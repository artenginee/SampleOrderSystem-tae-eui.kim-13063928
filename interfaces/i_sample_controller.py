from abc import ABC, abstractmethod
from models.sample import Sample


class ISampleController(ABC):
    @abstractmethod
    def create(self, name: str, avg_production_time: float, yield_rate: float, initial_stock: int = 0) -> Sample:
        ...

    @abstractmethod
    def find_all(self) -> list:
        ...

    @abstractmethod
    def find_by_id(self, sample_id: str):
        ...

    @abstractmethod
    def find_by_name(self, keyword: str) -> list:
        ...

    @abstractmethod
    def update(self, sample_id: str, name: str, avg_production_time: float, yield_rate: float) -> bool:
        ...

    @abstractmethod
    def delete(self, sample_id: str) -> bool:
        ...

    @abstractmethod
    def update_stock(self, sample_id: str, delta: int) -> bool:
        ...
