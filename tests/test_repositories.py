"""
Phase 3: Repository 테스트
TDD RED 단계 — 실패하는 테스트를 먼저 작성한다.
모든 테스트에서 :memory: SQLite 사용. 각 테스트 시작 시 새 DB 인스턴스 생성.
"""
import pytest
from models.sample import Sample
from models.order import Order, OrderStatus
from models.production_job import ProductionJob, JobStatus


@pytest.fixture(autouse=True)
def reset_singleton():
    """각 테스트 전후 DatabaseManager 싱글톤 캐시를 초기화한다."""
    from database.db_manager import DatabaseManager
    DatabaseManager._instances = {}
    yield
    DatabaseManager._instances = {}


@pytest.fixture
def db():
    """각 테스트를 위한 새 :memory: DatabaseManager 인스턴스."""
    from database.db_manager import DatabaseManager
    return DatabaseManager.get_instance(":memory:")


@pytest.fixture
def sample_repo(db):
    """SampleRepository 인스턴스."""
    from repositories.sample_repository import SampleRepository
    return SampleRepository(db)


@pytest.fixture
def order_repo(db):
    """OrderRepository 인스턴스."""
    from repositories.order_repository import OrderRepository
    return OrderRepository(db)


@pytest.fixture
def job_repo(db):
    """ProductionJobRepository 인스턴스."""
    from repositories.production_job_repository import ProductionJobRepository
    return ProductionJobRepository(db)


@pytest.fixture
def sample_in_db(sample_repo):
    """DB에 저장된 Sample 인스턴스."""
    sample = Sample(id="", name="DRAM-DDR5", avg_production_time=2.0, yield_rate=0.8, stock=100)
    return sample_repo.create(sample)


@pytest.fixture
def order_in_db(db, sample_repo, order_repo):
    """DB에 저장된 Order 인스턴스 (참조할 Sample도 DB에 저장)."""
    sample = Sample(id="", name="DRAM-DDR5", avg_production_time=2.0, yield_rate=0.8, stock=100)
    saved_sample = sample_repo.create(sample)
    order = Order(id="", sample_id=saved_sample.id, customer_name="고객A", quantity=50)
    return order_repo.create(order)


# ---------------------------------------------------------------------------
# SampleRepository 테스트
# ---------------------------------------------------------------------------

class TestSampleRepositoryCreate:
    """SampleRepository.create() 검증."""

    def test_create_returns_sample_instance(self, sample_repo):
        """create()는 Sample 인스턴스를 반환한다."""
        sample = Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8)
        result = sample_repo.create(sample)
        assert isinstance(result, Sample)

    def test_create_assigns_db_id(self, sample_repo):
        """create()는 DB가 할당한 lastrowid를 id에 반영한다."""
        sample = Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8)
        result = sample_repo.create(sample)
        assert result.id != ""
        assert result.id == "1"

    def test_create_second_sample_has_incremented_id(self, sample_repo):
        """두 번째 create()는 증가된 id를 반환한다."""
        s1 = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        s2 = sample_repo.create(Sample(id="", name="NAND", avg_production_time=1.5, yield_rate=0.7))
        assert int(s2.id) > int(s1.id)

    def test_create_stores_fields_correctly(self, sample_repo):
        """create()는 전달된 필드를 올바르게 저장한다."""
        sample = Sample(id="", name="CPU", avg_production_time=3.0, yield_rate=0.9, stock=50)
        result = sample_repo.create(sample)
        assert result.name == "CPU"
        assert result.avg_production_time == 3.0
        assert result.yield_rate == 0.9
        assert result.stock == 50


class TestSampleRepositoryFindById:
    """SampleRepository.find_by_id() 검증."""

    def test_find_by_id_returns_sample_when_exists(self, sample_repo, sample_in_db):
        """존재하는 ID로 조회하면 Sample을 반환한다."""
        result = sample_repo.find_by_id(int(sample_in_db.id))
        assert result is not None
        assert result.id == sample_in_db.id

    def test_find_by_id_returns_none_when_not_exists(self, sample_repo):
        """존재하지 않는 ID로 조회하면 None을 반환한다."""
        result = sample_repo.find_by_id(9999)
        assert result is None

    def test_find_by_id_returns_correct_fields(self, sample_repo, sample_in_db):
        """find_by_id()는 올바른 필드 값을 반환한다."""
        result = sample_repo.find_by_id(int(sample_in_db.id))
        assert result.name == "DRAM-DDR5"
        assert result.avg_production_time == 2.0
        assert result.yield_rate == 0.8
        assert result.stock == 100


