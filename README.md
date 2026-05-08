# 시료 주문 시스템 (SampleOrderSystem)

콘솔 기반 반도체 시료 주문 관리 시스템.  
생산 담당자와 주문 담당자가 시료를 등록·주문·승인·생산·출고하는 흐름을 관리한다.

---

## 요구 환경

- **Python 3.10 이상** (표준 라이브러리만 사용, 별도 패키지 설치 불필요)
- 테스트 실행 시에만 `pytest` 필요

```bash
pip install pytest
```

---

## 빠른 시작

```bash
python main.py
```

`data/` 디렉토리와 DB 파일은 **첫 실행 시 자동으로 생성**된다.

---

## 메인 메뉴

```bash
python main.py
```

```
=== 시료 주문 시스템 ===
1. 생산 담당자
2. 주문 담당자
3. 실시간 모니터링
4. 더미 데이터 관리
0. 종료
```

모든 기능을 하나의 진입점에서 사용할 수 있다.

### 1. 생산 담당자

| 메뉴 | 기능 |
|------|------|
| 시료 관리 | 시료 등록 / 목록 조회 / 이름 검색 |
| 주문 승인/거절 | RESERVED 상태 주문 목록 확인 후 승인 또는 거절 |
| 생산 라인 | 현재 생산 중인 시료 및 대기 큐 확인, 생산 완료 처리 |

### 2. 주문 담당자

| 메뉴 | 기능 |
|------|------|
| 시료 주문 | 시료 ID / 고객명 / 수량 입력 후 주문 접수 |
| 모니터링 | 상태별 주문 수, 시료별 재고 현황(여유/부족/고갈) |
| 출고 처리 | CONFIRMED 상태 주문 선택 후 출고 처리 |

### 3. 실시간 모니터링

갱신 주기(초)를 입력하면 DB 데이터를 주기적으로 조회해 콘솔에 표시한다.  
종료하려면 **Ctrl+C** 를 누른다.

### 4. 더미 데이터 관리

```
1. 전체 생성     — 샘플 10개 → 주문 30개 → 생산 작업 순차 생성
2. 샘플 생성     — 원하는 개수 입력
3. 주문 생성     — 원하는 개수 입력 (샘플이 먼저 있어야 함)
4. 생산 큐 생성  — PRODUCING 상태 주문의 생산 작업 자동 등록
5. DB 상태 조회  — 레코드 수, 주문 분포, 재고 수준 출력
6. 전체 초기화   — DB를 초기 상태로 리셋
0. 뒤로
```

처음 실행할 때 **4 → 1 (전체 생성)** 을 선택하면 샘플 10개, 주문 30개, 생산 작업이 자동 생성된다.

---

## 독립 실행 (선택)

메인 메뉴를 거치지 않고 각 도구를 직접 실행할 수도 있다.

```bash
# 실시간 모니터링 (갱신 주기 3초)
python monitor_main.py --interval 3

# 더미 데이터 생성 도구
python dummy_data_tool.py
```

---

## 주문 상태 흐름

```
RESERVED  ──approve(재고 충분)──▶ CONFIRMED ──release──▶ RELEASE
          ──approve(재고 부족)──▶ PRODUCING ──complete──▶ CONFIRMED
          ──reject────────────▶ REJECTED
```

---

## 테스트 실행

```bash
# 전체 테스트 (252개)
python -m pytest tests/ -v

# 빠른 확인 (첫 실패에서 중단)
python -m pytest tests/ -x

# Phase별 실행
python -m pytest tests/test_models.py -v        # Phase 1: 도메인 모델
python -m pytest tests/test_controllers.py -v   # Phase 2: 컨트롤러
python -m pytest tests/test_repositories.py -v  # Phase 3: Repository
python -m pytest tests/test_generators.py -v    # Phase 5: 더미 데이터 생성기
python -m pytest tests/test_monitor.py -v       # Phase 6: 모니터링
python -m pytest tests/test_e2e.py -v           # Phase 7: E2E 통합
```

> `pytest` 단독 명령은 패키지를 못 찾을 수 있으므로 반드시 `python -m pytest`를 사용한다.

---

## 프로젝트 구조

```
SampleOrderSystem/
├── models/          # 도메인 엔티티 (dataclass, 외부 의존 없음)
├── interfaces/      # 컨트롤러 추상 계약 (ABC)
├── database/        # DatabaseManager 싱글톤 (SQLite)
├── repositories/    # DB CRUD 계층
├── controllers/     # 비즈니스 로직 (Repository 주입)
├── views/           # 콘솔 UI (인터페이스만 호출)
├── monitor/         # 모니터링 대시보드 (ANSI 렌더러, 패널 3종)
├── generators/      # 더미 데이터 생성기
├── utils/           # 커스텀 예외
├── tests/           # 테스트 스위트
├── data/            # SQLite DB 파일 저장 위치 (gitignore)
├── main.py          # 메인 애플리케이션 진입점
├── monitor_main.py  # 모니터링 대시보드 진입점
└── dummy_data_tool.py  # 더미 데이터 생성 도구 진입점
```

