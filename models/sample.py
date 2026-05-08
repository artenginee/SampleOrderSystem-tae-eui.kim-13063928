from dataclasses import dataclass
from math import ceil


@dataclass
class Sample:
    id: str
    name: str
    avg_production_time: float  # 시간 단위
    yield_rate: float           # 0.0 ~ 1.0
    stock: int = 0

    def calculate_production_quantity(self, shortage: int) -> int:
        """계획 생산량: 부족분을 유효수율(yield_rate × 0.9)로 나눠 올림.
        유효수율 0.9는 수율 불확실성 보정 버퍼 — 충분한 양품 확보를 보장한다."""
        if shortage <= 0:
            return 0
        return ceil(shortage / (self.yield_rate * 0.9))

    def calculate_total_production_time(self, shortage: int) -> float:
        """총 생산 시간 = avg_production_time × 계획 생산량."""
        return float(self.avg_production_time * self.calculate_production_quantity(shortage))
