from collections import deque

from interfaces.i_production_controller import IProductionController
from models.production_job import ProductionJob, JobStatus


class ProductionController(IProductionController):
    def __init__(self):
        self._current_job: ProductionJob | None = None
        self._queue: deque = deque()
        self._counter: int = 0
        self._enqueue_counter: int = 0

    def enqueue(self, order_id: str, sample_id: str, planned_quantity: int, yield_rate: float, avg_production_time: float) -> ProductionJob:
        self._counter += 1
        self._enqueue_counter += 1
        job_id = f"J{self._counter:03d}"

        total_time_min = avg_production_time * planned_quantity

        if self._current_job is None:
            # 최초 작업: 즉시 IN_PROGRESS
            job = ProductionJob(
                job_id=job_id,
                order_id=order_id,
                sample_id=sample_id,
                planned_quantity=planned_quantity,
                actual_quantity=0,
                total_time_min=total_time_min,
                queue_order=self._enqueue_counter,
                status=JobStatus.IN_PROGRESS,
            )
            self._current_job = job
        else:
            # 이후 작업: 대기 큐에 추가 WAITING
            job = ProductionJob(
                job_id=job_id,
                order_id=order_id,
                sample_id=sample_id,
                planned_quantity=planned_quantity,
                actual_quantity=0,
                total_time_min=total_time_min,
                queue_order=self._enqueue_counter,
                status=JobStatus.WAITING,
            )
            self._queue.append(job)

        return job

    def find_in_progress(self):
        return self._current_job

    def find_waiting_queue(self) -> list:
        return sorted(list(self._queue), key=lambda j: j.queue_order)

    def update_status(self, job_id: str, new_status: JobStatus) -> bool:
        # 현재 작업 완료 처리
        if self._current_job is not None and self._current_job.job_id == job_id:
            self._current_job.status = new_status
            if new_status == JobStatus.COMPLETED:
                self._current_job = None
                self._try_start_next()
            return True

        # 대기 큐에서 찾기
        for job in self._queue:
            if job.job_id == job_id:
                job.status = new_status
                return True

        return False

    def _try_start_next(self):
        """대기 큐에서 다음 작업을 꺼내 IN_PROGRESS로 전환한다."""
        if self._queue:
            next_job = self._queue.popleft()
            next_job.status = JobStatus.IN_PROGRESS
            self._current_job = next_job
