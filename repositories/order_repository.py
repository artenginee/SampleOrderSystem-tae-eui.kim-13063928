"""
OrderRepository — orders 테이블 CRUD.
SQL은 파라미터 바인딩(?) 사용. f-string SQL 금지.
"""
import sqlite3
from database.db_manager import DatabaseManager
from models.order import Order, OrderStatus
from repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: DatabaseManager):
        self._db = db

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------

    def _row_to_order(self, row: sqlite3.Row) -> Order:
        """sqlite3.Row → Order 도메인 모델 변환."""
        return Order(
            id=str(row["order_id"]),
            sample_id=str(row["sample_id"]),
            customer_name=row["customer_name"],
            quantity=row["quantity"],
            status=OrderStatus(row["status"]),
        )

    # ------------------------------------------------------------------
    # BaseRepository 구현
    # ------------------------------------------------------------------

    def create(self, entity: Order) -> Order:
        """Order를 DB에 INSERT하고 DB 할당 ID(str)를 반영한 Order를 반환한다."""
        last_id = self._db.execute(
            """INSERT INTO orders (customer_name, sample_id, quantity, status)
               VALUES (?, ?, ?, ?)""",
            (entity.customer_name, int(entity.sample_id), entity.quantity,
             entity.status.value),
        )
        entity.id = str(last_id)
        return entity

    def find_by_id(self, id: int) -> Order | None:
        """order_id로 Order를 조회한다."""
        row = self._db.query_one(
            "SELECT * FROM orders WHERE order_id = ?",
            (id,),
        )
        if row is None:
            return None
        return self._row_to_order(row)

    def find_all(self) -> list[Order]:
        """모든 Order를 반환한다."""
        rows = self._db.query("SELECT * FROM orders")
        return [self._row_to_order(row) for row in rows]

    def update(self, entity: Order) -> Order:
        """Order 정보를 DB에 업데이트하고 갱신된 Order를 반환한다."""
        self._db.execute(
            """UPDATE orders
               SET customer_name = ?, sample_id = ?, quantity = ?, status = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE order_id = ?""",
            (entity.customer_name, int(entity.sample_id), entity.quantity,
             entity.status.value, int(entity.id)),
        )
        return entity

    def delete(self, id: int) -> bool:
        """order_id로 Order를 삭제한다. 삭제된 행이 있으면 True."""
        row = self._db.query_one("SELECT order_id FROM orders WHERE order_id = ?", (id,))
        if row is None:
            return False
        self._db.execute("DELETE FROM orders WHERE order_id = ?", (id,))
        return True

    def count(self) -> int:
        """저장된 Order 수를 반환한다."""
        row = self._db.query_one("SELECT COUNT(*) as cnt FROM orders")
        return row["cnt"]

    # ------------------------------------------------------------------
    # 추가 메서드
    # ------------------------------------------------------------------

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        """해당 상태의 Order 목록을 반환한다."""
        rows = self._db.query(
            "SELECT * FROM orders WHERE status = ?",
            (status.value,),
        )
        return [self._row_to_order(row) for row in rows]

    def find_by_sample(self, sample_id: str) -> list[Order]:
        """해당 sample_id의 Order 목록을 반환한다."""
        rows = self._db.query(
            "SELECT * FROM orders WHERE sample_id = ?",
            (int(sample_id),),
        )
        return [self._row_to_order(row) for row in rows]

    def update_status(self, order_id: str, new_status: OrderStatus) -> bool:
        """order_id로 Order 상태를 업데이트한다. 대상 없으면 False."""
        row = self._db.query_one(
            "SELECT order_id FROM orders WHERE order_id = ?",
            (int(order_id),),
        )
        if row is None:
            return False
        self._db.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
            (new_status.value, int(order_id)),
        )
        return True

    def count_by_status(self, status: OrderStatus) -> int:
        """해당 상태의 Order 수를 반환한다."""
        row = self._db.query_one(
            "SELECT COUNT(*) as cnt FROM orders WHERE status = ?",
            (status.value,),
        )
        return row["cnt"]
