from interfaces.i_sample_controller import ISampleController
from interfaces.i_order_controller import IOrderController
from interfaces.i_production_controller import IProductionController
from models.order import OrderStatus
from models.production_job import JobStatus


class ProductionView:
    """생산 담당자 뷰: 시료 관리 / 주문 승인·거절 / 생산 라인"""

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
            self._output("=== 생산 담당자 메뉴 ===")
            self._output("1. 시료 관리")
            self._output("2. 주문 승인/거절")
            self._output("3. 생산 라인")
            self._output("0. 뒤로")
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

    # ------------------------------------------------------------------
    # 시료 관리
    # ------------------------------------------------------------------

    def _sample_management(self):
        while True:
            self._output("=== 시료 관리 ===")
            self._output("1. 시료 등록")
            self._output("2. 시료 목록")
            self._output("3. 시료 검색")
            self._output("0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1":
                self._create_sample()
            elif choice == "2":
                self._list_samples()
            elif choice == "3":
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
            stock = int(self._input("초기 재고: ") or "0")
        except ValueError:
            self._output("입력값이 올바르지 않습니다.")
            return
        sample = self._sample_ctrl.create(name, avg_time, yield_rate, stock)
        self._output(f"시료 등록 완료: {sample.id} - {sample.name}")

    def _list_samples(self):
        samples = self._sample_ctrl.find_all()
        if not samples:
            self._output("등록된 시료가 없습니다.")
            return
        self._output("=== 시료 목록 ===")
        for s in samples:
            self._output(f"[{s.id}] {s.name} | 재고: {s.stock} | 수율: {s.yield_rate} | 생산시간: {s.avg_production_time}h")

    def _search_samples(self):
        keyword = self._input("검색 키워드: ")
        results = self._sample_ctrl.find_by_name(keyword)
        if not results:
            self._output("검색 결과가 없습니다.")
            return
        for s in results:
            self._output(f"[{s.id}] {s.name} | 재고: {s.stock}")

    # ------------------------------------------------------------------
    # 주문 승인/거절
    # ------------------------------------------------------------------

    def _order_approval(self):
        while True:
            reserved_orders = self._order_ctrl.find_by_status(OrderStatus.RESERVED)
            if not reserved_orders:
                self._output("승인/거절 대기 중인 주문이 없습니다.")
                return
            self._output("=== RESERVED 주문 목록 ===")
            for o in reserved_orders:
                self._output(f"[{o.id}] 고객: {o.customer_name} | 시료: {o.sample_id} | 수량: {o.quantity}")
            order_id = self._input("처리할 주문 ID (0=뒤로): ")
            if order_id == "0":
                break
            order = self._order_ctrl.find_by_id(order_id)
            if order is None:
                self._output("주문을 찾을 수 없습니다.")
                continue
            self._output("1. 승인  2. 거절  0. 취소")
            action = self._input("선택: ")
            if action == "1":
                self._approve_order(order)
            elif action == "2":
                self._reject_order(order)
            elif action == "0":
                continue
            else:
                self._output("잘못된 입력입니다.")

    def _approve_order(self, order):
        sample = self._sample_ctrl.find_by_id(order.sample_id)
        if sample is None:
            self._output("시료 정보를 찾을 수 없습니다.")
            return
        has_stock = sample.stock >= order.quantity
        order.approve(has_stock)
        self._order_ctrl.update_status(order.id, order.status)

        if order.status == OrderStatus.PRODUCING:
            # 재고 부족 → 생산 큐 등록
            shortage = order.quantity - sample.stock
            planned_qty = sample.calculate_production_quantity(shortage)
            self._prod_ctrl.enqueue(
                order.id,
                sample.id,
                planned_qty,
                sample.yield_rate,
                sample.avg_production_time,
            )
            self._output(f"주문 [{order.id}] 생산 큐 등록 완료 (계획 생산량: {planned_qty})")
        else:
            self._output(f"주문 [{order.id}] 승인 완료 (CONFIRMED)")

    def _reject_order(self, order):
        order.reject()
        self._order_ctrl.update_status(order.id, order.status)
        self._output(f"주문 [{order.id}] 거절 완료 (REJECTED)")

    # ------------------------------------------------------------------
    # 생산 라인
    # ------------------------------------------------------------------

    def _production_line(self):
        while True:
            self._output("=== 생산 라인 ===")
            current = self._prod_ctrl.find_in_progress()
            if current:
                self._output(f"[현재 생산 중] {current.job_id} | 주문: {current.order_id} | 계획량: {current.planned_quantity}")
            else:
                self._output("[현재 생산 중] 없음")

            queue = self._prod_ctrl.find_waiting_queue()
            self._output(f"[대기 큐] {len(queue)}개")
            for j in queue:
                self._output(f"  {j.job_id} | 주문: {j.order_id} | 계획량: {j.planned_quantity}")

            self._output("1. 생산 완료 처리  0. 뒤로")
            choice = self._input("선택: ")
            if choice == "1":
                if current is None:
                    self._output("현재 생산 중인 작업이 없습니다.")
                    continue
                self._prod_ctrl.update_status(current.job_id, JobStatus.COMPLETED)
                # 연결된 주문도 CONFIRMED로 전환
                self._order_ctrl.update_status(current.order_id, OrderStatus.CONFIRMED)
                self._output(f"생산 완료: {current.job_id}")
            elif choice == "0":
                break
            else:
                self._output("잘못된 입력입니다.")
