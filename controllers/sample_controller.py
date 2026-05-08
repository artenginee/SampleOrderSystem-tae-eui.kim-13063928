from interfaces.i_sample_controller import ISampleController
from models.sample import Sample


class SampleController(ISampleController):
    def __init__(self):
        self._samples: list = []
        self._counter: int = 0

    def create(self, name: str, avg_production_time: float, yield_rate: float, initial_stock: int = 0) -> Sample:
        self._counter += 1
        sample_id = f"S{self._counter:03d}"
        sample = Sample(
            id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=initial_stock,
        )
        self._samples.append(sample)
        return sample

    def find_all(self) -> list:
        return list(self._samples)

    def find_by_id(self, sample_id: str):
        for s in self._samples:
            if s.id == sample_id:
                return s
        return None

    def find_by_name(self, keyword: str) -> list:
        keyword_lower = keyword.lower()
        return [s for s in self._samples if keyword_lower in s.name.lower()]

    def update(self, sample_id: str, name: str, avg_production_time: float, yield_rate: float) -> bool:
        sample = self.find_by_id(sample_id)
        if sample is None:
            return False
        sample.name = name
        sample.avg_production_time = avg_production_time
        sample.yield_rate = yield_rate
        return True

    def delete(self, sample_id: str) -> bool:
        sample = self.find_by_id(sample_id)
        if sample is None:
            return False
        self._samples.remove(sample)
        return True

    def update_stock(self, sample_id: str, delta: int) -> bool:
        sample = self.find_by_id(sample_id)
        if sample is None:
            return False
        sample.stock += delta
        return True
