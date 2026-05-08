"""
monitor/panels/inventory_panel.py — 재고 현황 패널.
MonitorSnapshot 을 받아 시료별 재고/주문량/부족량/상태를 렌더링한다.
"""
from monitor.interfaces import MonitorSnapshot
from monitor.renderer import ljust_v


class InventoryPanel:
    def render(self, snapshot: MonitorSnapshot) -> str:
        """재고 현황 패널 문자열을 반환한다."""
        lines = ["╭─ 재고 현황 ─────────────────────────────────╮"]
        if not snapshot.sample_stock_info:
            lines.append("│  (등록된 시료 없음)                          │")
        else:
            for info in snapshot.sample_stock_info:
                status_color = {
                    "여유": "\033[32m",
                    "부족": "\033[33m",
                    "고갈": "\033[31m",
                }.get(info.status, "")
                line = (
                    f"│ {ljust_v(info.name, 16)} "
                    f"재고:{info.stock:4d} 주문:{info.total_order_qty:4d} "
                    f"부족:{info.shortage:4d} {status_color}[{info.status}]\033[0m │"
                )
                lines.append(line)
        lines.append("╰─────────────────────────────────────────────╯")
        return "\n".join(lines)
