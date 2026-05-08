"""
tests/test_e2e.py — Phase 7 E2E 통합 시나리오 테스트.

mock 없이 실제 DB(`:memory:` SQLite), Repository, Controller, Monitor 모두 실제 구현체 사용.
각 픽스처에서 `DatabaseManager._instances = {}`로 싱글톤을 초기화하여 테스트 간 격리.
"""
import pytest
from datetime import datetime

from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_job_repository import ProductionJobRepository
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from monitor.adapters import DBMonitorAdapter
from models.order import OrderStatus
from models.production_job import JobStatus


@pytest.fixture
def setup():
    """각 테스트마다 새 :memory: DB를 생성하여 테스트 간 완전 격리."""
    DatabaseManager._instances = {}
    db = DatabaseManager.get_instance(":memory:")
    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)
    job_repo = ProductionJobRepository(db)
    sample_ctrl = SampleController(sample_repo)
    order_ctrl = OrderController(order_repo)
    prod_ctrl = ProductionController(job_repo)
    yield db, sample_ctrl, order_ctrl, prod_ctrl
    DatabaseManager._instances = {}


# ---------------------------------------------------------------------------
# 시나리오 1: 재고 충분 흐름
# 시료 등록(재고 100) → 주문(수량 50) → 승인(재고 충분) → CONFIRMED → 출고 → RELEASE
# ---------------------------------------------------------------------------

def test_scenario1_sufficient_stock_registers_sample(setup):
    """시나리오1: 시료 등록 후 find_all로 1개 반환되는지 확인한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    samples = sample_ctrl.find_all()
    assert len(samples) == 1
    assert samples[0].name == "DRAM"
    assert samples[0].stock == 100


def test_scenario1_order_initial_status_is_reserved(setup):
    """시나리오1: 주문 생성 직후 초기 상태가 RESERVED인지 확인한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    order = order_ctrl.create(sample.id, "고객A", 50)
    assert order.status == OrderStatus.RESERVED


def test_scenario1_approve_with_sufficient_stock_becomes_confirmed(setup):
    """시나리오1: 재고 충분 시 approve(has_stock=True) → CONFIRMED 상태가 된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    order = order_ctrl.create(sample.id, "고객A", 50)

    # 재고(100) >= 주문량(50) → 재고 충분
    assert sample.stock >= order.quantity
    order.approve(has_stock=True)
    order_ctrl.update_status(order.id, OrderStatus.CONFIRMED)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.CONFIRMED


def test_scenario1_release_after_confirmed_becomes_release(setup):
    """시나리오1: CONFIRMED 상태에서 release() → RELEASE 상태가 된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    order = order_ctrl.create(sample.id, "고객A", 50)

    order.approve(has_stock=True)
    order_ctrl.update_status(order.id, OrderStatus.CONFIRMED)

    order.release()
    order_ctrl.update_status(order.id, OrderStatus.RELEASE)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.RELEASE


def test_scenario1_find_by_name_returns_sample(setup):
    """시나리오1: find_by_name("DRAM")으로 시료를 검색하면 해당 시료가 반환된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample_ctrl.create("DRAM-DDR5", 2.0, 0.8, initial_stock=100)
    sample_ctrl.create("NAND Flash", 1.5, 0.7, initial_stock=50)

    results = sample_ctrl.find_by_name("DRAM")
    assert len(results) == 1
    assert "DRAM" in results[0].name


# ---------------------------------------------------------------------------
# 시나리오 2: 재고 부족·생산 완료 흐름
# 시료 등록(재고 0) → 주문(수량 50) → 승인(재고 부족) → PRODUCING + 큐 등록
# → 생산 완료 → CONFIRMED → 출고 → RELEASE
# ---------------------------------------------------------------------------

def test_scenario2_approve_with_no_stock_becomes_producing(setup):
    """시나리오2: 재고 0일 때 approve(has_stock=False) → PRODUCING 상태가 된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)
    order = order_ctrl.create(sample.id, "고객B", 50)

    order.approve(has_stock=False)
    order_ctrl.update_status(order.id, OrderStatus.PRODUCING)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.PRODUCING


