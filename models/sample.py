from dataclasses import dataclass


@dataclass
class Sample:
    id: str
    name: str
    avg_production_time: float  # 시간 단위
    yield_rate: float           # 0.0 ~ 1.0
    stock: int = 0

    def calculate_production_quantity(self, shortage: int) -> int:
        """PRD 공식: int(shortage / yield_rate * 0.9) — 절삭(floor) 적용."""
        return int(shortage / self.yield_rate * 0.9)

    def calculate_total_production_time(self, shortage: int) -> float:
        """총 생산 시간 = avg_production_time × 실 생산량."""
        return float(self.avg_production_time * self.calculate_production_quantity(shortage))
