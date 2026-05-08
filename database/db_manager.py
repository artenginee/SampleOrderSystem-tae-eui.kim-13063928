"""
DatabaseManager — SQLite 싱글톤 관리자
POC2 기반. 직접 sqlite3.connect() 호출 금지. 반드시 get_instance()를 통한다.
"""
import sqlite3


class DatabaseManager:
    _instances: dict[str, "DatabaseManager"] = {}

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_pragma()
        self._init_schema()

    @classmethod
    def get_instance(cls, db_path: str = "data/order_system.db") -> "DatabaseManager":
        """경로별 싱글톤 인스턴스를 반환한다."""
        if db_path not in cls._instances:
            cls._instances[db_path] = cls(db_path)
        return cls._instances[db_path]

    def _init_pragma(self) -> None:
        """PRAGMA 설정: foreign_keys ON, journal_mode WAL."""
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.commit()

    def _init_schema(self) -> None:
        """DDL 실행 — 테이블이 없는 경우에만 생성."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS samples (
                sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                avg_production_time REAL NOT NULL,
                yield_rate REAL NOT NULL CHECK(yield_rate > 0 AND yield_rate <= 1),
                stock INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                sample_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                status TEXT DEFAULT 'RESERVED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
            );

            CREATE TABLE IF NOT EXISTS production_jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                sample_id INTEGER NOT NULL,
                planned_quantity INTEGER NOT NULL,
                actual_quantity INTEGER DEFAULT 0,
                total_time_min REAL NOT NULL,
                status TEXT DEFAULT 'WAITING',
                queue_order INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
            );
        """)
        self._conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """SELECT 쿼리를 실행하고 모든 결과 행을 list로 반환한다."""
        cursor = self._conn.execute(sql, params)
        return cursor.fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """SELECT 쿼리를 실행하고 첫 번째 결과 행을 반환한다. 없으면 None."""
        cursor = self._conn.execute(sql, params)
        return cursor.fetchone()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE 쿼리를 실행하고 lastrowid를 int로 반환한다."""
        cursor = self._conn.execute(sql, params)
        self._conn.commit()
        return cursor.lastrowid

    def execute_many(self, sql: str, params_list: list) -> None:
        """동일한 SQL을 여러 파라미터 세트로 실행한다 (다중 INSERT 등)."""
        self._conn.executemany(sql, params_list)
        self._conn.commit()
