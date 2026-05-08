"""
더미 데이터 생성 CLI 도구.
DB 경로는 생성자 파라미터로 전달받으며 하드코딩하지 않는다.
"""
import os
from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_job_repository import ProductionJobRepository
from generators.sample_generator import SampleGenerator
from generators.order_generator import OrderGenerator
from generators.production_generator import ProductionGenerator
from models.order import OrderStatus


class DummyDataTool:
    def __init__(self, db_path: str = "data/order_system.db"):
        self._db_path = db_path

    def _get_db(self) -> DatabaseManager:
        return DatabaseManager.get_instance(self._db_path)

    def _get_repos(self):
        db = self._get_db()
        return (
            SampleRepository(db),
            OrderRepository(db),
            ProductionJobRepository(db),
        )

    def generate_all(self, sample_n: int = 10, order_n: int = 30) -> None:
        """샘플 → 주문 → 생산 작업 순서로 순차 생성한다."""
        print(f"\n[1/3] 샘플 {sample_n}개 생성 중...")
        samples = SampleGenerator().generate(n=sample_n, db_path=self._db_path)
        print(f"      -> {len(samples)}개 생성 완료")

        print(f"[2/3] 주문 {order_n}개 생성 중...")
        orders = OrderGenerator().generate(n=order_n, db_path=self._db_path)
        print(f"      -> {len(orders)}개 생성 완료")

        print("[3/3] 생산 작업 생성 중...")
        jobs = ProductionGenerator().generate(db_path=self._db_path)
        print(f"      -> {len(jobs)}개 생성 완료")

        print("\n전체 생성 완료!")

    def generate_samples(self, n: int = 10) -> None:
        """N개의 샘플을 생성한다."""
        print(f"\n샘플 {n}개 생성 중...")
        samples = SampleGenerator().generate(n=n, db_path=self._db_path)
        print(f"-> {len(samples)}개 생성 완료")

    def generate_orders(self, n: int = 30) -> None:
        """N개의 주문을 생성한다. 먼저 샘플이 있어야 한다."""
        sample_repo, _, _ = self._get_repos()
        if not sample_repo.find_all():
            print("\n주문 생성 전에 샘플을 먼저 생성해야 합니다.")
            return
        print(f"\n주문 {n}개 생성 중...")
        orders = OrderGenerator().generate(n=n, db_path=self._db_path)
        print(f"-> {len(orders)}개 생성 완료")

    def generate_production_jobs(self) -> None:
        """PRODUCING 상태 주문에 대한 ProductionJob을 자동 생성한다."""
        print("\n생산 작업 생성 중...")
        jobs = ProductionGenerator().generate(db_path=self._db_path)
        print(f"-> {len(jobs)}개 생성 완료")

    def show_db_status(self) -> None:
        """DB 레코드 수, 주문 분포, 재고 수준을 출력한다."""
        sample_repo, order_repo, job_repo = self._get_repos()

        samples = sample_repo.find_all()
        orders = order_repo.find_all()
        jobs = job_repo.find_all()

        print("\n=== DB 상태 조회 ===")
        print(f"샘플 수: {len(samples)}")
        print(f"주문 수: {len(orders)}")
        print(f"생산 작업 수: {len(jobs)}")

        print("\n[주문 상태 분포]")
        for status in OrderStatus:
            count = order_repo.count_by_status(status)
            pct = count / len(orders) * 100 if orders else 0
            print(f"  {status.value:<12}: {count:4d}개 ({pct:.1f}%)")

        print("\n[재고 수준]")
        depleted = sum(1 for s in samples if s.stock == 0)
        shortage = sum(1 for s in samples if 0 < s.stock < 100)
        sufficient = sum(1 for s in samples if s.stock >= 100)
        print(f"  고갈(0)    : {depleted}개")
        print(f"  부족(1~99) : {shortage}개")
        print(f"  여유(100+) : {sufficient}개")

    def reset_all(self, sample_n: int = 10, order_n: int = 30) -> None:
        """테이블을 DROP → 재생성 → 초기 데이터를 생성한다."""
        db = self._get_db()
        print("\n[초기화] 기존 데이터 삭제 중...")
        db.execute("DELETE FROM production_jobs")
        db.execute("DELETE FROM orders")
        db.execute("DELETE FROM samples")
        # AUTOINCREMENT 시퀀스도 초기화
        db.execute("DELETE FROM sqlite_sequence WHERE name IN ('samples','orders','production_jobs')")
        print("[초기화] 완료. 초기 데이터 생성 시작...")
        # 싱글톤을 유지하면서 데이터만 새로 생성
        self.generate_all(sample_n=sample_n, order_n=order_n)

    def run(self) -> None:
        """CLI 메뉴를 실행한다."""
        while True:
            print("\n============================")
            print("  더미 데이터 생성 도구")
            print(f"  DB: {self._db_path}")
            print("============================")
            print("1. 전체 생성     (샘플 10개 → 주문 30개 → 생산 작업)")
            print("2. 샘플 생성     (N개 입력)")
            print("3. 주문 생성     (N개 입력)")
            print("4. 생산 큐 생성  (PRODUCING 주문의 ProductionJob 자동 생성)")
            print("5. DB 상태 조회  (레코드 수, 주문 분포, 재고 수준)")
            print("6. 전체 초기화   (DROP → 재생성 → 초기 데이터)")
            print("0. 종료")
            print("----------------------------")

            choice = input("선택: ").strip()

            if choice == "1":
                self.generate_all()

            elif choice == "2":
                try:
                    n = int(input("생성할 샘플 수 (기본 10): ").strip() or "10")
                except ValueError:
                    n = 10
                self.generate_samples(n=n)

            elif choice == "3":
                try:
                    n = int(input("생성할 주문 수 (기본 30): ").strip() or "30")
                except ValueError:
                    n = 30
                self.generate_orders(n=n)

            elif choice == "4":
                self.generate_production_jobs()

            elif choice == "5":
                self.show_db_status()

            elif choice == "6":
                confirm = input("정말 초기화하시겠습니까? (y/N): ").strip().lower()
                if confirm == "y":
                    self.reset_all()
                else:
                    print("취소되었습니다.")

            elif choice == "0":
                print("종료합니다.")
                break

            else:
                print("올바른 번호를 입력하세요.")


if __name__ == "__main__":
    # data 디렉토리 자동 생성
    os.makedirs("data", exist_ok=True)
    DummyDataTool().run()
