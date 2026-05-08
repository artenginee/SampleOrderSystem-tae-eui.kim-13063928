from abc import ABC, abstractmethod
from models.order import Order, OrderStatus


class IOrderController(ABC):
    @abstractmethod
    def create(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        ...

    @abstractmethod
    def find_all(self) -> list:
        ...

    @abstractmethod
    def find_by_id(self, order_id: str):
        ...

    @abstractmethod
    def find_by_status(self, status: OrderStatus) -> list:
        ...

    @abstractmethod
    def update_status(self, order_id: str, new_status: OrderStatus) -> bool:
        ...
