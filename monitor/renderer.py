"""
monitor/renderer.py — ANSI 콘솔 렌더링 유틸리티.
컬럼 정렬 시 반드시 visible_len() / ljust_v() 를 사용한다. len()/ljust() 직접 사용 금지.
"""
import re

ANSI_ESCAPE = re.compile(r'\033\[[0-9;]*m')


def visible_len(s: str) -> int:
    """ANSI 이스케이프 코드를 제외한 실제 표시 길이를 반환한다."""
    return len(ANSI_ESCAPE.sub('', s))


def ljust_v(s: str, width: int, fillchar: str = ' ') -> str:
    """ANSI 코드를 고려하여 visible_len 기준으로 width 만큼 오른쪽을 패딩한다."""
    pad = width - visible_len(s)
    return s + fillchar * max(0, pad)


def progress_bar(value: int, total: int, width: int = 10) -> str:
    """진행률 바를 생성한다 (████░░░░░░)."""
    if total == 0:
        filled = 0
    else:
        filled = int(width * value / total)
    return '█' * filled + '░' * (width - filled)


def status_badge(status: str) -> str:
    """상태 이름을 ANSI 컬러 배지 문자열로 반환한다."""
    colors = {
        'RESERVED': '\033[33m',    # 노랑
        'CONFIRMED': '\033[32m',   # 초록
        'PRODUCING': '\033[34m',   # 파랑
        'RELEASE': '\033[36m',     # 시안
        'REJECTED': '\033[31m',    # 빨강
        'IN_PROGRESS': '\033[34m',
        'WAITING': '\033[33m',
        'COMPLETED': '\033[32m',
    }
    color = colors.get(status, '\033[0m')
    return f"{color}[{status}]\033[0m"
