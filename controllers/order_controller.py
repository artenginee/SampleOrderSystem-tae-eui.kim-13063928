from interfaces.i_order_controller import IOrderController
from repositories.order_repository import OrderRepository
from models.order import Order, OrderStatus


class OrderController(IOrderController):
    def __init__(self, repo: OrderRepository):
        self._repo = repo

    def create(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        order = Order(
            id="",
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=OrderStatus.RESERVED,
        )
        return self._repo.create(order)

    def find_all(self) -> list:
        return self._repo.find_all()

    def find_by_id(self, order_id: str):
        return self._repo.find_by_id(order_id)

    def find_by_status(self, status: OrderStatus) -> list:
        return self._repo.find_by_status(status)

    def update_status(self, order_id: str, new_status: OrderStatus) -> bool:
        return self._repo.update_status(order_id, new_status)
