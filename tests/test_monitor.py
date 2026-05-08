"""
tests/test_monitor.py — Phase 6: 데이터 모니터링 도구 TDD 테스트.
모든 테스트는 :memory: SQLite 사용, DatabaseManager._instances = {} 격리.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from database.db_manager import DatabaseManager
from models.order import Order, OrderStatus
from models.production_job import ProductionJob, JobStatus


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """격리된 :memory: DatabaseManager 반환."""
    DatabaseManager._instances = {}
    manager = DatabaseManager.get_instance(":memory:")
    yield manager
    DatabaseManager._instances = {}


# ─────────────────────────────────────────────────────────────────────────────
# 1. MonitorSnapshot / IMonitorDataProvider 구조 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_monitor_snapshot_fields_exist():
    """MonitorSnapshot 이 필수 필드를 모두 갖는지 확인."""
    from monitor.interfaces import MonitorSnapshot
    from models.order import OrderStatus

    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=None,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )
    assert isinstance(snap.timestamp, datetime)
    assert isinstance(snap.order_count_by_status, dict)
    assert isinstance(snap.sample_stock_info, list)
    assert snap.current_production is None
    assert isinstance(snap.production_queue, list)
    assert isinstance(snap.orders_by_status, dict)


def test_monitor_snapshot_timestamp_is_datetime():
    """MonitorSnapshot.timestamp 타입이 datetime 이어야 한다."""
    from monitor.interfaces import MonitorSnapshot
    from models.order import OrderStatus

    snap = MonitorSnapshot(
        timestamp=datetime(2026, 5, 8, 12, 0, 0),
        order_count_by_status={},
        sample_stock_info=[],
        current_production=None,
        production_queue=[],
        orders_by_status={},
    )
    assert isinstance(snap.timestamp, datetime)


def test_db_monitor_adapter_inherits_interface():
    """DBMonitorAdapter 가 IMonitorDataProvider 를 상속하는지 확인."""
    from monitor.adapters import DBMonitorAdapter
    from monitor.interfaces import IMonitorDataProvider
    assert issubclass(DBMonitorAdapter, IMonitorDataProvider)


def test_sample_stock_info_fields():
    """SampleStockInfo 가 필수 필드를 갖는지 확인."""
    from monitor.interfaces import SampleStockInfo

    info = SampleStockInfo(
        sample_id="1",
        name="테스트 시료",
        stock=100,
        total_order_qty=50,
        shortage=0,
        status="여유",
    )
    assert info.sample_id == "1"
    assert info.name == "테스트 시료"
    assert info.stock == 100
    assert info.total_order_qty == 50
    assert info.shortage == 0
    assert info.status == "여유"


# ─────────────────────────────────────────────────────────────────────────────
# 2. DBMonitorAdapter.get_snapshot() 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_get_snapshot_empty_db_returns_zero_counts(db):
    """빈 DB 에서 get_snapshot() 은 모든 order_count_by_status 값이 0 이어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from models.order import OrderStatus

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    for status in OrderStatus:
        assert snapshot.order_count_by_status[status] == 0


def test_get_snapshot_empty_db_returns_empty_stock_info(db):
    """빈 DB 에서 get_snapshot() 의 sample_stock_info 는 빈 리스트여야 한다."""
    from monitor.adapters import DBMonitorAdapter

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.sample_stock_info == []


def test_get_snapshot_empty_db_no_current_production(db):
    """빈 DB 에서 get_snapshot() 의 current_production 은 None 이어야 한다."""
    from monitor.adapters import DBMonitorAdapter

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.current_production is None


def test_get_snapshot_empty_db_no_production_queue(db):
    """빈 DB 에서 get_snapshot() 의 production_queue 는 빈 리스트여야 한다."""
    from monitor.adapters import DBMonitorAdapter

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.production_queue == []


