"""
BaseRepository — 모든 Repository의 추상 기반 클래스.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """도메인 엔티티의 CRUD 추상 계약."""

    @abstractmethod
    def create(self, entity: T) -> T:
        """엔티티를 DB에 저장하고 DB 할당 ID가 반영된 인스턴스를 반환한다."""
        ...

    @abstractmethod
    def find_by_id(self, id: int) -> T | None:
        """ID로 엔티티를 조회한다. 없으면 None."""
        ...

    @abstractmethod
    def find_all(self) -> list[T]:
        """모든 엔티티를 반환한다."""
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        """엔티티를 업데이트하고 갱신된 인스턴스를 반환한다."""
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        """ID로 엔티티를 삭제한다. 삭제 성공 시 True, 대상 없으면 False."""
        ...

    @abstractmethod
    def count(self) -> int:
        """저장된 엔티티 수를 반환한다."""
        ...
