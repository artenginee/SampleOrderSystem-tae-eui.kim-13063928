"""
Phase 5: 더미 데이터 생성 도구 테스트
모든 테스트에서 :memory: SQLite 사용. DatabaseManager._instances = {} 로 격리.
"""
import pytest
from math import ceil
from database.db_manager import DatabaseManager
from models.order import OrderStatus
from models.production_job import JobStatus


def reset_db():
    """테스트 격리를 위해 싱글톤 인스턴스를 초기화한다."""
    DatabaseManager._instances = {}


# ===========================================================================
# SampleGenerator 테스트
# ===========================================================================

class TestSampleGeneratorCount:
    def setup_method(self):
        reset_db()

    def test_generate_returns_n_samples(self):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        samples = gen.generate(n=5, db_path=":memory:")
        assert len(samples) == 5

    def test_generate_returns_ten_samples_by_default(self):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        samples = gen.generate(n=10, db_path=":memory:")
        assert len(samples) == 10


class TestSampleGeneratorFieldValidation:
    def setup_method(self):
        reset_db()

    def test_yield_rate_is_within_zero_to_one(self):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        samples = gen.generate(n=10, db_path=":memory:")
        for s in samples:
            assert 0.0 <= s.yield_rate <= 1.0, f"yield_rate {s.yield_rate} out of range"

    def test_name_is_not_empty(self):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        samples = gen.generate(n=5, db_path=":memory:")
        for s in samples:
            assert s.name != "", f"Sample name should not be empty"

    def test_yield_rate_is_within_preset_tolerance(self):
        """yield_rate는 프리셋 기준값 ±0.03 범위 내여야 한다."""
        from generators.sample_generator import SampleGenerator, SAMPLE_PRESETS
        gen = SampleGenerator()
        samples = gen.generate(n=len(SAMPLE_PRESETS), db_path=":memory:")
        # 생성된 샘플 이름으로 프리셋 매핑
        preset_map = {name: base_yield for name, _, base_yield in SAMPLE_PRESETS}
        for s in samples:
            if s.name in preset_map:
                base = preset_map[s.name]
                assert abs(s.yield_rate - base) <= 0.03 + 1e-9, \
                    f"{s.name}: yield_rate={s.yield_rate}, base={base}, diff={abs(s.yield_rate - base)}"


class TestSampleGeneratorPersistence:
    def setup_method(self):
        reset_db()

    def test_generated_samples_are_saved_to_db(self):
        """생성된 Sample이 DB에 저장되어 있는지 SampleRepository.find_all() 결과 수로 확인한다."""
        from generators.sample_generator import SampleGenerator
        from repositories.sample_repository import SampleRepository
        gen = SampleGenerator()
        gen.generate(n=5, db_path=":memory:")
        db = DatabaseManager.get_instance(":memory:")
        repo = SampleRepository(db)
        saved = repo.find_all()
        assert len(saved) == 5


# ===========================================================================
# OrderGenerator 테스트
# ===========================================================================

class TestOrderGeneratorCount:
    def setup_method(self):
        reset_db()

    def _setup_samples(self, db_path=":memory:", n=5):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        return gen.generate(n=n, db_path=db_path)

    def test_generate_returns_n_orders(self):
        from generators.order_generator import OrderGenerator
        self._setup_samples(db_path=":memory:")
        gen = OrderGenerator()
        orders = gen.generate(n=10, db_path=":memory:")
        assert len(orders) == 10

    def test_generate_returns_empty_when_no_samples(self):
        """샘플이 없으면 빈 리스트를 반환한다."""
        from generators.order_generator import OrderGenerator
        gen = OrderGenerator()
        orders = gen.generate(n=5, db_path=":memory:")
        assert orders == []


class TestOrderGeneratorStatusDistribution:
    def setup_method(self):
        reset_db()

    def _setup_samples(self, db_path=":memory:", n=5):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        return gen.generate(n=n, db_path=db_path)

    def test_order_status_is_valid_orderStatus(self):
        from generators.order_generator import OrderGenerator
        self._setup_samples()
        gen = OrderGenerator()
        orders = gen.generate(n=10, db_path=":memory:")
        valid_statuses = set(OrderStatus)
        for o in orders:
            assert o.status in valid_statuses, f"Invalid status: {o.status}"

    def test_status_distribution_is_approximately_correct_with_large_n(self):
        """n=100으로 상태 분포가 대략 기대값에 가까운지 확인한다 (±15% 허용)."""
        from generators.order_generator import OrderGenerator
        self._setup_samples(n=10)
        gen = OrderGenerator()
        orders = gen.generate(n=100, db_path=":memory:")
        total = len(orders)
        counts = {s: 0 for s in OrderStatus}
        for o in orders:
            counts[o.status] += 1
        # 기대 분포: CONFIRMED 30%, RESERVED 25%, PRODUCING 20%, RELEASE 15%, REJECTED 10%
        expected = {
            OrderStatus.CONFIRMED: 0.30,
            OrderStatus.RESERVED: 0.25,
            OrderStatus.PRODUCING: 0.20,
            OrderStatus.RELEASE: 0.15,
            OrderStatus.REJECTED: 0.10,
        }
        for status, expected_ratio in expected.items():
            actual_ratio = counts[status] / total
            assert abs(actual_ratio - expected_ratio) < 0.15, \
                f"{status}: expected ~{expected_ratio:.0%}, got {actual_ratio:.0%}"