def test_get_snapshot_counts_orders_by_status(db):
    """주문 생성 후 get_snapshot() 이 각 상태별 주문 수를 올바르게 반환해야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)

    sample = sample_repo.create(Sample(id="", name="DRAM", avg_production_time=2.0, yield_rate=0.9, stock=100))

    # RESERVED 2개, CONFIRMED 1개 생성
    o1 = Order(id="", sample_id=sample.id, customer_name="A사", quantity=10, status=OrderStatus.RESERVED)
    o2 = Order(id="", sample_id=sample.id, customer_name="B사", quantity=20, status=OrderStatus.RESERVED)
    o3 = Order(id="", sample_id=sample.id, customer_name="C사", quantity=30, status=OrderStatus.CONFIRMED)
    order_repo.create(o1)
    order_repo.create(o2)
    order_repo.create(o3)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.order_count_by_status[OrderStatus.RESERVED] == 2
    assert snapshot.order_count_by_status[OrderStatus.CONFIRMED] == 1
    assert snapshot.order_count_by_status[OrderStatus.PRODUCING] == 0


def test_get_snapshot_sample_stock_info_content(db):
    """샘플 생성 후 get_snapshot() 의 sample_stock_info 에 올바른 재고 정보가 있어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from models.sample import Sample

    sample_repo = SampleRepository(db)
    sample = sample_repo.create(Sample(id="", name="NAND Flash", avg_production_time=3.0, yield_rate=0.85, stock=500))

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert len(snapshot.sample_stock_info) == 1
    info = snapshot.sample_stock_info[0]
    assert info.name == "NAND Flash"
    assert info.stock == 500
    assert info.total_order_qty == 0
    assert info.shortage == 0
    assert info.status == "여유"


def test_get_snapshot_sample_stock_info_shortage(db):
    """RESERVED + PRODUCING 주문이 있을 때 sample_stock_info 의 부족량이 올바르게 계산되어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)

    sample = sample_repo.create(Sample(id="", name="ARM CPU", avg_production_time=1.5, yield_rate=0.8, stock=30))

    # RESERVED 20개, PRODUCING 20개 → 총 40개 주문 vs 재고 30개 → 부족 10
    o1 = Order(id="", sample_id=sample.id, customer_name="A사", quantity=20, status=OrderStatus.RESERVED)
    o2 = Order(id="", sample_id=sample.id, customer_name="B사", quantity=20, status=OrderStatus.PRODUCING)
    order_repo.create(o1)
    order_repo.create(o2)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    info = snapshot.sample_stock_info[0]
    assert info.total_order_qty == 40
    assert info.shortage == 10
    assert info.status == "부족"


def test_get_snapshot_sample_stock_depleted(db):
    """재고가 0이고 주문이 있을 때 status 가 '고갈' 이어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)

    sample = sample_repo.create(Sample(id="", name="GPU", avg_production_time=4.0, yield_rate=0.75, stock=0))
    o = Order(id="", sample_id=sample.id, customer_name="A사", quantity=10, status=OrderStatus.RESERVED)
    order_repo.create(o)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    info = snapshot.sample_stock_info[0]
    assert info.status == "고갈"
    assert info.shortage == 10


def test_get_snapshot_current_production_in_progress(db):
    """IN_PROGRESS 생산 작업이 있을 때 current_production 에 반환되어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from repositories.production_job_repository import ProductionJobRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus
    from models.production_job import ProductionJob, JobStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)
    job_repo = ProductionJobRepository(db)

    sample = sample_repo.create(Sample(id="", name="SSD", avg_production_time=2.0, yield_rate=0.9, stock=0))
    order = order_repo.create(Order(id="", sample_id=sample.id, customer_name="A사", quantity=50, status=OrderStatus.PRODUCING))
    job = ProductionJob(
        job_id="", order_id=order.id, sample_id=sample.id,
        planned_quantity=60, actual_quantity=0, total_time_min=120.0,
        queue_order=1, status=JobStatus.IN_PROGRESS,
    )
    created_job = job_repo.create(job)

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert snapshot.current_production is not None
    assert snapshot.current_production.job_id == created_job.job_id
    assert snapshot.current_production.status == JobStatus.IN_PROGRESS


def test_get_snapshot_production_queue_waiting(db):
    """WAITING 생산 작업들이 production_queue 에 순서대로 반환되어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from repositories.production_job_repository import ProductionJobRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus
    from models.production_job import ProductionJob, JobStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)
    job_repo = ProductionJobRepository(db)

    sample = sample_repo.create(Sample(id="", name="SSD2", avg_production_time=2.0, yield_rate=0.9, stock=0))
    order1 = order_repo.create(Order(id="", sample_id=sample.id, customer_name="A사", quantity=10, status=OrderStatus.PRODUCING))
    order2 = order_repo.create(Order(id="", sample_id=sample.id, customer_name="B사", quantity=20, status=OrderStatus.PRODUCING))

    job1 = job_repo.create(ProductionJob(
        job_id="", order_id=order1.id, sample_id=sample.id,
        planned_quantity=12, actual_quantity=0, total_time_min=24.0,
        queue_order=1, status=JobStatus.WAITING,
    ))
    job2 = job_repo.create(ProductionJob(
        job_id="", order_id=order2.id, sample_id=sample.id,
        planned_quantity=23, actual_quantity=0, total_time_min=46.0,
        queue_order=2, status=JobStatus.WAITING,
    ))

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert len(snapshot.production_queue) == 2
    assert snapshot.production_queue[0].queue_order == 1
    assert snapshot.production_queue[1].queue_order == 2


