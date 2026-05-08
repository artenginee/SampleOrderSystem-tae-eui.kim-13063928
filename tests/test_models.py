"""
Phase 1: 도메인 모델 테스트
TDD RED 단계 — 실패하는 테스트를 먼저 작성한다.
"""
import pytest
from models.sample import Sample
from models.order import Order, OrderStatus
from models.production_job import ProductionJob, JobStatus


# ---------------------------------------------------------------------------
# Sample 테스트
# ---------------------------------------------------------------------------

class TestSampleCalculateProductionQuantity:
    """calculate_production_quantity(shortage) 검증."""

    def test_calculate_production_quantity_covers_shortage(self):
        """계획 생산량 × 유효수율(yield×0.9) ≥ shortage 를 보장한다 (올림 적용)."""
        from math import ceil
        sample = Sample(id="S001", name="DRAM", avg_production_time=2.0, yield_rate=0.8, stock=0)
        shortage = 100
        expected = ceil(shortage / (sample.yield_rate * 0.9))  # = 139
        assert sample.calculate_production_quantity(shortage) == expected

    def test_calculate_production_quantity_ceil_applied(self):
        """소수 결과는 올림(ceil)하여 부족분을 반드시 충족한다."""
        from math import ceil
        sample = Sample(id="S002", name="NAND", avg_production_time=1.5, yield_rate=0.7, stock=0)
        shortage = 50
        expected = ceil(shortage / (sample.yield_rate * 0.9))
        assert sample.calculate_production_quantity(shortage) == expected

    def test_calculate_production_quantity_shortage_zero_returns_zero(self):
        """shortage=0 경계값: 생산량은 0이어야 한다."""
        sample = Sample(id="S003", name="CPU", avg_production_time=3.0, yield_rate=0.9, stock=100)
        assert sample.calculate_production_quantity(0) == 0

    def test_calculate_production_quantity_returns_int_type(self):
        """반환 타입이 int인지 확인."""
        sample = Sample(id="S004", name="GPU", avg_production_time=1.0, yield_rate=0.85, stock=0)
        result = sample.calculate_production_quantity(30)
        assert isinstance(result, int)


class TestSampleCalculateTotalProductionTime:
    """calculate_total_production_time(shortage) 검증."""

    def test_calculate_total_production_time_equals_time_times_quantity(self):
        """총 생산 시간 = avg_production_time × calculate_production_quantity(shortage)."""
        sample = Sample(id="S001", name="DRAM", avg_production_time=2.0, yield_rate=0.8, stock=0)
        shortage = 100
        expected_qty = sample.calculate_production_quantity(shortage)
        expected_time = sample.avg_production_time * expected_qty
        assert sample.calculate_total_production_time(shortage) == expected_time

    def test_calculate_total_production_time_shortage_zero_returns_zero(self):
        """shortage=0 경계값: 총 생산 시간은 0이어야 한다."""
        sample = Sample(id="S002", name="NAND", avg_production_time=1.5, yield_rate=0.7, stock=0)
        assert sample.calculate_total_production_time(0) == 0.0

    def test_calculate_total_production_time_returns_float(self):
        """반환 타입이 float인지 확인."""
        sample = Sample(id="S003", name="CPU", avg_production_time=3.0, yield_rate=0.9, stock=0)
        result = sample.calculate_total_production_time(50)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# Order 상태 전이 테스트
# ---------------------------------------------------------------------------

