from interfaces.i_sample_controller import ISampleController
from interfaces.i_order_controller import IOrderController
from interfaces.i_production_controller import IProductionController
from views.production_view import ProductionView
from views.order_view import OrderView


class MainView:
    """메인 뷰: 역할 선택 + 모니터링 + 더미 데이터 관리"""

    def __init__(
        self,
        sample_ctrl: ISampleController,
        order_ctrl: IOrderController,
        prod_ctrl: IProductionController,
        db_path: str = "data/order_system.db",
        input_fn=input,
        output_fn=print,
    ):
        self._sample_ctrl = sample_ctrl
        self._order_ctrl = order_ctrl
        self._prod_ctrl = prod_ctrl
        self._db_path = db_path
        self._input = input_fn
        self._output = output_fn

    def run(self):
        while True:
            self._output("=== 시료 주문 시스템 ===")
            self._output("1. 생산 담당자")
            self._output("2. 주문 담당자")
            self._output("3. 실시간 모니터링")
            self._output("4. 더미 데이터 관리")
            self._output("0. 종료")
            choice = self._input("선택: ")
            if choice == "1":
                ProductionView(
                    self._sample_ctrl,
                    self._order_ctrl,
                    self._prod_ctrl,
                    input_fn=self._input,
                    output_fn=self._output,
                ).run()
            elif choice == "2":
                OrderView(
                    self._sample_ctrl,
                    self._order_ctrl,
                    self._prod_ctrl,
                    input_fn=self._input,
                    output_fn=self._output,
                ).run()
            elif choice == "3":
                self._run_monitor()
            elif choice == "4":
                self._run_dummy_data()
            elif choice == "0":
                self._output("시스템을 종료합니다.")
                break
            else:
                self._output("잘못된 입력입니다.")

    def _run_monitor(self):
        from database.db_manager import DatabaseManager
        from monitor.adapters import DBMonitorAdapter
        from monitor.dashboard import Dashboard

        raw = self._input("갱신 주기(초, 기본 5): ").strip()
        try:
            interval = float(raw) if raw else 5.0
        except ValueError:
            interval = 5.0

        db = DatabaseManager.get_instance(self._db_path)
        provider = DBMonitorAdapter(db)
        self._output("모니터링을 시작합니다. 종료하려면 Ctrl+C를 누르세요.")
        Dashboard(provider, interval=interval, output_fn=self._output).run()

    def _run_dummy_data(self):
        from dummy_data_tool import DummyDataTool
        DummyDataTool(db_path=self._db_path).run()
