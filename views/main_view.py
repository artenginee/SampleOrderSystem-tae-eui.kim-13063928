from interfaces.i_sample_controller import ISampleController
from interfaces.i_order_controller import IOrderController
from interfaces.i_production_controller import IProductionController
from views.production_view import ProductionView
from views.order_view import OrderView


class MainView:
    """메인 뷰: 역할 선택 (생산 담당자 / 주문 담당자)"""

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

    def run(self):
        while True:
            self._output("=== 시료 주문 시스템 ===")
            self._output("1. 생산 담당자")
            self._output("2. 주문 담당자")
            self._output("0. 종료")
            choice = self._input("역할을 선택하세요: ")
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
            elif choice == "0":
                self._output("시스템을 종료합니다.")
                break
            else:
                self._output("잘못된 입력입니다.")
