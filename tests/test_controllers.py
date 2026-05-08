"""
Phase 4: 컨트롤러 Repository 주입 방식 테스트
기존 Phase 2 인메모리 테스트를 DB 기반 Repository 주입 구조로 수정한다.
"""
import pytest
from models.order import Order, OrderStatus
from models.sample import Sample
from models.production_job import ProductionJob, JobStatus


# ---------------------------------------------------------------------------
# SampleController 테스트
# ---------------------------------------------------------------------------

class TestSampleControllerCreate:
    """SampleController.create() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}           # 싱글톤 격리
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_create_returns_sample_instance(self):
        """create()는 Sample 인스턴스를 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        assert isinstance(sample, Sample)

    def test_create_first_id_is_assigned(self):
        """첫 번째 생성된 Sample에 DB 할당 ID가 부여된다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        assert sample.id is not None and sample.id != ""

    def test_create_second_id_is_different_from_first(self):
        """두 번째 생성된 Sample의 ID는 첫 번째와 다르다."""
        sample1 = self.ctrl.create("DRAM", 2.0, 0.8)
        sample2 = self.ctrl.create("NAND", 1.5, 0.7)
        assert sample1.id != sample2.id

    def test_create_stores_fields_correctly(self):
        """create()는 전달된 필드를 올바르게 저장한다."""
        sample = self.ctrl.create("CPU", 3.0, 0.9, initial_stock=100)
        assert sample.name == "CPU"
        assert sample.avg_production_time == 3.0
        assert sample.yield_rate == 0.9
        assert sample.stock == 100

    def test_create_default_stock_is_zero(self):
        """initial_stock을 지정하지 않으면 기본값 0이어야 한다."""
        sample = self.ctrl.create("GPU", 1.0, 0.85)
        assert sample.stock == 0


class TestSampleControllerFindAll:
    """SampleController.find_all() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_find_all_empty_initially(self):
        """생성 전에는 빈 리스트를 반환한다."""
        assert self.ctrl.find_all() == []

    def test_find_all_returns_created_samples(self):
        """생성된 모든 Sample을 반환한다."""
        self.ctrl.create("DRAM", 2.0, 0.8)
        self.ctrl.create("NAND", 1.5, 0.7)
        result = self.ctrl.find_all()
        assert len(result) == 2


class TestSampleControllerFindById:
    """SampleController.find_by_id() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_find_by_id_returns_sample_when_exists(self):
        """존재하는 ID로 조회하면 Sample을 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        result = self.ctrl.find_by_id(sample.id)
        assert result is not None
        assert result.id == sample.id

    def test_find_by_id_returns_none_when_not_exists(self):
        """존재하지 않는 ID로 조회하면 None을 반환한다."""
        result = self.ctrl.find_by_id("9999")
        assert result is None


class TestSampleControllerFindByName:
    """SampleController.find_by_name() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))
        self.ctrl.create("DRAM-DDR5", 2.0, 0.8)
        self.ctrl.create("NAND Flash", 1.5, 0.7)
        self.ctrl.create("ARM CPU", 3.0, 0.9)

    def test_find_by_name_returns_matching_samples(self):
        """키워드가 포함된 Sample 목록을 반환한다."""
        result = self.ctrl.find_by_name("DRAM")
        assert len(result) == 1
        assert result[0].name == "DRAM-DDR5"

    def test_find_by_name_case_insensitive(self):
        """대소문자 무관하게 검색된다."""
        result = self.ctrl.find_by_name("dram")
        assert len(result) == 1

    def test_find_by_name_returns_empty_when_no_match(self):
        """일치하는 항목이 없으면 빈 리스트를 반환한다."""
        result = self.ctrl.find_by_name("XYZ")
        assert result == []

    def test_find_by_name_returns_multiple_matches(self):
        """여러 개가 일치하면 모두 반환한다."""
        self.ctrl.create("DRAM-DDR4", 1.8, 0.75)
        result = self.ctrl.find_by_name("DRAM")
        assert len(result) == 2


class TestSampleControllerUpdate:
    """SampleController.update() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_update_returns_true_when_exists(self):
        """존재하는 Sample을 업데이트하면 True를 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        result = self.ctrl.update(sample.id, "DRAM-New", 3.0, 0.9)
        assert result is True

    def test_update_modifies_fields(self):
        """update() 후 필드가 변경된다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        self.ctrl.update(sample.id, "DRAM-New", 3.0, 0.9)
        updated = self.ctrl.find_by_id(sample.id)
        assert updated.name == "DRAM-New"
        assert updated.avg_production_time == 3.0
        assert updated.yield_rate == 0.9

    def test_update_returns_false_when_not_exists(self):
        """존재하지 않는 ID로 update하면 False를 반환한다."""
        result = self.ctrl.update("9999", "XYZ", 1.0, 0.5)
        assert result is False


