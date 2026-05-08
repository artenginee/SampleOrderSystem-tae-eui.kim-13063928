from interfaces.i_sample_controller import ISampleController
from interfaces.i_order_controller import IOrderController
from interfaces.i_production_controller import IProductionController
from monitor.renderer import visible_len, ljust_v, status_badge, progress_bar
from models.order import OrderStatus

W = 54  # 카드 내부 콘텐츠 너비 (Python len 기준)


class BaseView:
    """뷰 공통 기반 클래스: 카드 렌더링 + 공유 데이터 렌더러."""

    def __init__(
        self,
        sample_ctrl: ISampleController,
        order_ctrl: IOrderController,
        prod_ctrl: IProductionController,
        input_fn=input,
        output_fn=print,
    ):
        self._sample_ctrl = sample_ctrl
        self._order_ctrl = order_ctrl
        self._prod_ctrl = prod_ctrl
        self._input = input_fn
        self._output = output_fn

    # ── 카드 프리미티브 ──────────────────────────────────────────

    def _top(self, title: str = "") -> str:
        if title:
            fill = max(0, W - visible_len(title) - 1)
            return f"╭─ {title} {'─' * fill}╮"
        return f"╭{'─' * (W + 2)}╮"

    def _row(self, content: str = "") -> str:
        return f"│ {ljust_v(content, W)} │"

    def _sep(self) -> str:
        return f"├{'─' * (W + 2)}┤"

    def _bot(self) -> str:
        return f"╰{'─' * (W + 2)}╯"

    def _card(self, title: str, rows: list) -> None:
        self._output(self._top(title))
        for r in rows:
            self._output(self._row(r))
        self._output(self._bot())

    # ── 공유 데이터 렌더러 ────────────────────────────────────────

    def _sample_rows(self, samples) -> list:
        if not samples:
            return ["(등록된 시료 없음)"]
        header = f"{'ID':<5} {'이름':<18} {'재고':>5} {'수율':>5} {'시간':>5}"
        rows = [header, "─" * W]
        for s in samples:
            name = s.name[:18]
            rows.append(
                f"{s.id:<5} {name:<18} {s.stock:>5} "
                f"{s.yield_rate:>5.2f} {s.avg_production_time:>4.1f}h"
            )
        return rows

    def _order_rows(self, orders, show_status: bool = False) -> list:
        if not orders:
            return ["(주문 없음)"]
        header = f"{'ID':<6} {'고객':<14} {'시료ID':>6} {'수량':>5}"
        if show_status:
            header += "  상태"
        rows = [header, "─" * W]
        for o in orders:
            name = o.customer_name[:14]
            line = f"{o.id:<6} {name:<14} {o.sample_id:>6} {o.quantity:>5}"
            if show_status:
                line += f"  {status_badge(o.status.value)}"
            rows.append(line)
        return rows

    def _order_stats_rows(self) -> list:
        statuses = [
            OrderStatus.RESERVED, OrderStatus.CONFIRMED,
            OrderStatus.PRODUCING, OrderStatus.RELEASE, OrderStatus.REJECTED,
        ]
        counts = {s: len(self._order_ctrl.find_by_status(s)) for s in statuses}
        total = sum(counts.values())
        rows = []
        for s, cnt in counts.items():
            bar = progress_bar(cnt, total if total else 1, width=10)
            badge = ljust_v(status_badge(s.value), 22)
            rows.append(f"{badge} {bar} {cnt:3d}건")
        return rows

    def _inventory_rows(self, active_orders) -> list:
        samples = self._sample_ctrl.find_all()
        if not samples:
            return ["(등록된 시료 없음)"]
        header = f"{'이름':<18} {'재고':>5} {'주문':>5} {'부족':>5}  상태"
        rows = [header, "─" * W]
        for s in samples:
            ordered = sum(o.quantity for o in active_orders if o.sample_id == s.id)
            shortage = max(0, ordered - s.stock)
            if s.stock == 0:
                st, color = "고갈", "\033[31m"
            elif s.stock < ordered:
                st, color = "부족", "\033[33m"
            else:
                st, color = "여유", "\033[32m"
            name = s.name[:18]
            rows.append(
                f"{name:<18} {s.stock:>5} {ordered:>5} {shortage:>5}"
                f"  {color}[{st}]\033[0m"
            )
        return rows
