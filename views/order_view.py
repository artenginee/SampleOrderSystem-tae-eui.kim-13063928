from monitor.renderer import status_badge
from models.order import OrderStatus
from views.base_view import BaseView


class OrderView(BaseView):
    """주문 담당자 뷰: 시료 주문 / 현황 조회 / 출고 처리"""

    def run(self):
        while True:
            self._card("주문 현황", self._order_stats_rows())
            self._output("1. 시료 주문   2. 현황 상세   3. 출고 처리   0. 뒤로")
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

    # ── 시료 주문 ────────────────────────────────────────────────

    def _create_order(self):
        samples = self._sample_ctrl.find_all()
        self._card(f"시료 목록 ({len(samples)}개)", self._sample_rows(samples))
        if not samples:
            return
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
        self._output(
            f"→ 주문 등록: [{order.id}] {order.customer_name} | "
            f"{order.quantity}개 {status_badge('RESERVED')}"
        )

    # ── 현황 상세 ────────────────────────────────────────────────

    def _monitoring(self):
        while True:
            active_orders = (
                self._order_ctrl.find_by_status(OrderStatus.RESERVED)
                + self._order_ctrl.find_by_status(OrderStatus.PRODUCING)
            )
            self._card("주문 현황", self._order_stats_rows())
            self._card("재고 현황", self._inventory_rows(active_orders))
            choice = self._input("갱신(Enter) / 뒤로(0): ")
            if choice == "0":
                break

    # ── 출고 처리 ────────────────────────────────────────────────

    def _release_orders(self):
        while True:
            confirmed = self._order_ctrl.find_by_status(OrderStatus.CONFIRMED)
            self._card(f"출고 대기 ({len(confirmed)}건)", self._order_rows(confirmed))
            if not confirmed:
                return
            order_id = self._input("출고할 주문 ID (0=뒤로): ")
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
            self._output(f"→ 출고 완료: [{order.id}] {status_badge('RELEASE')}")