def test_scenario2_calculate_production_quantity(setup):
    """시나리오2: shortage=50, yield_rate=0.7 → calculate_production_quantity 결과 검증."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)

    shortage = max(0, 50 - sample.stock)  # 50 - 0 = 50
    planned_qty = sample.calculate_production_quantity(shortage)
    # int(50 / 0.7 * 0.9) = int(64.28...) = 64
    assert planned_qty == int(50 / 0.7 * 0.9)


def test_scenario2_enqueue_creates_in_progress_job(setup):
    """시나리오2: enqueue 호출 시 첫 번째 작업이 IN_PROGRESS로 등록된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)
    order = order_ctrl.create(sample.id, "고객B", 50)

    order.approve(has_stock=False)
    order_ctrl.update_status(order.id, OrderStatus.PRODUCING)

    shortage = max(0, 50 - 0)
    planned_qty = sample.calculate_production_quantity(shortage)

    job = prod_ctrl.enqueue(order.id, sample.id, planned_qty, sample.yield_rate, sample.avg_production_time)
    assert job.status == JobStatus.IN_PROGRESS

    in_progress = prod_ctrl.find_in_progress()
    assert in_progress is not None
    assert in_progress.job_id == job.job_id


def test_scenario2_complete_production_then_confirmed_then_release(setup):
    """시나리오2: 생산 완료 → CONFIRMED → 출고 → RELEASE 전체 흐름을 검증한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)
    order = order_ctrl.create(sample.id, "고객B", 50)

    order.approve(has_stock=False)
    order_ctrl.update_status(order.id, OrderStatus.PRODUCING)

    shortage = max(0, 50 - 0)
    planned_qty = sample.calculate_production_quantity(shortage)
    job = prod_ctrl.enqueue(order.id, sample.id, planned_qty, sample.yield_rate, sample.avg_production_time)

    # 생산 완료
    prod_ctrl.update_status(job.job_id, JobStatus.COMPLETED)

    # 주문을 CONFIRMED으로 전이
    order.complete_production()
    order_ctrl.update_status(order.id, OrderStatus.CONFIRMED)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.CONFIRMED

    # 출고
    order.release()
    order_ctrl.update_status(order.id, OrderStatus.RELEASE)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.RELEASE


# ---------------------------------------------------------------------------
# 시나리오 3: 주문 거절 흐름
# 시료 등록 → 주문(RESERVED) → 거절 → REJECTED
# ---------------------------------------------------------------------------

def test_scenario3_reject_order_becomes_rejected(setup):
    """시나리오3: reject() 호출 후 OrderController.update_status(REJECTED) → DB에서 REJECTED 확인."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("ARM CPU", 3.0, 0.85, initial_stock=20)
    order = order_ctrl.create(sample.id, "고객C", 30)

    assert order.status == OrderStatus.RESERVED

    order.reject()
    order_ctrl.update_status(order.id, OrderStatus.REJECTED)

    fetched = order_ctrl.find_by_id(order.id)
    assert fetched.status == OrderStatus.REJECTED


def test_scenario3_reject_twice_raises_value_error(setup):
    """시나리오3: 이미 REJECTED 상태에서 reject() 재호출 시 ValueError가 발생한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("ARM CPU", 3.0, 0.85, initial_stock=20)
    order = order_ctrl.create(sample.id, "고객C", 30)

    order.reject()
    order_ctrl.update_status(order.id, OrderStatus.REJECTED)

    # DB에서 새로 조회한 Order는 REJECTED 상태여야 함
    fetched = order_ctrl.find_by_id(order.id)
    with pytest.raises(ValueError):
        fetched.reject()


# ---------------------------------------------------------------------------
# 시나리오 4: FIFO 생산 큐 흐름
# 주문A → enqueue → IN_PROGRESS
# 주문B → enqueue → WAITING
# A 완료 → _try_start_next() 자동 → B가 IN_PROGRESS
# B 완료 → find_in_progress() → None
# ---------------------------------------------------------------------------

def test_scenario4_first_job_is_in_progress_second_is_waiting(setup):
    """시나리오4: 첫 번째 enqueue는 IN_PROGRESS, 두 번째는 WAITING으로 등록된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=0)

    order_a = order_ctrl.create(sample.id, "고객A", 30)
    order_a.approve(has_stock=False)
    order_ctrl.update_status(order_a.id, OrderStatus.PRODUCING)
    job_a = prod_ctrl.enqueue(order_a.id, sample.id, 40, sample.yield_rate, sample.avg_production_time)

    order_b = order_ctrl.create(sample.id, "고객B", 20)
    order_b.approve(has_stock=False)
    order_ctrl.update_status(order_b.id, OrderStatus.PRODUCING)
    job_b = prod_ctrl.enqueue(order_b.id, sample.id, 28, sample.yield_rate, sample.avg_production_time)

    assert job_a.status == JobStatus.IN_PROGRESS
    assert job_b.status == JobStatus.WAITING


