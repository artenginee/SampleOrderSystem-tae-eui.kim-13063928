from monitor.renderer import status_badge
from models.order import OrderStatus
from models.production_job import JobStatus
from views.base_view import BaseView


class ProductionView(BaseView):
    """생산 담당자 뷰: 시료 관리 / 주문 승인·거절 / 생산 라인"""

    def run(self):
        while True:
            self._show_summary()
            self._output("1. 시료 관리   2. 주문 승인/거절   3. 생산 라인   0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1":
                self._sample_management()
            elif choice == "2":
                self._order_approval()
            elif choice == "3":
                self._production_line()
            elif choice == "0":
                break
            else:
                self._output("잘못된 입력입니다.")

    # ── 요약 카드 ───────────────────────────────────────────────

    def _show_summary(self):
        reserved_cnt = len(self._order_ctrl.find_by_status(OrderStatus.RESERVED))
        in_progress = self._prod_ctrl.find_in_progress()
        sample_cnt = len(self._sample_ctrl.find_all())
        queue_cnt = len(self._prod_ctrl.find_waiting_queue())
        prod_info = (
            f"{status_badge('IN_PROGRESS')} 대기 {queue_cnt}건"
            if in_progress else "대기 없음"
        )
        self._card("생산 담당자", [
            f"등록 시료: {sample_cnt}개   대기 주문: {reserved_cnt}건   생산: {prod_info}",
        ])

    # ── 시료 관리 ────────────────────────────────────────────────

    def _sample_management(self):
        while True:
            samples = self._sample_ctrl.find_all()
            self._card(f"시료 목록 ({len(samples)}개)", self._sample_rows(samples))
            self._output("1. 등록   2. 이름 검색   0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1":
                self._create_sample()
            elif choice == "2":
                self._search_samples()
            elif choice == "0":
                break
            else:
                self._output("잘못된 입력입니다.")

    def _create_sample(self):
        name = self._input("시료 이름: ")
        try:
            avg_time = float(self._input("평균 생산 시간(시간): "))
            yield_rate = float(self._input("수율(0~1): "))
            stock = int(self._input("초기 재고 (기본 0): ").strip() or "0")
        except ValueError:
            self._output("입력값이 올바르지 않습니다.")
            return
        sample = self._sample_ctrl.create(name, avg_time, yield_rate, stock)
        self._output(f"→ 등록 완료: [{sample.id}] {sample.name}")

    def _search_samples(self):
        keyword = self._input("검색 키워드: ")
        results = self._sample_ctrl.find_by_name(keyword)
        self._card(f"검색 결과 '{keyword}' ({len(results)}개)", self._sample_rows(results))

    # ── 주문 승인/거절 ───────────────────────────────────────────

    def _order_approval(self):
        while True:
            reserved = self._order_ctrl.find_by_status(OrderStatus.RESERVED)
            self._card(f"승인 대기 주문 ({len(reserved)}건)", self._order_rows(reserved))
            if not reserved:
                return
            order_id = self._input("처리할 주문 ID (0=뒤로): ")
            if order_id == "0":
                break
            order = self._order_ctrl.find_by_id(order_id)
            if order is None:
                self._output("주문을 찾을 수 없습니다.")
                continue
            self._output("1. 승인   2. 거절   0. 취소")
            action = self._input("선택: ")
            if action == "1":
                self._approve_order(order)
            elif action == "2":
                self._reject_order(order)

    def _approve_order(self, order):
        sample = self._sample_ctrl.find_by_id(order.sample_id)
        if sample is None:
            self._output("시료 정보를 찾을 수 없습니다.")
            return
        has_stock = sample.stock >= order.quantity
        order.approve(has_stock)
        self._order_ctrl.update_status(order.id, order.status)
        if order.status == OrderStatus.PRODUCING:
            shortage = order.quantity - sample.stock
            planned_qty = sample.calculate_production_quantity(shortage)
            self._prod_ctrl.enqueue(
                order.id, sample.id, planned_qty,
                sample.yield_rate, sample.avg_production_time,
            )
            self._output(
                f"→ 주문 [{order.id}] {status_badge('PRODUCING')} "
                f"생산 큐 등록 (계획: {planned_qty}개)"
            )
        else:
            self._output(f"→ 주문 [{order.id}] {status_badge('CONFIRMED')}")

    def _reject_order(self, order):
        order.reject()
        self._order_ctrl.update_status(order.id, order.status)
        self._output(f"→ 주문 [{order.id}] {status_badge('REJECTED')}")

    # ── 생산 라인 ────────────────────────────────────────────────

    def _production_line(self):
        while True:
            current = self._prod_ctrl.find_in_progress()
            queue = self._prod_ctrl.find_waiting_queue()

            if current:
                self._card("현재 생산", [
                    f"작업 [{current.job_id}]  주문 #{current.order_id}  "
                    f"계획량 {current.planned_quantity}개",
                    f"총 소요시간: {current.total_time_min:.1f}h  "
                    f"{status_badge('IN_PROGRESS')}",
                ])
            else:
                self._card("현재 생산", ["(생산 중인 작업 없음)"])

            q_rows = [
                f"[{i}] 작업 {j.job_id}  주문 #{j.order_id}  계획량 {j.planned_quantity}개"
                for i, j in enumerate(queue, 1)
            ] or ["(대기 없음)"]
            self._card(f"대기 큐 ({len(queue)}개)", q_rows)

            self._output("1. 생산 완료 처리   0. 뒤로" if current else "0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1" and current:
                self._prod_ctrl.update_status(current.job_id, JobStatus.COMPLETED)
                self._order_ctrl.update_status(current.order_id, OrderStatus.CONFIRMED)
                self._output(
                    f"→ 생산 완료: [{current.job_id}]  "
                    f"주문 [{current.order_id}] {status_badge('CONFIRMED')}"
                )
            elif choice == "0":
                break