class TestSampleRepositoryFindAll:
    """SampleRepository.find_all() 검증."""

    def test_find_all_returns_empty_list_initially(self, sample_repo):
        """DB가 비어 있으면 빈 리스트를 반환한다."""
        result = sample_repo.find_all()
        assert result == []

    def test_find_all_returns_all_samples(self, sample_repo):
        """생성된 모든 Sample을 반환한다."""
        sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        sample_repo.create(Sample(id="", name="NAND", avg_production_time=1.5, yield_rate=0.7))
        result = sample_repo.find_all()
        assert len(result) == 2

    def test_find_all_returns_sample_instances(self, sample_repo):
        """find_all()은 Sample 인스턴스 목록을 반환한다."""
        sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        result = sample_repo.find_all()
        assert all(isinstance(s, Sample) for s in result)


class TestSampleRepositoryUpdate:
    """SampleRepository.update() 검증."""

    def test_update_returns_updated_sample(self, sample_repo, sample_in_db):
        """update()는 업데이트된 Sample을 반환한다."""
        sample_in_db.name = "DRAM-Updated"
        sample_in_db.avg_production_time = 3.0
        result = sample_repo.update(sample_in_db)
        assert isinstance(result, Sample)
        assert result.name == "DRAM-Updated"

    def test_update_persists_changes(self, sample_repo, sample_in_db):
        """update() 후 find_by_id()로 변경된 값을 확인한다."""
        sample_in_db.stock = 200
        sample_repo.update(sample_in_db)
        found = sample_repo.find_by_id(int(sample_in_db.id))
        assert found.stock == 200


class TestSampleRepositoryDelete:
    """SampleRepository.delete() 검증."""

    def test_delete_returns_true_when_exists(self, sample_repo, sample_in_db):
        """존재하는 Sample을 삭제하면 True를 반환한다."""
        result = sample_repo.delete(int(sample_in_db.id))
        assert result is True

    def test_delete_removes_from_db(self, sample_repo, sample_in_db):
        """delete() 후 find_by_id()는 None을 반환한다."""
        sample_id = int(sample_in_db.id)
        sample_repo.delete(sample_id)
        assert sample_repo.find_by_id(sample_id) is None

    def test_delete_returns_false_when_not_exists(self, sample_repo):
        """존재하지 않는 ID로 delete하면 False를 반환한다."""
        result = sample_repo.delete(9999)
        assert result is False


class TestSampleRepositoryCount:
    """SampleRepository.count() 검증."""

    def test_count_returns_zero_initially(self, sample_repo):
        """DB가 비어 있으면 0을 반환한다."""
        assert sample_repo.count() == 0

    def test_count_returns_number_of_samples(self, sample_repo):
        """생성된 Sample 수를 반환한다."""
        sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        sample_repo.create(Sample(id="", name="NAND", avg_production_time=1.5, yield_rate=0.7))
        assert sample_repo.count() == 2


class TestSampleRepositoryFindByName:
    """SampleRepository.find_by_name() 검증."""

    def setup_method(self):
        pass

    def test_find_by_name_returns_matching_samples(self, sample_repo):
        """키워드가 포함된 Sample 목록을 반환한다."""
        sample_repo.create(Sample(id="", name="DRAM-DDR5", avg_production_time=2.0, yield_rate=0.8))
        sample_repo.create(Sample(id="", name="NAND Flash", avg_production_time=1.5, yield_rate=0.7))
        result = sample_repo.find_by_name("DRAM")
        assert len(result) == 1
        assert result[0].name == "DRAM-DDR5"

    def test_find_by_name_returns_multiple_matches(self, sample_repo):
        """여러 개가 일치하면 모두 반환한다."""
        sample_repo.create(Sample(id="", name="DRAM-DDR5", avg_production_time=2.0, yield_rate=0.8))
        sample_repo.create(Sample(id="", name="DRAM-DDR4", avg_production_time=1.8, yield_rate=0.75))
        result = sample_repo.find_by_name("DRAM")
        assert len(result) == 2

    def test_find_by_name_returns_empty_when_no_match(self, sample_repo):
        """일치하는 항목이 없으면 빈 리스트를 반환한다."""
        result = sample_repo.find_by_name("XYZ")
        assert result == []