def test_scenario4_waiting_queue_contains_second_job(setup):
    """시나리오4: find_waiting_queue()가 두 번째 작업(B)을 포함해 반환한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=0)

    order_a = order_ctrl.create(sample.id, "고객A", 30)
    order_a.approve(has_stock=False)
    order_ctrl.update_status(order_a.id, OrderStatus.PRODUCING)
    job_a = prod_ctrl.enqueue(order_a.id, sample.id, 40, sample.yield_rate, sample.avg_production_time)

    order_b = order_ctrl.create(sample.id, "고객B", 20)
    order_b.approve(has_stock=False)
    order_ctrl.update_status(order_b.id, OrderStatus.PRODUCING)
    job_b = prod_ctrl.enqueue(order_b.id, sample.id, 28, sample.yield_rate, sample.avg_production_time)

    waiting = prod_ctrl.find_waiting_queue()
    assert len(waiting) == 1
    assert waiting[0].job_id == job_b.job_id


def test_scenario4_complete_job_a_starts_job_b(setup):
    """시나리오4: A 완료 처리 시 _try_start_next()가 자동 호출되어 B가 IN_PROGRESS가 된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=0)

    order_a = order_ctrl.create(sample.id, "고객A", 30)
    order_a.approve(has_stock=False)
    order_ctrl.update_status(order_a.id, OrderStatus.PRODUCING)
    job_a = prod_ctrl.enqueue(order_a.id, sample.id, 40, sample.yield_rate, sample.avg_production_time)

    order_b = order_ctrl.create(sample.id, "고객B", 20)
    order_b.approve(has_stock=False)
    order_ctrl.update_status(order_b.id, OrderStatus.PRODUCING)
    job_b = prod_ctrl.enqueue(order_b.id, sample.id, 28, sample.yield_rate, sample.avg_production_time)

    # A 완료 → _try_start_next() 자동 실행
    prod_ctrl.update_status(job_a.job_id, JobStatus.COMPLETED)

    in_progress = prod_ctrl.find_in_progress()
    assert in_progress is not None
    assert in_progress.job_id == job_b.job_id


def test_scenario4_complete_job_b_queue_becomes_empty(setup):
    """시나리오4: B까지 완료 후 find_in_progress()가 None을 반환한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=0)

    order_a = order_ctrl.create(sample.id, "고객A", 30)
    order_a.approve(has_stock=False)
    order_ctrl.update_status(order_a.id, OrderStatus.PRODUCING)
    job_a = prod_ctrl.enqueue(order_a.id, sample.id, 40, sample.yield_rate, sample.avg_production_time)

    order_b = order_ctrl.create(sample.id, "고객B", 20)
    order_b.approve(has_stock=False)
    order_ctrl.update_status(order_b.id, OrderStatus.PRODUCING)
    job_b = prod_ctrl.enqueue(order_b.id, sample.id, 28, sample.yield_rate, sample.avg_production_time)

    prod_ctrl.update_status(job_a.job_id, JobStatus.COMPLETED)
    prod_ctrl.update_status(job_b.job_id, JobStatus.COMPLETED)

    assert prod_ctrl.find_in_progress() is None
    assert prod_ctrl.find_waiting_queue() == []


# ---------------------------------------------------------------------------
# 시나리오 5: 더미 데이터 → 모니터 조회
# Repository로 직접 데이터 삽입 후 DBMonitorAdapter.get_snapshot() 검증
# ---------------------------------------------------------------------------

def test_scenario5_monitor_snapshot_order_count_matches(setup):
    """시나리오5: 주문 2건 생성 후 snapshot.order_count_by_status 합계가 2와 일치한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    s1 = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    s2 = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)
    order_ctrl.create(s1.id, "고객A", 50)
    order_ctrl.create(s2.id, "고객B", 30)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    total = sum(snapshot.order_count_by_status.values())
    assert total == 2


def test_scenario5_monitor_snapshot_sample_stock_info_count(setup):
    """시나리오5: 시료 2개 생성 후 snapshot.sample_stock_info 길이가 2와 일치한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert len(snapshot.sample_stock_info) == 2


def test_scenario5_monitor_snapshot_all_reserved_status(setup):
    """시나리오5: 생성된 주문 2건이 모두 RESERVED 상태로 집계된다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    s1 = sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)
    s2 = sample_ctrl.create("NAND", 1.5, 0.7, initial_stock=0)
    order_ctrl.create(s1.id, "고객A", 50)
    order_ctrl.create(s2.id, "고객B", 30)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.order_count_by_status[OrderStatus.RESERVED] == 2


def test_scenario5_monitor_snapshot_timestamp_is_datetime(setup):
    """시나리오5: snapshot.timestamp가 datetime 타입인지 확인한다."""
    db, sample_ctrl, order_ctrl, prod_ctrl = setup
    sample_ctrl.create("DRAM", 2.0, 0.8, initial_stock=100)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert isinstance(snapshot.timestamp, datetime)
