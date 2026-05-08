from interfaces.i_sample_controller import ISampleController
from repositories.sample_repository import SampleRepository


class SampleController(ISampleController):
    def __init__(self, repo: SampleRepository):
        self._repo = repo

    def create(self, name: str, avg_production_time: float, yield_rate: float, initial_stock: int = 0):
        from models.sample import Sample
        sample = Sample(
            id="",
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=initial_stock,
        )
        return self._repo.create(sample)

    def find_all(self) -> list:
        return self._repo.find_all()

    def find_by_id(self, sample_id: str):
        return self._repo.find_by_id(sample_id)

    def find_by_name(self, keyword: str) -> list:
        return self._repo.find_by_name(keyword)

    def update(self, sample_id: str, name: str, avg_production_time: float, yield_rate: float) -> bool:
        sample = self._repo.find_by_id(sample_id)
        if sample is None:
            return False
        sample.name = name
        sample.avg_production_time = avg_production_time
        sample.yield_rate = yield_rate
        self._repo.update(sample)
        return True

    def delete(self, sample_id: str) -> bool:
        return self._repo.delete(sample_id)

    def update_stock(self, sample_id: str, delta: int) -> bool:
        return self._repo.update_stock(sample_id, delta)