class TestSampleRepositoryUpdateStock:
    """SampleRepository.update_stock() 검증."""

    def test_update_stock_increases_stock_by_delta(self, sample_repo, sample_in_db):
        """양수 delta로 재고가 증가한다."""
        sample_repo.update_stock(int(sample_in_db.id), 50)
        found = sample_repo.find_by_id(int(sample_in_db.id))
        assert found.stock == 150  # 100 + 50

    def test_update_stock_decreases_stock_by_delta(self, sample_repo, sample_in_db):
        """음수 delta로 재고가 감소한다."""
        sample_repo.update_stock(int(sample_in_db.id), -30)
        found = sample_repo.find_by_id(int(sample_in_db.id))
        assert found.stock == 70  # 100 - 30

    def test_update_stock_returns_true_when_exists(self, sample_repo, sample_in_db):
        """존재하는 Sample의 재고를 변경하면 True를 반환한다."""
        result = sample_repo.update_stock(int(sample_in_db.id), 10)
        assert result is True

    def test_update_stock_returns_false_when_not_exists(self, sample_repo):
        """존재하지 않는 ID로 update_stock하면 False를 반환한다."""
        result = sample_repo.update_stock(9999, 10)
        assert result is False


# ---------------------------------------------------------------------------
# OrderRepository 테스트
# ---------------------------------------------------------------------------

class TestOrderRepositoryCreate:
    """OrderRepository.create() 검증."""

    def test_create_returns_order_instance(self, sample_repo, order_repo):
        """create()는 Order 인스턴스를 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order = Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50)
        result = order_repo.create(order)
        assert isinstance(result, Order)

    def test_create_assigns_db_id(self, sample_repo, order_repo):
        """create()는 DB가 할당한 lastrowid를 id에 반영한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order = Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50)
        result = order_repo.create(order)
        assert result.id == "1"

    def test_create_initial_status_is_reserved(self, sample_repo, order_repo):
        """생성된 Order의 초기 상태는 RESERVED이어야 한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order = Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50)
        result = order_repo.create(order)
        assert result.status == OrderStatus.RESERVED

    def test_create_stores_fields_correctly(self, sample_repo, order_repo):
        """create()는 전달된 필드를 올바르게 저장한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order = Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100)
        result = order_repo.create(order)
        assert result.customer_name == "고객B"
        assert result.quantity == 100
        assert result.sample_id == sample.id


class TestOrderRepositoryFindById:
    """OrderRepository.find_by_id() 검증."""

    def test_find_by_id_returns_order_when_exists(self, order_repo, order_in_db):
        """존재하는 ID로 조회하면 Order를 반환한다."""
        result = order_repo.find_by_id(int(order_in_db.id))
        assert result is not None
        assert result.id == order_in_db.id

    def test_find_by_id_returns_none_when_not_exists(self, order_repo):
        """존재하지 않는 ID로 조회하면 None을 반환한다."""
        result = order_repo.find_by_id(9999)
        assert result is None


class TestOrderRepositoryFindAll:
    """OrderRepository.find_all() 검증."""

    def test_find_all_returns_empty_list_initially(self, order_repo):
        """DB가 비어 있으면 빈 리스트를 반환한다."""
        assert order_repo.find_all() == []

    def test_find_all_returns_all_orders(self, sample_repo, order_repo):
        """생성된 모든 Order를 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100))
        result = order_repo.find_all()
        assert len(result) == 2


class TestOrderRepositoryUpdate:
    """OrderRepository.update() 검증."""

    def test_update_persists_changes(self, order_repo, order_in_db):
        """update() 후 변경된 값이 DB에 저장된다."""
        order_in_db.quantity = 200
        order_repo.update(order_in_db)
        found = order_repo.find_by_id(int(order_in_db.id))
        assert found.quantity == 200


class TestOrderRepositoryDelete:
    """OrderRepository.delete() 검증."""

    def test_delete_returns_true_when_exists(self, order_repo, order_in_db):
        """존재하는 Order를 삭제하면 True를 반환한다."""
        result = order_repo.delete(int(order_in_db.id))
        assert result is True

    def test_delete_removes_from_db(self, order_repo, order_in_db):
        """delete() 후 find_by_id()는 None을 반환한다."""
        order_id = int(order_in_db.id)
        order_repo.delete(order_id)
        assert order_repo.find_by_id(order_id) is None

    def test_delete_returns_false_when_not_exists(self, order_repo):
        """존재하지 않는 ID로 delete하면 False를 반환한다."""
        result = order_repo.delete(9999)
        assert result is False


class TestOrderRepositoryCount:
    """OrderRepository.count() 검증."""

    def test_count_returns_zero_initially(self, order_repo):
        """DB가 비어 있으면 0을 반환한다."""
        assert order_repo.count() == 0

    def test_count_returns_number_of_orders(self, sample_repo, order_repo):
        """생성된 Order 수를 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100))
        assert order_repo.count() == 2


