"""
monitor/panels/production_panel.py — 생산 현황 패널.
MonitorSnapshot 을 받아 현재 생산 작업과 대기 큐를 렌더링한다.
"""
from monitor.interfaces import MonitorSnapshot
from monitor.renderer import ljust_v, status_badge


class ProductionPanel:
    def render(self, snapshot: MonitorSnapshot) -> str:
        """생산 현황 패널 문자열을 반환한다."""
        lines = ["╭─ 생산 현황 ─────────────────────────────────╮"]
        if snapshot.current_production:
            job = snapshot.current_production
            badge = status_badge(job.status.value)
            info = f"주문 {ljust_v(str(job.order_id), 6)} | 계획량 {job.planned_quantity:4d}"
            lines.append(f"│ 현재: {badge} {info} │")
        else:
            lines.append("│ 현재 생산 중인 작업 없음                     │")
        lines.append("│ 대기 큐:                                     │")
        if snapshot.production_queue:
            for job in snapshot.production_queue:
                info = f"주문 {ljust_v(str(job.order_id), 6)} | 계획량 {job.planned_quantity:4d}"
                lines.append(f"│   [{job.queue_order}] {info} │")
        else:
            lines.append("│   (대기 작업 없음)                           │")
        lines.append("╰─────────────────────────────────────────────╯")
        return "\n".join(lines)