def test_get_snapshot_orders_by_status(db):
    """orders_by_status 에 각 상태별 Order 리스트가 올바르게 반환되어야 한다."""
    from monitor.adapters import DBMonitorAdapter
    from repositories.sample_repository import SampleRepository
    from repositories.order_repository import OrderRepository
    from models.sample import Sample
    from models.order import Order, OrderStatus

    sample_repo = SampleRepository(db)
    order_repo = OrderRepository(db)

    sample = sample_repo.create(Sample(id="", name="Chip", avg_production_time=1.0, yield_rate=0.9, stock=100))

    o1 = order_repo.create(Order(id="", sample_id=sample.id, customer_name="A사", quantity=10, status=OrderStatus.RESERVED))
    o2 = order_repo.create(Order(id="", sample_id=sample.id, customer_name="B사", quantity=20, status=OrderStatus.CONFIRMED))
    o3 = order_repo.create(Order(id="", sample_id=sample.id, customer_name="C사", quantity=30, status=OrderStatus.CONFIRMED))

    adapter = DBMonitorAdapter(db)
    snapshot = adapter.get_snapshot()

    assert len(snapshot.orders_by_status[OrderStatus.RESERVED]) == 1
    assert len(snapshot.orders_by_status[OrderStatus.CONFIRMED]) == 2
    assert len(snapshot.orders_by_status[OrderStatus.PRODUCING]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. renderer.py 함수 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_visible_len_plain_text():
    """ANSI 코드가 없는 일반 문자열의 visible_len 은 len() 과 같아야 한다."""
    from monitor.renderer import visible_len
    assert visible_len("hello") == 5


def test_visible_len_with_ansi_codes():
    """ANSI 이스케이프 코드를 포함한 문자열의 visible_len 은 ANSI 제외 길이여야 한다."""
    from monitor.renderer import visible_len
    assert visible_len("\033[31mhello\033[0m") == 5


def test_visible_len_empty_string():
    """빈 문자열의 visible_len 은 0 이어야 한다."""
    from monitor.renderer import visible_len
    assert visible_len("") == 0


def test_visible_len_complex_ansi():
    """복잡한 ANSI 코드 포함 시에도 visible_len 이 정확해야 한다."""
    from monitor.renderer import visible_len
    # 색상 + 굵기 등 복합 코드
    assert visible_len("\033[1;32mOK\033[0m") == 2


def test_ljust_v_plain_text():
    """일반 문자열 ljust_v 는 길이 width 가 되도록 패딩되어야 한다."""
    from monitor.renderer import ljust_v, visible_len
    result = ljust_v("hi", 10)
    assert visible_len(result) == 10


def test_ljust_v_ansi_text():
    """ANSI 코드 포함 문자열 ljust_v 는 visible_len 기준 width 가 되어야 한다."""
    from monitor.renderer import ljust_v, visible_len
    result = ljust_v("\033[31mhi\033[0m", 10)
    assert visible_len(result) == 10


def test_ljust_v_no_padding_needed():
    """이미 width 이상인 문자열은 패딩 없이 그대로 반환되어야 한다."""
    from monitor.renderer import ljust_v, visible_len
    s = "hello world"  # 11자
    result = ljust_v(s, 5)
    assert result == s  # 그대로


def test_progress_bar_full():
    """progress_bar(10, 10) 은 전체가 채워진 바여야 한다."""
    from monitor.renderer import progress_bar
    bar = progress_bar(10, 10, width=10)
    assert bar == "██████████"


def test_progress_bar_empty():
    """progress_bar(0, 10) 은 전체가 빈 바여야 한다."""
    from monitor.renderer import progress_bar
    bar = progress_bar(0, 10, width=10)
    assert bar == "░░░░░░░░░░"


def test_progress_bar_zero_total():
    """total=0 일 때 progress_bar 는 빈 바여야 한다."""
    from monitor.renderer import progress_bar
    bar = progress_bar(0, 0, width=5)
    assert bar == "░░░░░"


def test_status_badge_contains_status():
    """status_badge 는 상태 이름을 포함한 문자열을 반환해야 한다."""
    from monitor.renderer import status_badge
    badge = status_badge("CONFIRMED")
    assert "CONFIRMED" in badge


# ─────────────────────────────────────────────────────────────────────────────
# 4. Dashboard 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_dashboard_depends_only_on_interface():
    """Dashboard 생성자가 IMonitorDataProvider 타입을 의존하는지 확인한다."""
    from monitor.dashboard import Dashboard
    from monitor.interfaces import IMonitorDataProvider

    mock_provider = MagicMock(spec=IMonitorDataProvider)
    mock_snapshot = MagicMock()
    mock_snapshot.timestamp = datetime.now()
    mock_snapshot.order_count_by_status = {}
    mock_snapshot.sample_stock_info = []
    mock_snapshot.current_production = None
    mock_snapshot.production_queue = []
    mock_snapshot.orders_by_status = {}
    mock_provider.get_snapshot.return_value = mock_snapshot

    dashboard = Dashboard(mock_provider, output_fn=lambda x: None)
    assert dashboard._provider is mock_provider


def test_dashboard_render_once_calls_get_snapshot_once():
    """render_once() 는 get_snapshot() 을 정확히 1번만 호출해야 한다."""
    from monitor.dashboard import Dashboard
    from monitor.interfaces import IMonitorDataProvider, MonitorSnapshot
    from models.order import OrderStatus

    mock_provider = MagicMock(spec=IMonitorDataProvider)
    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=None,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )
    mock_provider.get_snapshot.return_value = snap

    dashboard = Dashboard(mock_provider, output_fn=lambda x: None)
    dashboard.render_once()

    mock_provider.get_snapshot.assert_called_once()