class TestOrderRepositoryFindByStatus:
    """OrderRepository.find_by_status() 검증."""

    def test_find_by_status_returns_matching_orders(self, sample_repo, order_repo):
        """해당 상태의 Order 목록을 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100))
        result = order_repo.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 2

    def test_find_by_status_returns_empty_when_no_match(self, order_repo):
        """해당 상태의 Order가 없으면 빈 리스트를 반환한다."""
        result = order_repo.find_by_status(OrderStatus.CONFIRMED)
        assert result == []


class TestOrderRepositoryFindBySample:
    """OrderRepository.find_by_sample() 검증."""

    def test_find_by_sample_returns_matching_orders(self, sample_repo, order_repo):
        """해당 sample_id의 Order 목록을 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100))
        result = order_repo.find_by_sample(sample.id)
        assert len(result) == 2

    def test_find_by_sample_returns_empty_when_no_match(self, order_repo):
        """해당 sample_id의 Order가 없으면 빈 리스트를 반환한다."""
        result = order_repo.find_by_sample("9999")
        assert result == []


class TestOrderRepositoryUpdateStatus:
    """OrderRepository.update_status() 검증."""

    def test_update_status_returns_true_when_exists(self, order_repo, order_in_db):
        """존재하는 Order 상태를 변경하면 True를 반환한다."""
        result = order_repo.update_status(order_in_db.id, OrderStatus.CONFIRMED)
        assert result is True

    def test_update_status_changes_order_status(self, order_repo, order_in_db):
        """update_status() 후 Order 상태가 변경된다."""
        order_repo.update_status(order_in_db.id, OrderStatus.CONFIRMED)
        found = order_repo.find_by_id(int(order_in_db.id))
        assert found.status == OrderStatus.CONFIRMED

    def test_update_status_returns_false_when_not_exists(self, order_repo):
        """존재하지 않는 ID로 update_status하면 False를 반환한다."""
        result = order_repo.update_status("9999", OrderStatus.CONFIRMED)
        assert result is False


class TestOrderRepositoryCountByStatus:
    """OrderRepository.count_by_status() 검증."""

    def test_count_by_status_returns_correct_count(self, sample_repo, order_repo):
        """해당 상태의 Order 수를 반환한다."""
        sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
        order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객B", quantity=100))
        assert order_repo.count_by_status(OrderStatus.RESERVED) == 2

    def test_count_by_status_returns_zero_when_no_match(self, order_repo):
        """해당 상태의 Order가 없으면 0을 반환한다."""
        assert order_repo.count_by_status(OrderStatus.CONFIRMED) == 0


# ---------------------------------------------------------------------------
# ProductionJobRepository 테스트
# ---------------------------------------------------------------------------

@pytest.fixture
def job_setup(db, sample_repo, order_repo):
    """ProductionJob 테스트를 위한 Sample과 Order를 DB에 미리 저장."""
    sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.8))
    order = order_repo.create(Order(id="", sample_id=sample.id, customer_name="고객A", quantity=50))
    return sample, order


@pytest.fixture
def job_in_db(job_repo, job_setup):
    """DB에 저장된 ProductionJob 인스턴스."""
    sample, order = job_setup
    job = ProductionJob(
        job_id="",
        order_id=order.id,
        sample_id=sample.id,
        planned_quantity=100,
        actual_quantity=0,
        total_time_min=5.0,
        queue_order=1,
    )
    return job_repo.create(job)