class TestSampleControllerDelete:
    """SampleController.delete() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_delete_returns_true_when_exists(self):
        """존재하는 Sample을 삭제하면 True를 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        result = self.ctrl.delete(sample.id)
        assert result is True

    def test_delete_removes_sample(self):
        """delete() 후 find_by_id()는 None을 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        self.ctrl.delete(sample.id)
        assert self.ctrl.find_by_id(sample.id) is None

    def test_delete_returns_false_when_not_exists(self):
        """존재하지 않는 ID로 delete하면 False를 반환한다."""
        result = self.ctrl.delete("9999")
        assert result is False


class TestSampleControllerUpdateStock:
    """SampleController.update_stock() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from controllers.sample_controller import SampleController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.ctrl = SampleController(SampleRepository(db))

    def test_update_stock_increases_stock(self):
        """양수 delta로 재고가 증가한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8, initial_stock=50)
        self.ctrl.update_stock(sample.id, 30)
        updated = self.ctrl.find_by_id(sample.id)
        assert updated.stock == 80

    def test_update_stock_decreases_stock(self):
        """음수 delta로 재고가 감소한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
        self.ctrl.update_stock(sample.id, -40)
        updated = self.ctrl.find_by_id(sample.id)
        assert updated.stock == 60

    def test_update_stock_returns_true_when_exists(self):
        """존재하는 Sample의 재고를 변경하면 True를 반환한다."""
        sample = self.ctrl.create("DRAM", 2.0, 0.8)
        result = self.ctrl.update_stock(sample.id, 10)
        assert result is True

    def test_update_stock_returns_false_when_not_exists(self):
        """존재하지 않는 ID로 update_stock하면 False를 반환한다."""
        result = self.ctrl.update_stock("9999", 10)
        assert result is False


# ---------------------------------------------------------------------------
# OrderController 테스트
# ---------------------------------------------------------------------------

class TestOrderControllerCreate:
    """OrderController.create() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.ctrl = OrderController(OrderRepository(db))

    def test_create_returns_order_instance(self):
        """create()는 Order 인스턴스를 반환한다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        assert isinstance(order, Order)

    def test_create_first_order_id_is_assigned(self):
        """첫 번째 생성된 Order에 DB 할당 ID가 부여된다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        assert order.id is not None

    def test_create_second_order_id_is_different_from_first(self):
        """두 번째 생성된 Order의 ID는 첫 번째와 다르다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order1 = self.ctrl.create(sample.id, "고객A", 50)
        order2 = self.ctrl.create(sample.id, "고객B", 100)
        assert order1.id != order2.id

    def test_create_initial_status_is_reserved(self):
        """생성된 Order의 초기 상태는 RESERVED이어야 한다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        assert order.status == OrderStatus.RESERVED

    def test_create_stores_fields_correctly(self):
        """create()는 전달된 필드를 올바르게 저장한다."""
        sample1 = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        sample2 = self.sample_ctrl.create("NAND", 1.5, 0.7)
        order = self.ctrl.create(sample2.id, "고객B", 100)
        assert order.sample_id == sample2.id
        assert order.customer_name == "고객B"
        assert order.quantity == 100


class TestOrderControllerFindAll:
    """OrderController.find_all() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.ctrl = OrderController(OrderRepository(db))

    def test_find_all_empty_initially(self):
        """생성 전에는 빈 리스트를 반환한다."""
        assert self.ctrl.find_all() == []

    def test_find_all_returns_created_orders(self):
        """생성된 모든 Order를 반환한다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        self.ctrl.create(sample.id, "고객A", 50)
        self.ctrl.create(sample.id, "고객B", 100)
        result = self.ctrl.find_all()
        assert len(result) == 2


class TestOrderControllerFindById:
    """OrderController.find_by_id() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.ctrl = OrderController(OrderRepository(db))

    def test_find_by_id_returns_order_when_exists(self):
        """존재하는 ID로 조회하면 Order를 반환한다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        result = self.ctrl.find_by_id(order.id)
        assert result is not None
        assert result.id == order.id

    def test_find_by_id_returns_none_when_not_exists(self):
        """존재하지 않는 ID로 조회하면 None을 반환한다."""
        result = self.ctrl.find_by_id("9999")
        assert result is None


class TestOrderControllerFindByStatus:
    """OrderController.find_by_status() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.ctrl = OrderController(OrderRepository(db))
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        self.ctrl.create(sample.id, "고객A", 50)
        self.ctrl.create(sample.id, "고객B", 100)

    def test_find_by_status_returns_matching_orders(self):
        """해당 상태의 Order 목록을 반환한다."""
        result = self.ctrl.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 2

    def test_find_by_status_returns_empty_when_no_match(self):
        """해당 상태의 Order가 없으면 빈 리스트를 반환한다."""
        result = self.ctrl.find_by_status(OrderStatus.CONFIRMED)
        assert result == []