class TestOrderApprove:
    """approve(has_stock) 상태 전이 검증."""

    def test_approve_with_stock_transitions_to_confirmed(self):
        """재고 충분(has_stock=True): RESERVED → CONFIRMED."""
        order = Order(id="O1", sample_id="S001", customer_name="고객A", quantity=10)
        order.approve(has_stock=True)
        assert order.status == OrderStatus.CONFIRMED

    def test_approve_without_stock_transitions_to_producing(self):
        """재고 부족(has_stock=False): RESERVED → PRODUCING."""
        order = Order(id="O2", sample_id="S001", customer_name="고객B", quantity=100)
        order.approve(has_stock=False)
        assert order.status == OrderStatus.PRODUCING

    def test_approve_raises_value_error_when_not_reserved(self):
        """비RESERVED 상태에서 approve 호출 시 ValueError가 발생한다."""
        order = Order(id="O3", sample_id="S001", customer_name="고객C", quantity=10,
                      status=OrderStatus.CONFIRMED)
        with pytest.raises(ValueError):
            order.approve(has_stock=True)

    def test_approve_raises_value_error_when_rejected(self):
        """REJECTED 상태에서 approve 호출 시 ValueError가 발생한다."""
        order = Order(id="O4", sample_id="S001", customer_name="고객D", quantity=10,
                      status=OrderStatus.REJECTED)
        with pytest.raises(ValueError):
            order.approve(has_stock=True)

    def test_approve_raises_value_error_when_producing(self):
        """PRODUCING 상태에서 approve 호출 시 ValueError가 발생한다."""
        order = Order(id="O5", sample_id="S001", customer_name="고객E", quantity=10,
                      status=OrderStatus.PRODUCING)
        with pytest.raises(ValueError):
            order.approve(has_stock=False)


class TestOrderReject:
    """reject() 상태 전이 검증."""

    def test_reject_transitions_reserved_to_rejected(self):
        """RESERVED → REJECTED."""
        order = Order(id="O1", sample_id="S001", customer_name="고객A", quantity=10)
        order.reject()
        assert order.status == OrderStatus.REJECTED

    def test_reject_raises_value_error_when_not_reserved(self):
        """비RESERVED 상태에서 reject 호출 시 ValueError가 발생한다."""
        order = Order(id="O2", sample_id="S001", customer_name="고객B", quantity=10,
                      status=OrderStatus.CONFIRMED)
        with pytest.raises(ValueError):
            order.reject()

    def test_reject_raises_value_error_when_producing(self):
        """PRODUCING 상태에서 reject 호출 시 ValueError가 발생한다."""
        order = Order(id="O3", sample_id="S001", customer_name="고객C", quantity=10,
                      status=OrderStatus.PRODUCING)
        with pytest.raises(ValueError):
            order.reject()


class TestOrderCompleteProduction:
    """complete_production() 상태 전이 검증."""

    def test_complete_production_transitions_producing_to_confirmed(self):
        """PRODUCING → CONFIRMED."""
        order = Order(id="O1", sample_id="S001", customer_name="고객A", quantity=10,
                      status=OrderStatus.PRODUCING)
        order.complete_production()
        assert order.status == OrderStatus.CONFIRMED

    def test_complete_production_raises_value_error_when_not_producing(self):
        """비PRODUCING 상태에서 complete_production 호출 시 ValueError가 발생한다."""
        order = Order(id="O2", sample_id="S001", customer_name="고객B", quantity=10,
                      status=OrderStatus.RESERVED)
        with pytest.raises(ValueError):
            order.complete_production()

    def test_complete_production_raises_value_error_when_confirmed(self):
        """CONFIRMED 상태에서 complete_production 호출 시 ValueError가 발생한다."""
        order = Order(id="O3", sample_id="S001", customer_name="고객C", quantity=10,
                      status=OrderStatus.CONFIRMED)
        with pytest.raises(ValueError):
            order.complete_production()


class TestOrderRelease:
    """release() 상태 전이 검증."""

    def test_release_transitions_confirmed_to_release(self):
        """CONFIRMED → RELEASE."""
        order = Order(id="O1", sample_id="S001", customer_name="고객A", quantity=10,
                      status=OrderStatus.CONFIRMED)
        order.release()
        assert order.status == OrderStatus.RELEASE

    def test_release_raises_value_error_when_not_confirmed(self):
        """비CONFIRMED 상태에서 release 호출 시 ValueError가 발생한다."""
        order = Order(id="O2", sample_id="S001", customer_name="고객B", quantity=10,
                      status=OrderStatus.RESERVED)
        with pytest.raises(ValueError):
            order.release()

    def test_release_raises_value_error_when_producing(self):
        """PRODUCING 상태에서 release 호출 시 ValueError가 발생한다."""
        order = Order(id="O3", sample_id="S001", customer_name="고객C", quantity=10,
                      status=OrderStatus.PRODUCING)
        with pytest.raises(ValueError):
            order.release()


