"""
monitor_main.py — 모니터링 대시보드 진입점.
실행: python monitor_main.py [--interval 초] [--db 경로]
"""
import argparse

from database.db_manager import DatabaseManager
from monitor.adapters import DBMonitorAdapter
from monitor.dashboard import Dashboard


def main():
    parser = argparse.ArgumentParser(description="시료 주문 시스템 모니터링 대시보드")
    parser.add_argument("--interval", type=float, default=5.0, help="갱신 주기(초)")
    parser.add_argument("--db", default="data/order_system.db", help="DB 경로")
    args = parser.parse_args()

    db = DatabaseManager.get_instance(args.db)
    provider = DBMonitorAdapter(db)
    dashboard = Dashboard(provider, interval=args.interval)
    dashboard.run()


if __name__ == "__main__":
    main()
