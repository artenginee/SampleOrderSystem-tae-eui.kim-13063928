from interfaces.i_sample_controller import ISampleController
from interfaces.i_order_controller import IOrderController
from interfaces.i_production_controller import IProductionController
from models.order import OrderStatus


class OrderView:
    """주문 담당자 뷰: 시료 주문 / 모니터링 / 출고 처리"""

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
            self._output("=== 주문 담당자 메뉴 ===")
            self._output("1. 시료 주문")
            self._output("2. 모니터링")
            self._output("3. 출고 처리")
            self._output("0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1":
                self._create_order()
            elif choice == "2":
                self._monitoring()
            elif choice == "3":
                self._release_orders()
            elif choice == "0":
                break
            else:
                self._output("잘못된 입력입니다.")

    # ------------------------------------------------------------------
    # 시료 주문
    # ------------------------------------------------------------------

    def _create_order(self):
        samples = self._sample_ctrl.find_all()
        if not samples:
            self._output("등록된 시료가 없습니다.")
            return
        self._output("=== 시료 목록 ===")
        for s in samples:
            self._output(f"[{s.id}] {s.name} | 재고: {s.stock}")
        sample_id = self._input("시료 ID: ")
        sample = self._sample_ctrl.find_by_id(sample_id)
        if sample is None:
            self._output("시료를 찾을 수 없습니다.")
            return
        customer_name = self._input("고객 이름: ")
        try:
            quantity = int(self._input("수량: "))
        except ValueError:
            self._output("수량은 정수여야 합니다.")
            return
        order = self._order_ctrl.create(sample_id, customer_name, quantity)
        self._output(f"주문 등록 완료: {order.id} | {order.customer_name} | {order.quantity}개")

    # ------------------------------------------------------------------
    # 모니터링
    # ------------------------------------------------------------------

    def _monitoring(self):
        self._output("=== 모니터링 ===")
        self._output("-- 주문 상태별 현황 --")
        for status in [OrderStatus.RESERVED, OrderStatus.CONFIRMED, OrderStatus.PRODUCING, OrderStatus.RELEASE]:
            orders = self._order_ctrl.find_by_status(status)
            self._output(f"  {status.value}: {len(orders)}건")

        self._output("-- 시료 재고 현황 --")
        samples = self._sample_ctrl.find_all()
        active_orders = (
            self._order_ctrl.find_by_status(OrderStatus.RESERVED)
            + self._order_ctrl.find_by_status(OrderStatus.PRODUCING)
        )
        for s in samples:
            total_order_qty = sum(o.quantity for o in active_orders if o.sample_id == s.id)
            if s.stock == 0:
                stock_status = "고갈"
            elif s.stock < total_order_qty:
                stock_status = "부족"
            else:
                stock_status = "여유"
            self._output(f"  [{s.id}] {s.name}: 재고 {s.stock} ({stock_status})")

    # ------------------------------------------------------------------
    # 출고 처리
    # ------------------------------------------------------------------

    def _release_orders(self):
        while True:
            confirmed_orders = self._order_ctrl.find_by_status(OrderStatus.CONFIRMED)
            if not confirmed_orders:
                self._output("출고 대기 중인 주문이 없습니다.")
                return
            self._output("=== CONFIRMED 주문 목록 ===")
            for o in confirmed_orders:
                self._output(f"[{o.id}] 고객: {o.customer_name} | 시료: {o.sample_id} | 수량: {o.quantity}")
            order_id = self._input("출고 처리할 주문 ID (0=뒤로): ")
            if order_id == "0":
                break
            order = self._order_ctrl.find_by_id(order_id)
            if order is None:
                self._output("주문을 찾을 수 없습니다.")
                continue
            if order.status != OrderStatus.CONFIRMED:
                self._output("CONFIRMED 상태의 주문만 출고 처리할 수 있습니다.")
                continue
            order.release()
            self._order_ctrl.update_status(order.id, order.status)
            self._output(f"출고 완료: {order.id} → RELEASE")
