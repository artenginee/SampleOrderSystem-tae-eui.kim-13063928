from dataclasses import dataclass, field
from enum import Enum


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"


@dataclass
class Order:
    id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED

    def approve(self, has_stock: bool) -> None:
        """RESERVED → CONFIRMED (재고 충분) / PRODUCING (재고 부족).
        비RESERVED 상태에서 호출 시 ValueError."""
        if self.status != OrderStatus.RESERVED:
            raise ValueError(
                f"approve는 RESERVED 상태에서만 가능합니다. 현재 상태: {self.status.value}"
            )
        if has_stock:
            self.status = OrderStatus.CONFIRMED
        else:
            self.status = OrderStatus.PRODUCING

    def reject(self) -> None:
        """RESERVED → REJECTED, 비RESERVED 상태에서 ValueError."""
        if self.status != OrderStatus.RESERVED:
            raise ValueError(
                f"reject는 RESERVED 상태에서만 가능합니다. 현재 상태: {self.status.value}"
            )
        self.status = OrderStatus.REJECTED

    def complete_production(self) -> None:
        """PRODUCING → CONFIRMED, 비PRODUCING 상태에서 ValueError."""
        if self.status != OrderStatus.PRODUCING:
            raise ValueError(
                f"complete_production은 PRODUCING 상태에서만 가능합니다. 현재 상태: {self.status.value}"
            )
        self.status = OrderStatus.CONFIRMED

    def release(self) -> None:
        """CONFIRMED → RELEASE, 비CONFIRMED 상태에서 ValueError."""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError(
                f"release는 CONFIRMED 상태에서만 가능합니다. 현재 상태: {self.status.value}"
            )
        self.status = OrderStatus.RELEASE
