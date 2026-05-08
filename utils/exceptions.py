class OrderSystemError(Exception):
    """시료 주문 시스템 기본 예외."""


class SampleNotFoundError(OrderSystemError):
    """시료를 찾을 수 없을 때 발생."""


class OrderNotFoundError(OrderSystemError):
    """주문을 찾을 수 없을 때 발생."""


class InvalidStatusTransitionError(OrderSystemError, ValueError):
    """유효하지 않은 상태 전이 시 발생."""