class TestOrderControllerUpdateStatus:
    """OrderController.update_status() 검증."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.ctrl = OrderController(OrderRepository(db))

    def test_update_status_returns_true_when_exists(self):
        """존재하는 Order 상태를 변경하면 True를 반환한다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        result = self.ctrl.update_status(order.id, OrderStatus.CONFIRMED)
        assert result is True

    def test_update_status_changes_order_status(self):
        """update_status() 후 Order 상태가 변경된다."""
        sample = self.sample_ctrl.create("DRAM", 2.0, 0.8)
        order = self.ctrl.create(sample.id, "고객A", 50)
        self.ctrl.update_status(order.id, OrderStatus.CONFIRMED)
        updated = self.ctrl.find_by_id(order.id)
        assert updated.status == OrderStatus.CONFIRMED

    def test_update_status_returns_false_when_not_exists(self):
        """존재하지 않는 ID로 update_status하면 False를 반환한다."""
        result = self.ctrl.update_status("9999", OrderStatus.CONFIRMED)
        assert result is False


# ---------------------------------------------------------------------------
# ProductionController 테스트
# ---------------------------------------------------------------------------

def _make_production_setup():
    """ProductionController 테스트용 공통 setup — FK 제약 충족을 위해 sample/order 먼저 생성."""
    from database.db_manager import DatabaseManager
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from repositories.production_job_repository import ProductionJobRepository
    from controllers.sample_controller import SampleController
    from controllers.order_controller import OrderController
    from controllers.production_controller import ProductionController
    DatabaseManager._instances = {}
    db = DatabaseManager.get_instance(":memory:")
    sample_ctrl = SampleController(SampleRepository(db))
    order_ctrl = OrderController(OrderRepository(db))
    prod_ctrl = ProductionController(ProductionJobRepository(db))
    # FK 제약 충족을 위한 기본 데이터 생성
    sample = sample_ctrl.create("DRAM", 2.0, 0.8)
    order1 = order_ctrl.create(sample.id, "고객A", 100)
    order2 = order_ctrl.create(sample.id, "고객B", 50)
    order3 = order_ctrl.create(sample.id, "고객C", 80)
    return prod_ctrl, sample.id, order1.id, order2.id, order3.id


class TestProductionControllerEnqueue:
    """ProductionController.enqueue() 검증."""

    def setup_method(self):
        result = _make_production_setup()
        self.ctrl, self.sid, self.oid1, self.oid2, self.oid3 = result

    def test_enqueue_returns_production_job(self):
        """enqueue()는 ProductionJob 인스턴스를 반환한다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        assert isinstance(job, ProductionJob)

    def test_enqueue_first_job_is_in_progress(self):
        """최초 enqueue 시 IN_PROGRESS 상태가 된다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        assert job.status == JobStatus.IN_PROGRESS

    def test_enqueue_second_job_is_waiting(self):
        """두 번째 enqueue는 WAITING 상태이다."""
        self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        job2 = self.ctrl.enqueue(self.oid2, self.sid, 50, 0.8, 2.0)
        assert job2.status == JobStatus.WAITING

    def test_enqueue_stores_order_and_sample_ids(self):
        """enqueue()는 order_id, sample_id를 올바르게 저장한다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 200, 0.9, 1.5)
        assert job.order_id == self.oid1
        assert job.sample_id == self.sid

    def test_enqueue_stores_planned_quantity(self):
        """enqueue()는 planned_quantity를 올바르게 저장한다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 150, 0.8, 2.0)
        assert job.planned_quantity == 150


