from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


@dataclass
class ProductionJob:
    job_id: str
    order_id: str
    sample_id: str
    planned_quantity: int
    actual_quantity: int
    total_time_min: float
    queue_order: int = 0
    status: JobStatus = JobStatus.WAITING
    enqueued_at: datetime = field(default_factory=datetime.now)