class TestProductionJobRepositoryCreate:
    """ProductionJobRepository.create() 검증."""

    def test_create_returns_production_job_instance(self, job_repo, job_setup):
        """create()는 ProductionJob 인스턴스를 반환한다."""
        sample, order = job_setup
        job = ProductionJob(
            job_id="",
            order_id=order.id,
            sample_id=sample.id,
            planned_quantity=100,
            actual_quantity=0,
            total_time_min=5.0,
            queue_order=1,
        )
        result = job_repo.create(job)
        assert isinstance(result, ProductionJob)

    def test_create_assigns_db_id(self, job_repo, job_setup):
        """create()는 DB가 할당한 lastrowid를 job_id에 반영한다."""
        sample, order = job_setup
        job = ProductionJob(
            job_id="",
            order_id=order.id,
            sample_id=sample.id,
            planned_quantity=100,
            actual_quantity=0,
            total_time_min=5.0,
            queue_order=1,
        )
        result = job_repo.create(job)
        assert result.job_id == "1"

    def test_create_stores_fields_correctly(self, job_repo, job_setup):
        """create()는 전달된 필드를 올바르게 저장한다."""
        sample, order = job_setup
        job = ProductionJob(
            job_id="",
            order_id=order.id,
            sample_id=sample.id,
            planned_quantity=150,
            actual_quantity=0,
            total_time_min=7.5,
            queue_order=2,
        )
        result = job_repo.create(job)
        assert result.planned_quantity == 150
        assert result.total_time_min == 7.5
        assert result.queue_order == 2


class TestProductionJobRepositoryFindById:
    """ProductionJobRepository.find_by_id() 검증."""

    def test_find_by_id_returns_job_when_exists(self, job_repo, job_in_db):
        """존재하는 ID로 조회하면 ProductionJob을 반환한다."""
        result = job_repo.find_by_id(int(job_in_db.job_id))
        assert result is not None
        assert result.job_id == job_in_db.job_id

    def test_find_by_id_returns_none_when_not_exists(self, job_repo):
        """존재하지 않는 ID로 조회하면 None을 반환한다."""
        result = job_repo.find_by_id(9999)
        assert result is None


class TestProductionJobRepositoryFindAll:
    """ProductionJobRepository.find_all() 검증."""

    def test_find_all_returns_empty_list_initially(self, job_repo):
        """DB가 비어 있으면 빈 리스트를 반환한다."""
        assert job_repo.find_all() == []

    def test_find_all_returns_all_jobs(self, job_repo, job_setup):
        """생성된 모든 ProductionJob을 반환한다."""
        sample, order = job_setup
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=100, actual_quantity=0, total_time_min=5.0, queue_order=1))
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=50, actual_quantity=0, total_time_min=2.5, queue_order=2))
        result = job_repo.find_all()
        assert len(result) == 2


class TestProductionJobRepositoryUpdate:
    """ProductionJobRepository.update() 검증."""

    def test_update_persists_changes(self, job_repo, job_in_db):
        """update() 후 변경된 값이 DB에 저장된다."""
        job_in_db.actual_quantity = 80
        job_repo.update(job_in_db)
        found = job_repo.find_by_id(int(job_in_db.job_id))
        assert found.actual_quantity == 80


class TestProductionJobRepositoryDelete:
    """ProductionJobRepository.delete() 검증."""

    def test_delete_returns_true_when_exists(self, job_repo, job_in_db):
        """존재하는 ProductionJob을 삭제하면 True를 반환한다."""
        result = job_repo.delete(int(job_in_db.job_id))
        assert result is True

    def test_delete_returns_false_when_not_exists(self, job_repo):
        """존재하지 않는 ID로 delete하면 False를 반환한다."""
        result = job_repo.delete(9999)
        assert result is False


class TestProductionJobRepositoryCount:
    """ProductionJobRepository.count() 검증."""

    def test_count_returns_zero_initially(self, job_repo):
        """DB가 비어 있으면 0을 반환한다."""
        assert job_repo.count() == 0

    def test_count_returns_number_of_jobs(self, job_repo, job_setup):
        """생성된 ProductionJob 수를 반환한다."""
        sample, order = job_setup
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=100, actual_quantity=0, total_time_min=5.0, queue_order=1))
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=50, actual_quantity=0, total_time_min=2.5, queue_order=2))
        assert job_repo.count() == 2


