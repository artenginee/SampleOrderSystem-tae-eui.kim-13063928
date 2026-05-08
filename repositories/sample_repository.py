"""
SampleRepository — samples 테이블 CRUD.
SQL은 파라미터 바인딩(?) 사용. f-string SQL 금지.
"""
import sqlite3
from database.db_manager import DatabaseManager
from models.sample import Sample
from repositories.base_repository import BaseRepository


class SampleRepository(BaseRepository[Sample]):
    def __init__(self, db: DatabaseManager):
        self._db = db

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------

    def _row_to_sample(self, row: sqlite3.Row) -> Sample:
        """sqlite3.Row → Sample 도메인 모델 변환."""
        return Sample(
            id=str(row["sample_id"]),
            name=row["name"],
            avg_production_time=row["avg_production_time"],
            yield_rate=row["yield_rate"],
            stock=row["stock"],
        )

    # ------------------------------------------------------------------
    # BaseRepository 구현
    # ------------------------------------------------------------------

    def create(self, entity: Sample) -> Sample:
        """Sample을 DB에 INSERT하고 DB 할당 ID(str)를 반영한 Sample을 반환한다."""
        last_id = self._db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate, stock) VALUES (?, ?, ?, ?)",
            (entity.name, entity.avg_production_time, entity.yield_rate, entity.stock),
        )
        entity.id = str(last_id)
        return entity

    def find_by_id(self, id: int) -> Sample | None:
        """sample_id로 Sample을 조회한다."""
        row = self._db.query_one(
            "SELECT * FROM samples WHERE sample_id = ?",
            (id,),
        )
        if row is None:
            return None
        return self._row_to_sample(row)

    def find_all(self) -> list[Sample]:
        """모든 Sample을 반환한다."""
        rows = self._db.query("SELECT * FROM samples")
        return [self._row_to_sample(row) for row in rows]

    def update(self, entity: Sample) -> Sample:
        """Sample 정보를 DB에 업데이트하고 갱신된 Sample을 반환한다."""
        self._db.execute(
            """UPDATE samples
               SET name = ?, avg_production_time = ?, yield_rate = ?, stock = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE sample_id = ?""",
            (entity.name, entity.avg_production_time, entity.yield_rate, entity.stock,
             int(entity.id)),
        )
        return entity

    def delete(self, id: int) -> bool:
        """sample_id로 Sample을 삭제한다. 삭제된 행이 있으면 True."""
        row = self._db.query_one("SELECT sample_id FROM samples WHERE sample_id = ?", (id,))
        if row is None:
            return False
        self._db.execute("DELETE FROM samples WHERE sample_id = ?", (id,))
        return True

    def count(self) -> int:
        """저장된 Sample 수를 반환한다."""
        row = self._db.query_one("SELECT COUNT(*) as cnt FROM samples")
        return row["cnt"]

    # ------------------------------------------------------------------
    # 추가 메서드
    # ------------------------------------------------------------------

    def find_by_name(self, keyword: str) -> list[Sample]:
        """이름에 keyword가 포함된 Sample 목록을 반환한다 (부분 일치, 대소문자 무관)."""
        rows = self._db.query(
            "SELECT * FROM samples WHERE name LIKE ?",
            (f"%{keyword}%",),
        )
        return [self._row_to_sample(row) for row in rows]

    def update_stock(self, sample_id: int, delta: int) -> bool:
        """stock += delta. 대상이 없으면 False."""
        row = self._db.query_one("SELECT sample_id FROM samples WHERE sample_id = ?", (sample_id,))
        if row is None:
            return False
        self._db.execute(
            "UPDATE samples SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP WHERE sample_id = ?",
            (delta, sample_id),
        )
        return True
