"""
monitor/interfaces.py — 모니터링 도구 추상 계약.
IMonitorDataProvider 와 MonitorSnapshot 데이터 클래스를 정의한다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.order import Order, OrderStatus
from models.production_job import ProductionJob


@dataclass
class SampleStockInfo:
    """시료별 재고 현황 정보."""
    sample_id: str
    name: str
    stock: int
    total_order_qty: int   # RESERVED + PRODUCING 주문량 합계
    shortage: int          # max(0, total_order_qty - stock)
    status: str            # "여유" / "부족" / "고갈"


@dataclass
class MonitorSnapshot:
    """모니터링 대시보드에서 한 번의 조회로 모든 패널이 공유하는 스냅샷."""
    timestamp: datetime
    order_count_by_status: dict            # dict[OrderStatus, int]
    sample_stock_info: list                # list[SampleStockInfo]
    current_production: Optional[ProductionJob]
    production_queue: list                 # list[ProductionJob]
    orders_by_status: dict                 # dict[OrderStatus, list[Order]]


class IMonitorDataProvider(ABC):
    """모니터링 데이터 공급자 인터페이스."""

    @abstractmethod
    def get_snapshot(self) -> MonitorSnapshot:
        """현재 시스템 상태 스냅샷을 반환한다."""
        ...
