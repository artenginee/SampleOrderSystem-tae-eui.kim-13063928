"""
monitor/adapters.py — IMonitorDataProvider 의 DB 구현체.
DatabaseManager 를 통해 실시간으로 DB 를 조회하여 MonitorSnapshot 을 반환한다.
"""
from datetime import datetime

from database.db_manager import DatabaseManager
from models.order import OrderStatus
from models.production_job import JobStatus
from monitor.interfaces import IMonitorDataProvider, MonitorSnapshot, SampleStockInfo
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_job_repository import ProductionJobRepository


class DBMonitorAdapter(IMonitorDataProvider):
    """SQLite DB 에서 실시간으로 모니터링 스냅샷을 생성하는 어댑터."""

    def __init__(self, db: DatabaseManager):
        self._sample_repo = SampleRepository(db)
        self._order_repo = OrderRepository(db)
        self._job_repo = ProductionJobRepository(db)

    def get_snapshot(self) -> MonitorSnapshot:
        """DB 를 조회하여 현재 시스템 상태 스냅샷을 반환한다."""
        # 주문 상태별 카운트
        order_count_by_status = {s: self._order_repo.count_by_status(s) for s in OrderStatus}

        # 주문 상태별 Order 목록
        orders_by_status = {s: self._order_repo.find_by_status(s) for s in OrderStatus}

        # 활성 주문 (RESERVED + PRODUCING): 재고 부족량 계산에 사용
        active_orders = (
            self._order_repo.find_by_status(OrderStatus.RESERVED)
            + self._order_repo.find_by_status(OrderStatus.PRODUCING)
        )

        # 시료별 재고 정보 계산
        samples = self._sample_repo.find_all()
        stock_info = []
        for s in samples:
            total_order_qty = sum(o.quantity for o in active_orders if o.sample_id == s.id)
            shortage = max(0, total_order_qty - s.stock)
            if s.stock == 0:
                status = "고갈"
            elif s.stock < total_order_qty:
                status = "부족"
            else:
                status = "여유"
            stock_info.append(SampleStockInfo(
                sample_id=s.id,
                name=s.name,
                stock=s.stock,
                total_order_qty=total_order_qty,
                shortage=shortage,
                status=status,
            ))

        return MonitorSnapshot(
            timestamp=datetime.now(),
            order_count_by_status=order_count_by_status,
            sample_stock_info=stock_info,
            current_production=self._job_repo.find_in_progress(),
            production_queue=self._job_repo.find_waiting_queue(),
            orders_by_status=orders_by_status,
        )
