from interfaces.i_order_controller import IOrderController
from models.order import Order, OrderStatus


class OrderController(IOrderController):
    def __init__(self):
        self._orders: list = []
        self._counter: int = 0

    def create(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        self._counter += 1
        order_id = f"O{self._counter}"
        order = Order(
            id=order_id,
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=OrderStatus.RESERVED,
        )
        self._orders.append(order)
        return order

    def find_all(self) -> list:
        return list(self._orders)

    def find_by_id(self, order_id: str):
        for o in self._orders:
            if o.id == order_id:
                return o
        return None

    def find_by_status(self, status: OrderStatus) -> list:
        return [o for o in self._orders if o.status == status]

    def update_status(self, order_id: str, new_status: OrderStatus) -> bool:
        order = self.find_by_id(order_id)
        if order is None:
            return False
        order.status = new_status
        return True