# ---------------------------------------------------------------------------
# ProductionJob 기본 필드 테스트
# ---------------------------------------------------------------------------

class TestProductionJobDefaults:
    """ProductionJob 기본 필드값 검증."""

    def test_production_job_default_status_is_waiting(self):
        """기본 status는 WAITING이어야 한다."""
        job = ProductionJob(
            job_id="J001",
            order_id="O1",
            sample_id="S001",
            planned_quantity=100,
            actual_quantity=0,
            total_time_min=5.0,
        )
        assert job.status == JobStatus.WAITING

    def test_production_job_default_queue_order_is_zero(self):
        """기본 queue_order는 0이어야 한다."""
        job = ProductionJob(
            job_id="J001",
            order_id="O1",
            sample_id="S001",
            planned_quantity=100,
            actual_quantity=0,
            total_time_min=5.0,
        )
        assert job.queue_order == 0

    def test_production_job_enqueued_at_is_datetime(self):
        """enqueued_at 필드는 datetime 타입이어야 한다."""
        from datetime import datetime
        job = ProductionJob(
            job_id="J001",
            order_id="O1",
            sample_id="S001",
            planned_quantity=100,
            actual_quantity=0,
            total_time_min=5.0,
        )
        assert isinstance(job.enqueued_at, datetime)

    def test_production_job_fields_are_stored_correctly(self):
        """생성자에 전달된 필드가 올바르게 저장된다."""
        job = ProductionJob(
            job_id="J999",
            order_id="O42",
            sample_id="S007",
            planned_quantity=200,
            actual_quantity=150,
            total_time_min=10.5,
            queue_order=3,
            status=JobStatus.IN_PROGRESS,
        )
        assert job.job_id == "J999"
        assert job.order_id == "O42"
        assert job.sample_id == "S007"
        assert job.planned_quantity == 200
        assert job.actual_quantity == 150
        assert job.total_time_min == 10.5
        assert job.queue_order == 3
        assert job.status == JobStatus.IN_PROGRESS


class TestJobStatusEnum:
    """JobStatus Enum 값 검증."""

    def test_job_status_waiting_value(self):
        """WAITING 값이 'WAITING' 문자열인지 확인."""
        assert JobStatus.WAITING.value == "WAITING"

    def test_job_status_in_progress_value(self):
        """IN_PROGRESS 값이 'IN_PROGRESS' 문자열인지 확인."""
        assert JobStatus.IN_PROGRESS.value == "IN_PROGRESS"

    def test_job_status_completed_value(self):
        """COMPLETED 값이 'COMPLETED' 문자열인지 확인."""
        assert JobStatus.COMPLETED.value == "COMPLETED"

    def test_job_status_has_three_members(self):
        """JobStatus는 정확히 3개의 멤버를 가진다."""
        assert len(JobStatus) == 3


class TestOrderStatusEnum:
    """OrderStatus Enum 값 검증."""

    def test_order_status_reserved_value(self):
        assert OrderStatus.RESERVED.value == "RESERVED"

    def test_order_status_rejected_value(self):
        assert OrderStatus.REJECTED.value == "REJECTED"

    def test_order_status_producing_value(self):
        assert OrderStatus.PRODUCING.value == "PRODUCING"

    def test_order_status_confirmed_value(self):
        assert OrderStatus.CONFIRMED.value == "CONFIRMED"

    def test_order_status_release_value(self):
        assert OrderStatus.RELEASE.value == "RELEASE"
