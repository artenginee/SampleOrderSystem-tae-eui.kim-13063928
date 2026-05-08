"""
OrderGenerator — 더미 Order 데이터를 DB에 생성한다.
상태 분포: CONFIRMED 30% / RESERVED 25% / PRODUCING 20% / RELEASE 15% / REJECTED 10%
DB 경로는 파라미터로 받으며 하드코딩하지 않는다.
"""
import random
from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from models.order import Order, OrderStatus

CUSTOMER_POOL = [
    "삼성전자", "SK하이닉스", "LG전자", "현대자동차", "기아자동차",
    "포스코", "한화", "롯데케미칼", "카카오", "네이버",
    "Apple Korea", "Google Korea", "Microsoft Korea", "Intel Korea", "TSMC Korea",
    "Qualcomm Korea", "NVIDIA Korea", "AMD Korea", "Micron Korea", "Western Digital Korea",
]

# 상태 분포: CONFIRMED 30% / RESERVED 25% / PRODUCING 20% / RELEASE 15% / REJECTED 10%
STATUS_WEIGHTS = [
    (OrderStatus.CONFIRMED, 0.30),
    (OrderStatus.RESERVED, 0.25),
    (OrderStatus.PRODUCING, 0.20),
    (OrderStatus.RELEASE, 0.15),
    (OrderStatus.REJECTED, 0.10),
]


class OrderGenerator:
    def generate(self, n: int = 30, db_path: str = "data/order_system.db") -> list:
        """n개의 더미 Order를 생성하고 DB에 저장한 뒤 반환한다."""
        db = DatabaseManager.get_instance(db_path)
        sample_repo = SampleRepository(db)
        order_repo = OrderRepository(db)

        samples = sample_repo.find_all()
        if not samples:
            return []

        statuses = [s for s, _ in STATUS_WEIGHTS]
        weights = [w for _, w in STATUS_WEIGHTS]

        orders = []
        for _ in range(n):
            sample = random.choice(samples)
            customer = random.choice(CUSTOMER_POOL)
            quantity = random.randint(10, 500)
            target_status = random.choices(statuses, weights=weights, k=1)[0]

            # DB에는 항상 RESERVED로 INSERT
            order = Order(
                id="",
                sample_id=sample.id,
                customer_name=customer,
                quantity=quantity,
                status=OrderStatus.RESERVED,
            )
            order = order_repo.create(order)

            # 목표 상태가 RESERVED가 아니면 업데이트
            if target_status != OrderStatus.RESERVED:
                order_repo.update_status(order.id, target_status)
                order.status = target_status

            orders.append(order)
        return orders