class TestProductionJobRepositoryFindWaitingQueue:
    """ProductionJobRepository.find_waiting_queue() 검증."""

    def test_find_waiting_queue_returns_waiting_jobs_in_order(self, job_repo, job_setup):
        """WAITING 상태의 작업을 queue_order ASC 순서로 반환한다."""
        sample, order = job_setup
        job1 = job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                              planned_quantity=100, actual_quantity=0,
                                              total_time_min=5.0, queue_order=2, status=JobStatus.WAITING))
        job2 = job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                              planned_quantity=50, actual_quantity=0,
                                              total_time_min=2.5, queue_order=1, status=JobStatus.WAITING))
        result = job_repo.find_waiting_queue()
        assert len(result) == 2
        assert result[0].job_id == job2.job_id  # queue_order=1이 먼저
        assert result[1].job_id == job1.job_id  # queue_order=2가 나중

    def test_find_waiting_queue_excludes_non_waiting(self, job_repo, job_setup):
        """IN_PROGRESS 및 COMPLETED 작업은 제외된다."""
        sample, order = job_setup
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=100, actual_quantity=0,
                                      total_time_min=5.0, queue_order=1, status=JobStatus.IN_PROGRESS))
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                      planned_quantity=50, actual_quantity=0,
                                      total_time_min=2.5, queue_order=2, status=JobStatus.WAITING))
        result = job_repo.find_waiting_queue()
        assert len(result) == 1
        assert result[0].status == JobStatus.WAITING


class TestProductionJobRepositoryFindInProgress:
    """ProductionJobRepository.find_in_progress() 검증."""

    def test_find_in_progress_returns_in_progress_job(self, job_repo, job_setup):
        """IN_PROGRESS 상태의 작업을 반환한다."""
        sample, order = job_setup
        job = job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                             planned_quantity=100, actual_quantity=0,
                                             total_time_min=5.0, queue_order=1, status=JobStatus.IN_PROGRESS))
        result = job_repo.find_in_progress()
        assert result is not None
        assert result.job_id == job.job_id

    def test_find_in_progress_returns_none_when_none_in_progress(self, job_repo, job_setup):
        """IN_PROGRESS 상태의 작업이 없으면 None을 반환한다."""
        sample, order = job_setup
        job_repo.create(ProductionJob(job_id="", order_id=order.id, sample_id=sample.id,
                                       planned_quantity=100, actual_quantity=0,
                                       total_time_min=5.0, queue_order=1, status=JobStatus.WAITING))
        result = job_repo.find_in_progress()
        assert result is None


class TestProductionJobRepositoryUpdateStatus:
    """ProductionJobRepository.update_status() 검증."""

    def test_update_status_returns_true_when_exists(self, job_repo, job_in_db):
        """존재하는 job의 상태를 변경하면 True를 반환한다."""
        result = job_repo.update_status(job_in_db.job_id, JobStatus.IN_PROGRESS)
        assert result is True

    def test_update_status_changes_job_status(self, job_repo, job_in_db):
        """update_status() 후 job 상태가 변경된다."""
        job_repo.update_status(job_in_db.job_id, JobStatus.IN_PROGRESS)
        found = job_repo.find_by_id(int(job_in_db.job_id))
        assert found.status == JobStatus.IN_PROGRESS

    def test_update_status_returns_false_when_not_exists(self, job_repo):
        """존재하지 않는 job_id로 update_status하면 False를 반환한다."""
        result = job_repo.update_status("9999", JobStatus.COMPLETED)
        assert result is False


class TestProductionJobRepositoryUpdateActualQuantity:
    """ProductionJobRepository.update_actual_quantity() 검증."""

    def test_update_actual_quantity_returns_true_when_exists(self, job_repo, job_in_db):
        """존재하는 job의 실제 생산량을 변경하면 True를 반환한다."""
        result = job_repo.update_actual_quantity(job_in_db.job_id, 90)
        assert result is True

    def test_update_actual_quantity_changes_value(self, job_repo, job_in_db):
        """update_actual_quantity() 후 actual_quantity가 변경된다."""
        job_repo.update_actual_quantity(job_in_db.job_id, 90)
        found = job_repo.find_by_id(int(job_in_db.job_id))
        assert found.actual_quantity == 90

    def test_update_actual_quantity_returns_false_when_not_exists(self, job_repo):
        """존재하지 않는 job_id로 update_actual_quantity하면 False를 반환한다."""
        result = job_repo.update_actual_quantity("9999", 50)
        assert result is False