class TestProductionControllerFindInProgress:
    """ProductionController.find_in_progress() 검증."""

    def setup_method(self):
        result = _make_production_setup()
        self.ctrl, self.sid, self.oid1, self.oid2, self.oid3 = result

    def test_find_in_progress_returns_none_initially(self):
        """enqueue 전에는 None을 반환한다."""
        assert self.ctrl.find_in_progress() is None

    def test_find_in_progress_returns_current_job(self):
        """enqueue 후 현재 IN_PROGRESS 작업을 반환한다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        result = self.ctrl.find_in_progress()
        assert result is not None
        assert result.job_id == job.job_id
        assert result.status == JobStatus.IN_PROGRESS


class TestProductionControllerFindWaitingQueue:
    """ProductionController.find_waiting_queue() 검증."""

    def setup_method(self):
        result = _make_production_setup()
        self.ctrl, self.sid, self.oid1, self.oid2, self.oid3 = result

    def test_find_waiting_queue_empty_initially(self):
        """enqueue 전에는 빈 리스트를 반환한다."""
        assert self.ctrl.find_waiting_queue() == []

    def test_find_waiting_queue_returns_waiting_jobs(self):
        """대기 중인 작업 목록을 반환한다."""
        self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)  # IN_PROGRESS
        self.ctrl.enqueue(self.oid2, self.sid, 50, 0.8, 2.0)   # WAITING
        self.ctrl.enqueue(self.oid3, self.sid, 80, 0.8, 2.0)   # WAITING
        result = self.ctrl.find_waiting_queue()
        assert len(result) == 2

    def test_find_waiting_queue_returns_jobs_in_queue_order(self):
        """대기 큐는 queue_order ASC 순서(FIFO)로 반환한다."""
        self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)  # IN_PROGRESS
        job_b = self.ctrl.enqueue(self.oid2, self.sid, 50, 0.8, 2.0)   # WAITING
        job_c = self.ctrl.enqueue(self.oid3, self.sid, 80, 0.8, 2.0)   # WAITING
        result = self.ctrl.find_waiting_queue()
        assert result[0].job_id == job_b.job_id
        assert result[1].job_id == job_c.job_id


class TestProductionControllerUpdateStatus:
    """ProductionController.update_status() 검증."""

    def setup_method(self):
        result = _make_production_setup()
        self.ctrl, self.sid, self.oid1, self.oid2, self.oid3 = result

    def test_update_status_to_completed_returns_true(self):
        """IN_PROGRESS 작업을 COMPLETED로 변경하면 True를 반환한다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        result = self.ctrl.update_status(job.job_id, JobStatus.COMPLETED)
        assert result is True

    def test_update_status_completed_triggers_next_job(self):
        """COMPLETED 처리 후 _try_start_next()가 호출되어 다음 WAITING 작업이 IN_PROGRESS로 전환된다."""
        job_a = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)  # IN_PROGRESS
        job_b = self.ctrl.enqueue(self.oid2, self.sid, 50, 0.8, 2.0)   # WAITING
        self.ctrl.update_status(job_a.job_id, JobStatus.COMPLETED)
        current = self.ctrl.find_in_progress()
        assert current is not None
        assert current.job_id == job_b.job_id
        assert current.status == JobStatus.IN_PROGRESS

    def test_update_status_completed_clears_current_job_when_no_waiting(self):
        """COMPLETED 처리 후 대기 큐가 비어 있으면 find_in_progress()가 None이 된다."""
        job = self.ctrl.enqueue(self.oid1, self.sid, 100, 0.8, 2.0)
        self.ctrl.update_status(job.job_id, JobStatus.COMPLETED)
        assert self.ctrl.find_in_progress() is None

    def test_update_status_returns_false_when_not_exists(self):
        """존재하지 않는 job_id로 update_status하면 False를 반환한다."""
        result = self.ctrl.update_status("9999", JobStatus.COMPLETED)
        assert result is False


