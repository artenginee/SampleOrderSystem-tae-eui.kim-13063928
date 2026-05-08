"""
conftest.py — pytest 루트 설정.
프로젝트 루트를 sys.path에 추가해 모든 패키지를 임포트 가능하게 한다.
Windows 환경에서 UTF-8 출력과 ANSI Virtual Terminal을 활성화한다.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# UTF-8 강제 (Windows 콘솔 기본 인코딩 대응)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def enable_ansi() -> None:
    """Windows Virtual Terminal Processing 활성화 (ANSI 이스케이프 코드 지원)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


enable_ansi()