def test_dashboard_all_panels_use_same_snapshot_instance():
    """render_once() 에서 모든 패널이 동일한 MonitorSnapshot 인스턴스를 받는지 확인."""
    from monitor.dashboard import Dashboard
    from monitor.interfaces import IMonitorDataProvider, MonitorSnapshot
    from models.order import OrderStatus

    received_snapshots = []

    class TrackingPanel:
        def render(self, snapshot):
            received_snapshots.append(snapshot)
            return ""

    mock_provider = MagicMock(spec=IMonitorDataProvider)
    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=None,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )
    mock_provider.get_snapshot.return_value = snap

    dashboard = Dashboard(mock_provider, output_fn=lambda x: None)
    dashboard._order_panel = TrackingPanel()
    dashboard._inventory_panel = TrackingPanel()
    dashboard._production_panel = TrackingPanel()

    dashboard.render_once()

    # 3개 패널 모두 동일한 인스턴스를 받아야 한다
    assert len(received_snapshots) == 3
    assert received_snapshots[0] is received_snapshots[1]
    assert received_snapshots[1] is received_snapshots[2]


# ─────────────────────────────────────────────────────────────────────────────
# 5. Panel 테스트
# ─────────────────────────────────────────────────────────────────────────────

def _make_snapshot():
    """테스트용 MonitorSnapshot 생성 헬퍼."""
    from monitor.interfaces import MonitorSnapshot, SampleStockInfo
    from models.order import OrderStatus
    return MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[
            SampleStockInfo(
                sample_id="1", name="DRAM", stock=100,
                total_order_qty=50, shortage=0, status="여유",
            )
        ],
        current_production=None,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )


