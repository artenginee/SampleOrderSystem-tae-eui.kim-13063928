"""
SampleGenerator — 20개 반도체 프리셋을 사용해 더미 Sample 데이터를 DB에 생성한다.
생산량 공식은 POC4 기준: ceil(shortage / (yield_rate * 0.9))
DB 경로는 파라미터로 받으며 하드코딩하지 않는다.
"""
import random
from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from models.sample import Sample

# 20개 반도체 프리셋 (이름, avg_production_time, base_yield_rate)
SAMPLE_PRESETS = [
    ("DRAM-DDR5", 2.5, 0.85),
    ("DRAM-DDR4", 2.0, 0.88),
    ("NAND Flash-TLC", 1.8, 0.82),
    ("NAND Flash-MLC", 2.0, 0.87),
    ("NAND Flash-SLC", 2.2, 0.90),
    ("ARM Cortex-A78", 3.5, 0.75),
    ("ARM Cortex-M4", 2.8, 0.80),
    ("x86 Core i9", 4.0, 0.70),
    ("x86 Core i5", 3.5, 0.74),
    ("GPU RTX 4090", 5.0, 0.65),
    ("GPU RTX 3080", 4.5, 0.68),
    ("LPDDR5", 2.2, 0.86),
    ("UFS 4.0", 1.5, 0.91),
    ("eMMC 5.1", 1.2, 0.93),
    ("PCIe Gen5 SSD", 3.0, 0.78),
    ("HBM3", 6.0, 0.60),
    ("CXL Memory", 5.5, 0.62),
    ("eSIM Chip", 1.0, 0.95),
    ("TPU v4", 7.0, 0.55),
    ("Neural Engine", 4.2, 0.72),
]


class SampleGenerator:
    def generate(self, n: int = 10, db_path: str = "data/order_system.db") -> list:
        """n개의 더미 Sample을 생성하고 DB에 저장한 뒤 반환한다."""
        db = DatabaseManager.get_instance(db_path)
        repo = SampleRepository(db)

        # 프리셋 중 n개 선택 (n이 프리셋 수를 초과하면 중복 허용)
        presets = random.sample(SAMPLE_PRESETS, min(n, len(SAMPLE_PRESETS)))
        if n > len(SAMPLE_PRESETS):
            presets = presets + random.choices(SAMPLE_PRESETS, k=n - len(SAMPLE_PRESETS))

        samples = []
        for name, avg_time, base_yield in presets:
            yield_rate = round(
                max(0.5, min(1.0, base_yield + random.uniform(-0.03, 0.03))), 4
            )
            sample = Sample(
                id="",
                name=name,
                avg_production_time=avg_time,
                yield_rate=yield_rate,
                stock=random.randint(0, 200),
            )
            samples.append(repo.create(sample))
        return samples
