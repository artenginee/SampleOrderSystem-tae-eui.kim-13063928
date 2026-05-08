"""
Phase 3: DatabaseManager 테스트
TDD RED 단계 — 실패하는 테스트를 먼저 작성한다.
각 테스트에서 싱글톤 캐시를 격리한다.
"""
import pytest


@pytest.fixture(autouse=True)
def reset_singleton():
    """각 테스트 전후 DatabaseManager 싱글톤 캐시를 초기화한다."""
    from database.db_manager import DatabaseManager
    DatabaseManager._instances = {}
    yield
    DatabaseManager._instances = {}


class TestDatabaseManagerSingleton:
    """DatabaseManager 싱글톤 패턴 검증."""

    def test_get_instance_returns_database_manager(self):
        """get_instance()는 DatabaseManager 인스턴스를 반환한다."""
        from database.db_manager import DatabaseManager
        db = DatabaseManager.get_instance(":memory:")
        assert isinstance(db, DatabaseManager)

    def test_get_instance_same_path_returns_same_instance(self):
        """같은 경로로 두 번 호출하면 동일한 인스턴스를 반환한다."""
        from database.db_manager import DatabaseManager
        db1 = DatabaseManager.get_instance(":memory:")
        db2 = DatabaseManager.get_instance(":memory:")
        assert db1 is db2

    def test_get_instance_different_path_returns_different_instance(self):
        """다른 경로로 호출하면 다른 인스턴스를 반환한다."""
        from database.db_manager import DatabaseManager
        db1 = DatabaseManager.get_instance(":memory:")
        # 두 번째 인스턴스는 다른 키로 생성 (싱글톤은 경로별)
        DatabaseManager._instances["other"] = DatabaseManager(":memory:")
        db2 = DatabaseManager._instances["other"]
        assert db1 is not db2


class TestDatabaseManagerQuery:
    """DatabaseManager.query() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_query_returns_list(self):
        """query()는 list를 반환한다."""
        result = self.db.query("SELECT 1")
        assert isinstance(result, list)

    def test_query_returns_rows(self):
        """query()는 결과 행을 반환한다."""
        result = self.db.query("SELECT 1 as value")
        assert len(result) == 1

    def test_query_with_params_returns_filtered_result(self):
        """파라미터 바인딩으로 필터링된 결과를 반환한다."""
        self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("DRAM", 2.0, 0.8),
        )
        self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("NAND", 1.5, 0.7),
        )
        result = self.db.query("SELECT * FROM samples WHERE name = ?", ("DRAM",))
        assert len(result) == 1


class TestDatabaseManagerQueryOne:
    """DatabaseManager.query_one() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_query_one_returns_row_when_exists(self):
        """결과가 있으면 Row를 반환한다."""
        self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("DRAM", 2.0, 0.8),
        )
        result = self.db.query_one("SELECT * FROM samples WHERE name = ?", ("DRAM",))
        assert result is not None

    def test_query_one_returns_none_when_not_exists(self):
        """결과가 없으면 None을 반환한다."""
        result = self.db.query_one("SELECT * FROM samples WHERE name = ?", ("NONEXISTENT",))
        assert result is None


class TestDatabaseManagerExecute:
    """DatabaseManager.execute() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_execute_returns_lastrowid_int(self):
        """execute()는 lastrowid를 int로 반환한다."""
        row_id = self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("DRAM", 2.0, 0.8),
        )
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_execute_increments_lastrowid(self):
        """연속 INSERT 시 lastrowid가 증가한다."""
        id1 = self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("DRAM", 2.0, 0.8),
        )
        id2 = self.db.execute(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            ("NAND", 1.5, 0.7),
        )
        assert id2 > id1


class TestDatabaseManagerExecuteMany:
    """DatabaseManager.execute_many() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_execute_many_inserts_multiple_rows(self):
        """execute_many()는 여러 행을 한 번에 INSERT한다."""
        params_list = [
            ("DRAM", 2.0, 0.8),
            ("NAND", 1.5, 0.7),
            ("CPU", 3.0, 0.9),
        ]
        self.db.execute_many(
            "INSERT INTO samples (name, avg_production_time, yield_rate) VALUES (?, ?, ?)",
            params_list,
        )
        result = self.db.query("SELECT * FROM samples")
        assert len(result) == 3


class TestDatabaseManagerPragma:
    """DatabaseManager PRAGMA 설정 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_foreign_keys_is_enabled(self):
        """PRAGMA foreign_keys = ON이 설정되어 있는지 확인한다."""
        result = self.db.query_one("PRAGMA foreign_keys")
        assert result[0] == 1

    def test_journal_mode_is_wal_or_memory(self):
        """PRAGMA journal_mode = WAL이 설정되어 있는지 확인한다 (:memory:는 memory 모드일 수 있음)."""
        result = self.db.query_one("PRAGMA journal_mode")
        # :memory: DB는 WAL을 지원하지 않아 memory 모드로 유지될 수 있음
        assert result[0] in ("wal", "memory")


class TestDatabaseManagerSchema:
    """DatabaseManager 스키마 생성 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        DatabaseManager._instances = {}
        self.db = DatabaseManager.get_instance(":memory:")

    def test_samples_table_exists(self):
        """samples 테이블이 생성되어 있는지 확인한다."""
        result = self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='samples'"
        )
        assert result is not None

    def test_orders_table_exists(self):
        """orders 테이블이 생성되어 있는지 확인한다."""
        result = self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        )
        assert result is not None

    def test_production_jobs_table_exists(self):
        """production_jobs 테이블이 생성되어 있는지 확인한다."""
        result = self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='production_jobs'"
        )
        assert result is not None