class TestOrderGeneratorFieldValidation:
    def setup_method(self):
        reset_db()

    def _setup_samples(self, db_path=":memory:", n=5):
        from generators.sample_generator import SampleGenerator
        gen = SampleGenerator()
        return gen.generate(n=n, db_path=db_path)

    def test_customer_name_is_not_empty(self):
        from generators.order_generator import OrderGenerator
        self._setup_samples()
        gen = OrderGenerator()
        orders = gen.generate(n=10, db_path=":memory:")
        for o in orders:
            assert o.customer_name != "", "customer_name should not be empty"

    def test_quantity_is_at_least_one(self):
        from generators.order_generator import OrderGenerator
        self._setup_samples()
        gen = OrderGenerator()
        orders = gen.generate(n=10, db_path=":memory:")
        for o in orders:
            assert o.quantity >= 1, f"quantity={o.quantity} should be >= 1"


# ===========================================================================
# ProductionGenerator 테스트
# ===========================================================================

class TestProductionGeneratorNoProducingOrders:
    def setup_method(self):
        reset_db()

    def test_generate_returns_empty_when_no_producing_orders(self):
        """PRODUCING 주문이 없으면 0개 반환한다."""
        from generators.production_generator import ProductionGenerator
        gen = ProductionGenerator()
        jobs = gen.generate(db_path=":memory:")
        assert jobs == []


class TestProductionGeneratorWithProducingOrder:
    def setup_method(self):
        reset_db()

    def _create_sample_and_producing_order(self, db_path=":memory:", quantity=100, stock=50):
        """테스트용 Sample + PRODUCING 상태 Order를 DB에 직접 생성한다."""
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from models.sample import Sample
        from models.order import Order, OrderStatus
        db = DatabaseManager.get_instance(db_path)
        sample_repo = SampleRepository(db)
        order_repo = OrderRepository(db)
        sample = Sample(id="", name="TestSample", avg_production_time=2.0,
                        yield_rate=0.8, stock=stock)
        sample = sample_repo.create(sample)
        order = Order(id="", sample_id=sample.id, customer_name="테스트고객",
                      quantity=quantity, status=OrderStatus.PRODUCING)
        order = order_repo.create(order)
        return sample, order

    def test_generate_creates_one_job_for_one_producing_order(self):
        from generators.production_generator import ProductionGenerator
        self._create_sample_and_producing_order(quantity=100, stock=50)
        gen = ProductionGenerator()
        jobs = gen.generate(db_path=":memory:")
        assert len(jobs) == 1

    def test_planned_quantity_formula_ceil_shortage_over_yield_rate_times_0_9(self):
        """공식: ceil(shortage / (yield_rate * 0.9))
        shortage=100, yield_rate=0.8 → ceil(100 / (0.8 * 0.9)) = ceil(138.88...) = 139
        """
        from generators.production_generator import ProductionGenerator
        # quantity=150, stock=50 → shortage=100
        self._create_sample_and_producing_order(quantity=150, stock=50)
        gen = ProductionGenerator()
        jobs = gen.generate(db_path=":memory:")
        assert len(jobs) == 1
        # ceil(100 / (0.8 * 0.9)) = ceil(138.888...) = 139
        assert jobs[0].planned_quantity == 139

    def test_planned_quantity_formula_specific_values(self):
        """구체적인 숫자로 단언: shortage=100, yield_rate=0.8 → planned_qty=139."""
        shortage = 100
        yield_rate = 0.8
        expected = ceil(shortage / (yield_rate * 0.9))
        assert expected == 139

    def test_job_status_first_is_in_progress(self):
        """첫 번째 PRODUCING 주문의 Job 상태는 IN_PROGRESS여야 한다."""
        from generators.production_generator import ProductionGenerator
        self._create_sample_and_producing_order(quantity=100, stock=50)
        gen = ProductionGenerator()
        jobs = gen.generate(db_path=":memory:")
        assert jobs[0].status == JobStatus.IN_PROGRESS

    def test_multiple_producing_orders_second_job_is_waiting(self):
        """두 번째 PRODUCING 주문의 Job 상태는 WAITING이어야 한다."""
        from generators.production_generator import ProductionGenerator
        from repositories.sample_repository import SampleRepository
        from repositories.order_repository import OrderRepository
        from models.sample import Sample
        from models.order import Order, OrderStatus
        db = DatabaseManager.get_instance(":memory:")
        sample_repo = SampleRepository(db)
        order_repo = OrderRepository(db)
        sample = Sample(id="", name="TestSample2", avg_production_time=2.0,
                        yield_rate=0.8, stock=10)
        sample = sample_repo.create(sample)
        for i in range(2):
            order = Order(id="", sample_id=sample.id, customer_name=f"고객{i}",
                          quantity=100, status=OrderStatus.PRODUCING)
            order_repo.create(order)
        gen = ProductionGenerator()
        jobs = gen.generate(db_path=":memory:")
        assert len(jobs) == 2
        assert jobs[0].status == JobStatus.IN_PROGRESS
        assert jobs[1].status == JobStatus.WAITING

    def test_jobs_are_persisted_to_db(self):
        """생성된 ProductionJob이 DB에 저장되어 있는지 확인한다."""
        from generators.production_generator import ProductionGenerator
        from repositories.production_job_repository import ProductionJobRepository
        self._create_sample_and_producing_order(quantity=100, stock=50)
        gen = ProductionGenerator()
        gen.generate(db_path=":memory:")
        db = DatabaseManager.get_instance(":memory:")
        job_repo = ProductionJobRepository(db)
        saved = job_repo.find_all()
        assert len(saved) == 1