class TestProductionControllerFifo:
    """ProductionController FIFO 순서 보장 테스트."""

    def test_fifo_order_a_b_c_completes_in_order(self):
        """작업 A→B→C 순서로 enqueue 후 완료 순서가 A→B→C임을 확인한다."""
        ctrl, sid, oid1, oid2, oid3 = _make_production_setup()

        job_a = ctrl.enqueue(oid1, sid, 100, 0.8, 2.0)  # IN_PROGRESS
        job_b = ctrl.enqueue(oid2, sid, 50, 0.8, 2.0)   # WAITING
        job_c = ctrl.enqueue(oid3, sid, 80, 0.8, 2.0)   # WAITING

        # A 완료 → B가 IN_PROGRESS
        ctrl.update_status(job_a.job_id, JobStatus.COMPLETED)
        assert ctrl.find_in_progress().job_id == job_b.job_id

        # B 완료 → C가 IN_PROGRESS
        ctrl.update_status(job_b.job_id, JobStatus.COMPLETED)
        assert ctrl.find_in_progress().job_id == job_c.job_id

        # C 완료 → None
        ctrl.update_status(job_c.job_id, JobStatus.COMPLETED)
        assert ctrl.find_in_progress() is None


# ---------------------------------------------------------------------------
# View 테스트 (의존성 주입 방식 — DB 기반)
# ---------------------------------------------------------------------------

class TestProductionViewSampleList:
    """ProductionView 시료 목록 출력 테스트."""

    def setup_method(self):
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from repositories.production_job_repository import ProductionJobRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        from controllers.production_controller import ProductionController
        from views.production_view import ProductionView

        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        self.sample_ctrl = SampleController(SampleRepository(db))
        self.order_ctrl = OrderController(OrderRepository(db))
        self.prod_ctrl = ProductionController(ProductionJobRepository(db))

        self.sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
        self.sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=50)

        self.output_lines = []
        self.view = ProductionView(
            self.sample_ctrl,
            self.order_ctrl,
            self.prod_ctrl,
            input_fn=lambda prompt="": "0",  # 즉시 뒤로가기
            output_fn=lambda msg="": self.output_lines.append(msg),
        )

    def test_sample_list_output_contains_sample_names(self):
        """시료 관리 진입 시 시료 목록이 자동 표시된다."""
        from views.production_view import ProductionView
        # 시료 관리(1) 진입 → 자동으로 목록 표시 → 뒤로(0) → 뒤로(0)
        inputs = iter(["1", "0", "0"])
        self.view = ProductionView(
            self.sample_ctrl,
            self.order_ctrl,
            self.prod_ctrl,
            input_fn=lambda prompt="": next(inputs),
            output_fn=lambda msg="": self.output_lines.append(str(msg)),
        )
        self.view.run()
        combined = "\n".join(self.output_lines)
        assert "DRAM" in combined
        assert "NAND" in combined


class TestProductionViewApproveWithStock:
    """ProductionView 주문 승인 (재고 충분) 테스트."""

    def test_approve_with_stock_transitions_to_confirmed(self):
        """재고 충분 시 승인하면 주문이 CONFIRMED 상태로 전환된다."""
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from repositories.production_job_repository import ProductionJobRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        from controllers.production_controller import ProductionController
        from views.production_view import ProductionView

        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        sample_ctrl = SampleController(SampleRepository(db))
        order_ctrl = OrderController(OrderRepository(db))
        prod_ctrl = ProductionController(ProductionJobRepository(db))

        sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
        order = order_ctrl.create(sample.id, "고객A", 50)

        output_lines = []
        # 메뉴: 2=주문 승인/거절 → order_id 입력 → 1=승인 → 0=뒤로 → 0=뒤로
        inputs = iter(["2", order.id, "1", "0", "0"])
        view = ProductionView(
            sample_ctrl, order_ctrl, prod_ctrl,
            input_fn=lambda prompt="": next(inputs),
            output_fn=lambda msg="": output_lines.append(str(msg)),
        )
        view.run()

        updated = order_ctrl.find_by_id(order.id)
        assert updated.status == OrderStatus.CONFIRMED


