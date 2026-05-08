from interfaces.i_production_controller import IProductionController
from repositories.production_job_repository import ProductionJobRepository
from models.production_job import ProductionJob, JobStatus


class ProductionController(IProductionController):
    def __init__(self, repo: ProductionJobRepository):
        self._repo = repo
        self._enqueue_counter: int = 0

    def enqueue(self, order_id: str, sample_id: str, planned_quantity: int, yield_rate: float, avg_production_time: float) -> ProductionJob:
        self._enqueue_counter += 1
        total_time_min = avg_production_time * planned_quantity
        in_progress = self._repo.find_in_progress()
        status = JobStatus.WAITING if in_progress else JobStatus.IN_PROGRESS
        job = ProductionJob(
            job_id="",
            order_id=order_id,
            sample_id=sample_id,
            planned_quantity=planned_quantity,
            actual_quantity=0,
            total_time_min=total_time_min,
            queue_order=self._enqueue_counter,
            status=status,
        )
        return self._repo.create(job)

    def find_in_progress(self):
        return self._repo.find_in_progress()

    def find_waiting_queue(self) -> list:
        return self._repo.find_waiting_queue()

    def update_status(self, job_id: str, new_status: JobStatus) -> bool:
        result = self._repo.update_status(job_id, new_status)
        if result and new_status == JobStatus.COMPLETED:
            self._try_start_next()
        return result

    def _try_start_next(self):
        """대기 큐에서 다음 작업을 꺼내 IN_PROGRESS로 전환한다."""
        waiting = self._repo.find_waiting_queue()
        if waiting:
            self._repo.update_status(waiting[0].job_id, JobStatus.IN_PROGRESS)
