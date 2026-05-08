"""
ProductionJobRepository — production_jobs 테이블 CRUD.
SQL은 파라미터 바인딩(?) 사용. f-string SQL 금지.
"""
import sqlite3
from database.db_manager import DatabaseManager
from models.production_job import ProductionJob, JobStatus
from repositories.base_repository import BaseRepository


class ProductionJobRepository(BaseRepository[ProductionJob]):
    def __init__(self, db: DatabaseManager):
        self._db = db

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------

    def _row_to_job(self, row: sqlite3.Row) -> ProductionJob:
        """sqlite3.Row → ProductionJob 도메인 모델 변환."""
        return ProductionJob(
            job_id=str(row["job_id"]),
            order_id=str(row["order_id"]),
            sample_id=str(row["sample_id"]),
            planned_quantity=row["planned_quantity"],
            actual_quantity=row["actual_quantity"],
            total_time_min=row["total_time_min"],
            queue_order=row["queue_order"],
            status=JobStatus(row["status"]),
        )

    # ------------------------------------------------------------------
    # BaseRepository 구현
    # ------------------------------------------------------------------

    def create(self, entity: ProductionJob) -> ProductionJob:
        """ProductionJob을 DB에 INSERT하고 DB 할당 ID(str)를 job_id에 반영한 인스턴스를 반환한다."""
        last_id = self._db.execute(
            """INSERT INTO production_jobs
               (order_id, sample_id, planned_quantity, actual_quantity, total_time_min, status, queue_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (int(entity.order_id), int(entity.sample_id), entity.planned_quantity,
             entity.actual_quantity, entity.total_time_min, entity.status.value,
             entity.queue_order),
        )
        entity.job_id = str(last_id)
        return entity

    def find_by_id(self, id: int) -> ProductionJob | None:
        """job_id로 ProductionJob을 조회한다."""
        row = self._db.query_one(
            "SELECT * FROM production_jobs WHERE job_id = ?",
            (id,),
        )
        if row is None:
            return None
        return self._row_to_job(row)

    def find_all(self) -> list[ProductionJob]:
        """모든 ProductionJob을 반환한다."""
        rows = self._db.query("SELECT * FROM production_jobs")
        return [self._row_to_job(row) for row in rows]

    def update(self, entity: ProductionJob) -> ProductionJob:
        """ProductionJob 정보를 DB에 업데이트하고 갱신된 인스턴스를 반환한다."""
        self._db.execute(
            """UPDATE production_jobs
               SET order_id = ?, sample_id = ?, planned_quantity = ?, actual_quantity = ?,
                   total_time_min = ?, status = ?, queue_order = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE job_id = ?""",
            (int(entity.order_id), int(entity.sample_id), entity.planned_quantity,
             entity.actual_quantity, entity.total_time_min, entity.status.value,
             entity.queue_order, int(entity.job_id)),
        )
        return entity

    def delete(self, id: int) -> bool:
        """job_id로 ProductionJob을 삭제한다. 삭제된 행이 있으면 True."""
        row = self._db.query_one("SELECT job_id FROM production_jobs WHERE job_id = ?", (id,))
        if row is None:
            return False
        self._db.execute("DELETE FROM production_jobs WHERE job_id = ?", (id,))
        return True

    def count(self) -> int:
        """저장된 ProductionJob 수를 반환한다."""
        row = self._db.query_one("SELECT COUNT(*) as cnt FROM production_jobs")
        return row["cnt"]

    # ------------------------------------------------------------------
    # 추가 메서드
    # ------------------------------------------------------------------

    def find_waiting_queue(self) -> list[ProductionJob]:
        """WAITING 상태의 작업을 queue_order ASC 순서로 반환한다."""
        rows = self._db.query(
            "SELECT * FROM production_jobs WHERE status = ? ORDER BY queue_order ASC",
            (JobStatus.WAITING.value,),
        )
        return [self._row_to_job(row) for row in rows]

    def find_in_progress(self) -> ProductionJob | None:
        """IN_PROGRESS 상태의 작업을 반환한다. 없으면 None."""
        row = self._db.query_one(
            "SELECT * FROM production_jobs WHERE status = ? LIMIT 1",
            (JobStatus.IN_PROGRESS.value,),
        )
        if row is None:
            return None
        return self._row_to_job(row)

    def update_status(self, job_id: str, new_status: JobStatus) -> bool:
        """job_id로 ProductionJob 상태를 업데이트한다. 대상 없으면 False."""
        row = self._db.query_one(
            "SELECT job_id FROM production_jobs WHERE job_id = ?",
            (int(job_id),),
        )
        if row is None:
            return False
        self._db.execute(
            "UPDATE production_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            (new_status.value, int(job_id)),
        )
        return True

    def update_actual_quantity(self, job_id: str, quantity: int) -> bool:
        """job_id로 actual_quantity를 업데이트한다. 대상 없으면 False."""
        row = self._db.query_one(
            "SELECT job_id FROM production_jobs WHERE job_id = ?",
            (int(job_id),),
        )
        if row is None:
            return False
        self._db.execute(
            "UPDATE production_jobs SET actual_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            (quantity, int(job_id)),
        )
        return True
