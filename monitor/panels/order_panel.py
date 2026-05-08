"""
monitor/panels/order_panel.py — 주문 현황 패널.
MonitorSnapshot 을 받아 상태별 주문 수와 진행률 바를 렌더링한다.
"""
from models.order import OrderStatus
from monitor.interfaces import MonitorSnapshot
from monitor.renderer import ljust_v, progress_bar, status_badge


class OrderPanel:
    def render(self, snapshot: MonitorSnapshot) -> str:
        """주문 현황 패널 문자열을 반환한다."""
        lines = ["╭─ 주문 현황 ─────────────────────────────────╮"]
        total = sum(snapshot.order_count_by_status.values())
        for status in [
            OrderStatus.RESERVED,
            OrderStatus.CONFIRMED,
            OrderStatus.PRODUCING,
            OrderStatus.RELEASE,
            OrderStatus.REJECTED,
        ]:
            count = snapshot.order_count_by_status.get(status, 0)
            bar = progress_bar(count, total if total > 0 else 1, width=8)
            badge = status_badge(status.value)
            line = f"│ {ljust_v(badge, 20)} {bar} {count:3d}건 │"
            lines.append(line)
        lines.append("╰─────────────────────────────────────────────╯")
        return "\n".join(lines)
