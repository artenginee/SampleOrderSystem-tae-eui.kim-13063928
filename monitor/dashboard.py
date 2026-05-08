"""
monitor/dashboard.py — 모니터링 대시보드 이벤트 루프.
IMonitorDataProvider 에만 의존. DB/Repository 를 직접 참조하지 않는다.
render_once() 에서 get_snapshot() 을 한 번만 호출하여 모든 패널이 동일 인스턴스를 공유한다.
"""
import time

from monitor.interfaces import IMonitorDataProvider
from monitor.panels.inventory_panel import InventoryPanel
from monitor.panels.order_panel import OrderPanel
from monitor.panels.production_panel import ProductionPanel


class Dashboard:
    """실시간 콘솔 대시보드."""

    def __init__(
        self,
        provider: IMonitorDataProvider,
        interval: float = 5.0,
        output_fn=print,
    ):
        self._provider = provider
        self._interval = interval
        self._output = output_fn
        self._order_panel = OrderPanel()
        self._inventory_panel = InventoryPanel()
        self._production_panel = ProductionPanel()
        self._mode = "ALL"  # ALL / ORDER / INVENTORY / PRODUCTION

    def render_once(self) -> None:
        """스냅샷을 한 번 조회하고 모든 패널을 렌더링한다. 동일 인스턴스 공유."""
        snapshot = self._provider.get_snapshot()
        self._output(f"[{snapshot.timestamp.strftime('%H:%M:%S')}] 갱신 | 모드: {self._mode}")
        if self._mode in ("ALL", "ORDER"):
            self._output(self._order_panel.render(snapshot))
        if self._mode in ("ALL", "INVENTORY"):
            self._output(self._inventory_panel.render(snapshot))
        if self._mode in ("ALL", "PRODUCTION"):
            self._output(self._production_panel.render(snapshot))

    def run(self) -> None:
        """이벤트 루프: 갱신 주기마다 렌더링, KeyboardInterrupt 로 종료."""
        self._output("모니터링 시작 (q=종료, 1=전체, 2=주문, 3=재고, 4=생산)")
        try:
            while True:
                self.render_once()
                time.sleep(self._interval)
        except KeyboardInterrupt:
            self._output("모니터링 종료")
