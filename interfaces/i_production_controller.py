from abc import ABC, abstractmethod
from models.production_job import ProductionJob, JobStatus


class IProductionController(ABC):
    @abstractmethod
    def enqueue(self, order_id: str, sample_id: str, planned_quantity: int, yield_rate: float, avg_production_time: float) -> ProductionJob:
        ...

    @abstractmethod
    def find_in_progress(self):
        ...

    @abstractmethod
    def find_waiting_queue(self) -> list:
        ...

    @abstractmethod
    def update_status(self, job_id: str, new_status: JobStatus) -> bool:
        ...