class TestProductionViewApproveWithoutStock:
    """ProductionView 주문 승인 (재고 부족) 테스트."""

    def test_approve_without_stock_transitions_to_producing_and_enqueues(self):
        """재고 부족 시 승인하면 PRODUCING으로 전환되고 생산 큐에 등록된다."""
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from repositories.production_job_repository import ProductionJobRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        from controllers.production_controller import ProductionController
        from views.production_view import ProductionView

        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        sample_ctrl = SampleController(SampleRepository(db))
        order_ctrl = OrderController(OrderRepository(db))
        prod_ctrl = ProductionController(ProductionJobRepository(db))

        sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=0)
        order = order_ctrl.create(sample.id, "고객A", 50)

        output_lines = []
        # 메뉴: 2=주문 승인/거절 → order_id → 1=승인 → 0=뒤로 → 0=뒤로
        inputs = iter(["2", order.id, "1", "0", "0"])
        view = ProductionView(
            sample_ctrl, order_ctrl, prod_ctrl,
            input_fn=lambda prompt="": next(inputs),
            output_fn=lambda msg="": output_lines.append(str(msg)),
        )
        view.run()

        updated = order_ctrl.find_by_id(order.id)
        assert updated.status == OrderStatus.PRODUCING
        current_job = prod_ctrl.find_in_progress()
        assert current_job is not None


class TestProductionViewReject:
    """ProductionView 주문 거절 테스트."""

    def test_reject_transitions_to_rejected(self):
        """거절 처리 시 RESERVED → REJECTED로 전환된다."""
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from repositories.production_job_repository import ProductionJobRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        from controllers.production_controller import ProductionController
        from views.production_view import ProductionView

        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        sample_ctrl = SampleController(SampleRepository(db))
        order_ctrl = OrderController(OrderRepository(db))
        prod_ctrl = ProductionController(ProductionJobRepository(db))

        sample = sample_ctrl.create("DRAM", 2.0, 0.8)
        order = order_ctrl.create(sample.id, "고객A", 50)

        output_lines = []
        # 메뉴: 2=주문 승인/거절 → order_id → 2=거절 → 0=뒤로 → 0=뒤로
        inputs = iter(["2", order.id, "2", "0", "0"])
        view = ProductionView(
            sample_ctrl, order_ctrl, prod_ctrl,
            input_fn=lambda prompt="": next(inputs),
            output_fn=lambda msg="": output_lines.append(str(msg)),
        )
        view.run()

        updated = order_ctrl.find_by_id(order.id)
        assert updated.status == OrderStatus.REJECTED


class TestOrderViewRelease:
    """OrderView 출고 처리 테스트."""

    def test_release_transitions_confirmed_to_release(self):
        """출고 처리 시 CONFIRMED → RELEASE로 전환된다."""
        from database.db_manager import DatabaseManager
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from repositories.production_job_repository import ProductionJobRepository
        from controllers.sample_controller import SampleController
        from controllers.order_controller import OrderController
        from controllers.production_controller import ProductionController
        from views.order_view import OrderView

        DatabaseManager._instances = {}
        db = DatabaseManager.get_instance(":memory:")
        sample_ctrl = SampleController(SampleRepository(db))
        order_ctrl = OrderController(OrderRepository(db))
        prod_ctrl = ProductionController(ProductionJobRepository(db))

        sample = sample_ctrl.create("DRAM", 2.0, 0.8)
        order = order_ctrl.create(sample.id, "고객A", 50)
        order_ctrl.update_status(order.id, OrderStatus.CONFIRMED)

        output_lines = []
        # 메뉴: 3=출고 처리 → order_id → 0=뒤로 → 0=뒤로
        inputs = iter(["3", order.id, "0", "0"])
        view = OrderView(
            sample_ctrl, order_ctrl, prod_ctrl,
            input_fn=lambda prompt="": next(inputs),
            output_fn=lambda msg="": output_lines.append(str(msg)),
        )
        view.run()

        updated = order_ctrl.find_by_id(order.id)
        assert updated.status == OrderStatus.RELEASE