def test_order_panel_render_returns_string():
    """OrderPanel.render() 는 문자열을 반환해야 한다."""
    from monitor.panels.order_panel import OrderPanel
    panel = OrderPanel()
    result = panel.render(_make_snapshot())
    assert isinstance(result, str)


def test_order_panel_render_contains_order_status():
    """OrderPanel.render() 결과에 주문 상태 정보가 포함되어야 한다."""
    from monitor.panels.order_panel import OrderPanel
    panel = OrderPanel()
    result = panel.render(_make_snapshot())
    # RESERVED, CONFIRMED 등 상태명이 포함되어야 함
    assert "RESERVED" in result or "CONFIRMED" in result


def test_inventory_panel_render_returns_string():
    """InventoryPanel.render() 는 문자열을 반환해야 한다."""
    from monitor.panels.inventory_panel import InventoryPanel
    panel = InventoryPanel()
    result = panel.render(_make_snapshot())
    assert isinstance(result, str)


def test_inventory_panel_render_contains_sample_name():
    """InventoryPanel.render() 결과에 시료 이름이 포함되어야 한다."""
    from monitor.panels.inventory_panel import InventoryPanel
    panel = InventoryPanel()
    result = panel.render(_make_snapshot())
    assert "DRAM" in result


def test_inventory_panel_render_empty_samples():
    """InventoryPanel.render() 는 시료 없을 때 빈 메시지를 포함해야 한다."""
    from monitor.panels.inventory_panel import InventoryPanel
    from monitor.interfaces import MonitorSnapshot
    from models.order import OrderStatus

    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=None,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )
    panel = InventoryPanel()
    result = panel.render(snap)
    assert isinstance(result, str)
    assert "없음" in result


def test_production_panel_render_returns_string():
    """ProductionPanel.render() 는 문자열을 반환해야 한다."""
    from monitor.panels.production_panel import ProductionPanel
    panel = ProductionPanel()
    result = panel.render(_make_snapshot())
    assert isinstance(result, str)


def test_production_panel_render_no_current_job():
    """현재 생산 작업이 없을 때 ProductionPanel 은 그 메시지를 포함해야 한다."""
    from monitor.panels.production_panel import ProductionPanel
    panel = ProductionPanel()
    result = panel.render(_make_snapshot())
    assert "없음" in result


def test_production_panel_render_with_current_job():
    """현재 생산 작업이 있을 때 ProductionPanel 은 해당 작업 정보를 포함해야 한다."""
    from monitor.panels.production_panel import ProductionPanel
    from monitor.interfaces import MonitorSnapshot
    from models.order import OrderStatus
    from models.production_job import ProductionJob, JobStatus

    job = ProductionJob(
        job_id="1", order_id="10", sample_id="1",
        planned_quantity=50, actual_quantity=0, total_time_min=100.0,
        queue_order=1, status=JobStatus.IN_PROGRESS,
    )
    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=job,
        production_queue=[],
        orders_by_status={s: [] for s in OrderStatus},
    )
    panel = ProductionPanel()
    result = panel.render(snap)
    assert "10" in result  # order_id 포함


def test_production_panel_render_with_queue():
    """대기 큐에 작업이 있을 때 ProductionPanel 은 그 정보를 포함해야 한다."""
    from monitor.panels.production_panel import ProductionPanel
    from monitor.interfaces import MonitorSnapshot
    from models.order import OrderStatus
    from models.production_job import ProductionJob, JobStatus

    waiting_job = ProductionJob(
        job_id="2", order_id="20", sample_id="1",
        planned_quantity=30, actual_quantity=0, total_time_min=60.0,
        queue_order=1, status=JobStatus.WAITING,
    )
    snap = MonitorSnapshot(
        timestamp=datetime.now(),
        order_count_by_status={s: 0 for s in OrderStatus},
        sample_stock_info=[],
        current_production=None,
        production_queue=[waiting_job],
        orders_by_status={s: [] for s in OrderStatus},
    )
    panel = ProductionPanel()
    result = panel.render(snap)
    assert "20" in result  # order_id 포함
