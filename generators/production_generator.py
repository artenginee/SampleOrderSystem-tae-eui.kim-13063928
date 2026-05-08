"""
ProductionGenerator — PRODUCING 상태 주문에 대해 ProductionJob을 생성한다.
생산량 공식 (POC4 기준): ceil(shortage / (yield_rate * 0.9))
DB 경로는 파라미터로 받으며 하드코딩하지 않는다.
"""
from math import ceil
from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_job_repository import ProductionJobRepository
from models.order import OrderStatus
from models.production_job import ProductionJob, JobStatus


class ProductionGenerator:
    def generate(self, db_path: str = "data/order_system.db") -> list:
        """PRODUCING 상태의 주문마다 ProductionJob을 생성하고 DB에 저장한 뒤 반환한다."""
        db = DatabaseManager.get_instance(db_path)
        sample_repo = SampleRepository(db)
        order_repo = OrderRepository(db)
        job_repo = ProductionJobRepository(db)

        producing_orders = order_repo.find_by_status(OrderStatus.PRODUCING)
        if not producing_orders:
            return []

        jobs = []
        for i, order in enumerate(producing_orders):
            sample = sample_repo.find_by_id(int(order.sample_id))
            if sample is None:
                continue

            shortage = max(0, order.quantity - sample.stock)
            # POC4 공식: ceil(shortage / (yield_rate * 0.9))
            planned_qty = ceil(shortage / (sample.yield_rate * 0.9))
            total_time = sample.avg_production_time * planned_qty

            # 첫 번째 작업은 IN_PROGRESS, 나머지는 WAITING
            status = JobStatus.IN_PROGRESS if i == 0 else JobStatus.WAITING

            job = ProductionJob(
                job_id="",
                order_id=order.id,
                sample_id=sample.id,
                planned_quantity=planned_qty,
                actual_quantity=0,
                total_time_min=total_time,
                queue_order=i + 1,
                status=status,
            )
            jobs.append(job_repo.create(job))
        return jobs
