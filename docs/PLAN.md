# PLAN.md — 시료 주문 시스템 구현 계획

## 개발 방식: Agentic Engineering (TDD + Verify Harness)

각 Phase는 4개의 서브에이전트가 순서대로 실행되는 독립적인 작업 단위다.

### 에이전트 실행 흐름

```
┌─────────────────────────────────────────────────────────┐
│                   Phase N 시작                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │   doc-validation    │  문서 정합성 검증
          │  (PRD·PLAN·CLAUDE)  │  FAIL → 문서 수정 후 재실행
          └──────────┬──────────┘
                PASS │
                     ▼
          ┌─────────────────────┐
          │     ai-action       │  RED → GREEN (TDD)
          │  (테스트 작성·구현)  │  테스트 실패 확인 → 최소 구현
          └──────────┬──────────┘
            완료     │
          ┌──────────┴──────────┐
          │                     │  병렬 실행
          ▼                     ▼
┌─────────────────┐   ┌──────────────────────┐
│   test-verify   │   │  compliance-verify   │
│ (테스트 실행·   │   │ (PRD·아키텍처·POC    │
│  품질 점검)     │   │  정합성 정적 분석)   │
└────────┬────────┘   └──────────┬───────────┘
         │                       │
         └──────────┬────────────┘
                    │ 양쪽 PASS
                    ▼
         ┌─────────────────────┐
         │  PLAN.md 상태 업데이트│  ⬜ → 🟢
         │  Phase 단위 COMMIT   │
         └─────────────────────┘
```

### Phase 진입/완료 조건

| 조건 | 내용 |
|------|------|
| **진입** | `doc-validation` PASS |
| **완료** | `test-verify` PASS + `compliance-verify` PASS + 이전 Phase 테스트 회귀 없음 |
| **블로킹** | 어느 에이전트든 FAIL이면 다음 Phase로 진행 불가 |

---

## POC 참고 저장소

| POC | 저장소 | 핵심 내용 |
|-----|--------|----------|
| POC1 | ConsoleMVC-tae-eui.kim-13063928 | MVC 패키지 구조, 인터페이스 기반 DI, 인메모리 컨트롤러 |
| POC2 | DataPersistence-tae-eui.kim-13063928 | SQLite Repository 패턴, 스키마, CRUD, 싱글톤 DB 매니저 |
| POC3 | DataMonitor-tae-eui.kim-13063928 | 실시간 콘솔 대시보드, ANSI 렌더러, 패널 구조 |
| POC4 | DummyDataGenerator-tae-eui.kim-13063928 | 더미 데이터 생성기, 20개 샘플 프리셋, 상태별 분포 |

---

## 목표 아키텍처 (POC1+2+3+4 통합)

```
SampleOrderSystem/
│
├── models/                    # 도메인 엔티티 (순수 dataclass)
│   ├── sample.py
│   ├── order.py               # Order + OrderStatus
│   └── production_job.py      # ProductionJob + JobStatus
│
├── interfaces/                # 추상 계약 (ABC)
│   ├── i_sample_controller.py
│   ├── i_order_controller.py
│   └── i_production_controller.py
│
├── database/                  # SQLite 관리
│   └── db_manager.py          # DatabaseManager 싱글톤
│
├── repositories/              # DB CRUD 계층
│   ├── base_repository.py
│   ├── sample_repository.py
│   ├── order_repository.py
│   └── production_job_repository.py
│
├── controllers/               # 비즈니스 로직 (인터페이스 구현)
│   ├── sample_controller.py
│   ├── order_controller.py
│   └── production_controller.py
│
├── views/                     # 콘솔 UI
│   ├── main_view.py
│   ├── production_view.py
│   └── order_view.py
│
├── monitor/                   # 별도 모니터링 도구 (POC3)
│   ├── dashboard.py
│   ├── renderer.py
│   └── panels/
│       ├── order_panel.py
│       ├── inventory_panel.py
│       └── production_panel.py
│
├── generators/                # 더미 데이터 생성 도구 (POC4)
│   ├── sample_generator.py
│   ├── order_generator.py
│   └── production_generator.py
│
├── utils/
│   └── exceptions.py
│
├── main.py
├── monitor_main.py
├── dummy_data_tool.py
│
└── tests/
    ├── test_models.py
    ├── test_controllers.py
    ├── test_repositories.py
    ├── test_monitor.py
    ├── test_generators.py
    └── test_e2e.py
```

---

## Phase 1: 도메인 모델 구현

**참고 POC:** POC1 `models/`  
**목표:** Sample·Order 도메인 모델과 상태 전이 로직을 TDD로 구현한다.

### 구현 대상

**`models/sample.py`**
```python
@dataclass
class Sample:
    id: str
    name: str
    avg_production_time: float   # 시간 단위
    yield_rate: float            # 0.0 ~ 1.0
    stock: int = 0

    def calculate_production_quantity(self, shortage: int) -> int:
        # PRD 공식: int(shortage / yield_rate * 0.9)  ← 도메인 모델 기준 (절삭)
        # Phase 5 generators는 POC4 기준 ceil(shortage / (yield_rate * 0.9)) 사용 — 의도적 차이

    def calculate_total_production_time(self, shortage: int) -> float:
        # avg_production_time × 실 생산량
```

**`models/order.py`**
```python
class OrderStatus(Enum):
    RESERVED | REJECTED | PRODUCING | CONFIRMED | RELEASE

@dataclass
class Order:
    def approve(self, has_stock: bool) -> None:
        # RESERVED → CONFIRMED (재고 충분) / PRODUCING (재고 부족)
        # 비RESERVED 상태에서 호출 시 ValueError

    def reject(self) -> None:          # RESERVED → REJECTED, 아니면 ValueError
    def complete_production(self) -> None:  # PRODUCING → CONFIRMED, 아니면 ValueError
    def release(self) -> None:         # CONFIRMED → RELEASE, 아니면 ValueError
```

**`models/production_job.py`** (POC1 기준)
```python
class JobStatus(Enum):
    WAITING | IN_PROGRESS | COMPLETED

@dataclass
class ProductionJob:
    job_id: str
    order_id: str
    sample_id: str
    planned_quantity: int
    actual_quantity: int
    total_time_min: float
    queue_order: int = 0
    status: JobStatus = JobStatus.WAITING
    enqueued_at: datetime = field(default_factory=datetime.now)
```

### 에이전트 실행 절차

**① doc-validation**
- PLAN.md Phase 1 구현 대상과 `CLAUDE.md` 도메인 규칙 섹션이 일치하는지 확인
- `models/` 디렉토리가 없으면 생성 필요 항목으로 보고

**② ai-action**
- `tests/test_models.py` 작성 → `python -m pytest tests/test_models.py -x` 실패 확인
- `models/sample.py`, `models/order.py`, `models/production_job.py` 구현
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- `tests/test_models.py` 전체 실행, 0 FAILED 확인
- 상태 전이 오류 케이스(`ValueError`) 테스트가 포함되어 있는지 점검
- 생산량 공식 테스트가 `int(shortage / yield_rate * 0.9)` 결과와 일치하는지 확인

**④ compliance-verify** (병렬)
- `models/` 파일이 외부 패키지(`repositories`, `controllers` 등)를 import하지 않는지 확인
- `OrderStatus`, `JobStatus` Enum 값이 PRD 명세와 일치하는지 확인
- `Sample`, `Order`, `ProductionJob` 필드가 PRD 속성 값과 매핑되는지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS

---

## Phase 2: MVC 골격 구축 (인메모리)

**참고 POC:** POC1 전체 구조  
**목표:** 인터페이스 기반 MVC를 구축하고, 인메모리 컨트롤러로 콘솔 UI까지 동작시킨다.

### 구현 대상

**`interfaces/`** — ABC 추상 계약
```python
class ISampleController(ABC):
    def create(name, avg_production_time, yield_rate, initial_stock=0) -> Sample
    def find_all() -> list[Sample]
    def find_by_id(sample_id) -> Sample | None
    def find_by_name(keyword) -> list[Sample]
    def update(sample_id, name, avg_production_time, yield_rate) -> bool
    def delete(sample_id) -> bool
    def update_stock(sample_id, delta) -> bool

class IOrderController(ABC):
    def create(sample_id, customer_name, quantity) -> Order
    def find_all() -> list[Order]
    def find_by_id(order_id) -> Order | None
    def find_by_status(status) -> list[Order]
    def update_status(order_id, new_status) -> bool

class IProductionController(ABC):
    def enqueue(order_id, sample_id, planned_quantity, yield_rate, avg_production_time) -> ProductionJob
    def find_in_progress() -> ProductionJob | None
    def find_waiting_queue() -> list[ProductionJob]
    def update_status(job_id, new_status) -> bool
```

**`controllers/`** — 인메모리 구현체
- `SampleController`: `list[Sample]` + 자동 증가 ID (`S001`, `S002`...)
- `OrderController`: `list[Order]` + 자동 증가 ID (`O1`, `O2`...)
- `ProductionController`: `_current_job: ProductionJob | None` + `_queue: deque[ProductionJob]`
  - 완료 시 `_try_start_next()` 자동 호출

**`views/`** — 콘솔 UI (컨트롤러 인터페이스만 호출)
```
views/main_view.py          # 역할 선택 → ProductionView / OrderView
views/production_view.py    # 시료 관리 / 주문 승인·거절 / 생산 라인
views/order_view.py         # 시료 주문 / 모니터링 / 출고 처리
```

**`main.py`** 진입점
```python
sample_ctrl = SampleController()
order_ctrl  = OrderController()
prod_ctrl   = ProductionController()
MainView(sample_ctrl, order_ctrl, prod_ctrl).run()
```

### 에이전트 실행 절차

**① doc-validation**
- Phase 1이 🟢 GREEN인지 확인 (미완료 시 Phase 2 진입 차단)
- `CLAUDE.md` 아키텍처 트리의 `interfaces/`, `controllers/`, `views/` 항목이 PLAN과 일치하는지 확인

**② ai-action**
- `tests/test_controllers.py` 작성 → 실패 확인
- `interfaces/` → `controllers/` → `views/` 순서로 구현
- `python -m pytest tests/ -v` 전체 GREEN (Phase 1 포함) 확인

**③ test-verify** (병렬)
- `test_controllers.py` 전체 실행 확인
- `ProductionController` FIFO 순서 보장 테스트 존재 여부 점검
- View 테스트에서 `input()`/`print()` 의존성 주입 방식 사용 여부 확인
- Phase 1 회귀 없음 확인

**④ compliance-verify** (병렬)
- `views/`가 `controllers/` 구체 클래스가 아닌 `interfaces/` 타입만 참조하는지 확인
- `controllers/`가 `ISampleController`, `IOrderController`, `IProductionController`를 상속하는지 확인
- `ProductionController`에 `_current_job`과 `_queue` 분리 구조가 있는지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS + Phase 1 회귀 없음

---

## Phase 3: SQLite 영속성 계층

**참고 POC:** POC2 전체 구조, POC4 `database/db_manager.py`  
**목표:** SQLite 기반 Repository 계층을 구현한다.

### 구현 대상

**`database/db_manager.py`** — 싱글톤
```python
class DatabaseManager:
    @classmethod
    def get_instance(cls, db_path="data/order_system.db") -> DatabaseManager: ...
    def _init_schema(self): ...   # DDL 자동 실행, PRAGMA 설정
    def query(sql, params=()) -> list[sqlite3.Row]: ...
    def query_one(sql, params=()) -> sqlite3.Row | None: ...
    def execute(sql, params=()) -> int: ...   # lastrowid 반환
    def execute_many(sql, params_list): ...
```
PRAGMA: `foreign_keys = ON`, `journal_mode = WAL`

**DB 스키마** (POC2 표준)
```sql
CREATE TABLE samples (
    sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    avg_production_time REAL NOT NULL,
    yield_rate REAL NOT NULL CHECK(yield_rate > 0 AND yield_rate <= 1),
    stock INTEGER DEFAULT 0,
    description TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    sample_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    status TEXT DEFAULT 'RESERVED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);
CREATE TABLE production_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    sample_id INTEGER NOT NULL,
    planned_quantity INTEGER NOT NULL,
    actual_quantity INTEGER DEFAULT 0,
    total_time_min REAL NOT NULL,
    status TEXT DEFAULT 'WAITING',
    queue_order INTEGER NOT NULL,
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);
```

**`repositories/`** — BaseRepository + 구현체
```python
class BaseRepository(ABC, Generic[T]):
    def create(entity) -> T          # lastrowid로 ID 반영해 반환
    def find_by_id(id) -> T | None
    def find_all() -> list[T]
    def update(entity) -> T
    def delete(id) -> bool
    def count() -> int
```
- `SampleRepository`: `find_by_name(keyword)`, `update_stock(sample_id, delta)`
- `OrderRepository`: `find_by_status()`, `find_by_sample()`, `update_status()`, `count_by_status()`
- `ProductionJobRepository`: `find_waiting_queue()` (queue_order ASC), `find_in_progress()`, `update_status()`, `update_actual_quantity()`

### 에이전트 실행 절차

**① doc-validation**
- Phase 2가 🟢 GREEN인지 확인
- PLAN.md 스키마 정의와 `CLAUDE.md` POC2 섹션 내용 일치 여부 확인

**② ai-action**
- `tests/test_db_manager.py`, `tests/test_repositories.py` 작성 → 실패 확인
- 테스트에서 파일 DB 대신 `:memory:` SQLite 사용
- `database/` → `repositories/` 순서로 구현
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- Repository CRUD 전체 실행 확인
- `create()` 반환값에 DB 할당 ID가 반영되어 있는지 테스트 확인
- `update_stock()` 델타 방식 동작 테스트 존재 여부 확인
- Phase 1·2 회귀 없음 확인

**④ compliance-verify** (병렬)
- `sqlite3.connect()` 직접 호출 코드가 `database/db_manager.py` 외부에 없는지 확인
- `PRAGMA foreign_keys = ON`, `journal_mode = WAL` 설정 누락 여부 확인
- Repository `create()`가 `lastrowid`로 정수형 ID를 반영해 반환하는지 확인
- SQL 쿼리가 f-string이 아닌 파라미터 바인딩(`?`)을 사용하는지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS + Phase 1·2 회귀 없음

---

## Phase 4: 컨트롤러 DB 연동

**참고 POC:** POC1 + POC2  
**목표:** Phase 2 인메모리 컨트롤러를 Phase 3 Repository 기반으로 교체한다.

### 구현 대상

컨트롤러 생성자를 Repository 주입 방식으로 변경한다.

```python
# 변경 전 (인메모리)
class SampleController(ISampleController):
    def __init__(self):
        self._samples: list[Sample] = []

# 변경 후 (Repository 주입)
class SampleController(ISampleController):
    def __init__(self, repo: ISampleRepository):
        self._repo = repo
```

**`main.py`** 진입점 변경
```python
db          = DatabaseManager.get_instance()
sample_repo = SampleRepository(db)
order_repo  = OrderRepository(db)
job_repo    = ProductionJobRepository(db)

sample_ctrl = SampleController(sample_repo)
order_ctrl  = OrderController(order_repo, sample_repo)
prod_ctrl   = ProductionController(job_repo)

MainView(sample_ctrl, order_ctrl, prod_ctrl).run()
```

### 에이전트 실행 절차

**① doc-validation**
- Phase 3이 🟢 GREEN인지 확인
- PLAN.md의 컨트롤러 주입 패턴과 `CLAUDE.md` 아키텍처 섹션이 일치하는지 확인

**② ai-action**
- 기존 `test_controllers.py`가 Repository를 주입받는 구조에서도 통과하도록 수정
- 컨트롤러 생성자 시그니처 변경 → `main.py` 업데이트
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- 컨트롤러 테스트가 `:memory:` SQLite Repository를 주입받아 실행되는지 확인
- `main.py` 실행 후 재시작해도 데이터가 유지되는지 수동 검증 항목 보고
- Phase 1·2·3 회귀 없음 확인

**④ compliance-verify** (병렬)
- 컨트롤러가 `DatabaseManager`나 Repository를 직접 생성하지 않고 주입받는지 확인
- `views/`에서 Repository를 직접 참조하는 코드가 없는지 확인
- `main.py`에서 DB → Repository → Controller 초기화 순서가 올바른지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS + Phase 1·2·3 회귀 없음

---

## Phase 5: 더미 데이터 생성 도구

**참고 POC:** POC4 전체 구조  
**목표:** SQLite DB에 테스트용 더미 데이터를 생성하는 독립 CLI 도구를 구현한다.

### 구현 대상

**`generators/`**
- `SampleGenerator`: 20개 반도체 프리셋 (DRAM-DDR5, NAND Flash, ARM CPU 등), yield_rate ±0.03 변동
- `OrderGenerator`: 20개 고객사 풀, 상태 분포 CONFIRMED 30% / RESERVED 25% / PRODUCING 20% / RELEASE 15% / REJECTED 10%
- `ProductionGenerator`: PRODUCING 상태 주문 대상, `ceil(shortage / (yield_rate * 0.9))`로 생산량 계산

**`dummy_data_tool.py`** — CLI 메뉴 (6개 옵션)
```
1. 전체 생성     — 샘플 → 주문 → 생산 작업 순차 생성
2. 샘플 생성     — N개 (기본 10)
3. 주문 생성     — N개 (기본 30)
4. 생산 큐 생성  — PRODUCING 주문의 ProductionJob 자동 생성
5. DB 상태 조회  — 레코드 수, 주문 분포, 재고 수준
6. 전체 초기화   — DROP → 재생성 → 초기 데이터
```

### 에이전트 실행 절차

**① doc-validation**
- Phase 4가 🟢 GREEN인지 확인
- PLAN.md 생산량 공식과 `CLAUDE.md` POC4 섹션의 공식이 일치하는지 확인
- DB 경로가 `data/order_system.db`로 통일되어 있는지 확인

**② ai-action**
- `tests/test_generators.py` 작성 → 실패 확인
- `generators/` → `dummy_data_tool.py` 순서로 구현
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- 각 Generator의 생성 로직 단위 테스트 확인
- `ProductionGenerator` 공식이 `ceil(shortage / (yield_rate * 0.9))`인지 테스트로 검증되는지 확인
- Phase 1~4 회귀 없음 확인

**④ compliance-verify** (병렬)
- `generators/`가 `DatabaseManager.get_instance()`를 싱글톤으로 사용하는지 확인
- DB 경로 하드코딩 여부 확인 (`config.py` 또는 파라미터로 분리되어야 함)
- `dummy_data_tool.py`가 생산량 공식으로 `ceil` (POC4 방식)을 사용하고, `models/`의 `int` 방식과 혼용하지 않는지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS + Phase 1~4 회귀 없음

---

## Phase 6: 데이터 모니터링 도구

**참고 POC:** POC3 전체 구조  
**목표:** 실시간으로 DB 상태를 조회하는 독립 콘솔 대시보드를 구현한다.

### 구현 대상

**`monitor/interfaces.py`**
```python
class IMonitorDataProvider(ABC):
    def get_snapshot(self) -> MonitorSnapshot: ...

@dataclass
class MonitorSnapshot:
    timestamp: datetime
    order_count_by_status: dict[OrderStatus, int]
    sample_stock_info: list[SampleStockInfo]
    current_production: ProductionJob | None
    production_queue: list[ProductionJob]
    orders_by_status: dict[OrderStatus, list[Order]]
```

**`monitor/adapters.py`**
```python
class DBMonitorAdapter(IMonitorDataProvider):
    def __init__(self, db: DatabaseManager): ...
    def get_snapshot(self) -> MonitorSnapshot: ...  # DB 실시간 조회
```

**`monitor/renderer.py`** (POC3 이식)
- `visible_len(s)` — ANSI 코드 제외 실제 표시 길이
- `ljust_v(s, width)` — ANSI 고려 패딩
- 상태 배지, 카드 레이아웃(`╭─ ... ╰─`), 진행률 바(`████░░░░░░`)

**`monitor/panels/`** — 3개 패널
| 패널 | 표시 정보 |
|------|----------|
| `order_panel.py` | 상태별 주문 수 + 미니 바, 상태별 주문 목록 |
| `inventory_panel.py` | 시료별 재고 / 주문량 / 부족량 / 상태(여유·부족·고갈) |
| `production_panel.py` | 현재 생산 카드 + 대기 큐 목록 |

**`monitor/dashboard.py`** — 이벤트 루프
```
갱신 주기: 5초 (--interval 옵션), 입력 폴링: 150ms
키: 1(ALL) / 2(주문) / 3(재고) / 4(생산) / Enter(즉시갱신) / q(종료)
```

### 에이전트 실행 절차

**① doc-validation**
- Phase 5가 🟢 GREEN인지 확인
- PLAN.md `MonitorSnapshot` 필드 정의와 `CLAUDE.md` POC3 섹션이 일치하는지 확인

**② ai-action**
- `tests/test_monitor.py` 작성 → 실패 확인
- `monitor/interfaces.py` → `monitor/adapters.py` → `monitor/renderer.py` → `monitor/panels/` → `monitor/dashboard.py` 순서로 구현
- `monitor_main.py` 진입점 추가
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- `Dashboard`가 `IMonitorDataProvider`만 의존하는지 단위 테스트 확인
- 모든 패널이 동일한 `MonitorSnapshot` 인스턴스를 공유하는지 확인
- Windows UTF-8·ANSI 관련 설정(`conftest.py`) 존재 여부 확인
- Phase 1~5 회귀 없음 확인

**④ compliance-verify** (병렬)
- `Dashboard`가 DB/Repository를 직접 호출하지 않고 `IMonitorDataProvider`만 사용하는지 확인
- 컬럼 정렬 시 `visible_len()`·`ljust_v()` 없이 `len()`·`ljust()` 직접 사용하는 코드 탐지
- `DBMonitorAdapter`가 `DatabaseManager.get_instance()`를 통해 DB에 접근하는지 확인

**Exit 조건:** test-verify PASS + compliance-verify PASS + Phase 1~5 회귀 없음

---

## Phase 7: E2E 통합 시나리오 테스트

**목표:** 실제 SQLite DB(`:memory:`)를 사용해 전체 계층을 관통하는 시나리오를 검증한다.

### 구현 대상

**`tests/test_e2e.py`** — 5개 시나리오 (mock 없이 실제 객체 사용)

| # | 시나리오 | 검증 포인트 |
|---|----------|------------|
| 1 | 재고 충분 흐름 | 등록(재고 100) → 주문(50) → 승인 → CONFIRMED → 출고 → RELEASE |
| 2 | 재고 부족·생산 완료 흐름 | 등록(재고 0) → 주문(50) → 승인 → PRODUCING + 큐 등록 → 생산 완료 → CONFIRMED → 출고 |
| 3 | 주문 거절 흐름 | 주문(RESERVED) → 거절 → REJECTED |
| 4 | FIFO 생산 큐 흐름 | 주문A·B 순차 PRODUCING → 완료 순서가 A→B임을 확인 |
| 5 | 더미 데이터 → 모니터 조회 | 더미 생성 → DB 어댑터 스냅샷 → 주문·재고·생산 데이터 일치 |

### 에이전트 실행 절차

**① doc-validation**
- Phase 6이 🟢 GREEN인지 확인
- 5개 시나리오가 PRD의 모든 기능 항목을 커버하는지 매핑 확인

**② ai-action**
- `tests/test_e2e.py` 작성 → 실패 확인 (전체 계층 미연동 상태에서 실패해야 함)
- 필요 시 통합 시 발견된 버그 수정
- `python -m pytest tests/ -v` 전체 GREEN 확인

**③ test-verify** (병렬)
- 5개 시나리오 모두 PASSED 확인
- 각 시나리오가 mock 없이 실제 객체를 사용하는지 확인
- `:memory:` SQLite를 사용해 테스트 간 격리되는지 확인
- Phase 1~6 회귀 없음 확인

**④ compliance-verify** (병렬)
- PRD 기능 항목과 E2E 시나리오 1:1 매핑 확인
- 미커버 PRD 항목 있으면 보고
- 시나리오 흐름이 PRD 상태 전이도와 일치하는지 확인

**Exit 조건:** 5개 E2E 시나리오 모두 PASSED + compliance-verify PRD 완전 커버 확인

---

## 현재 상태 요약

| Phase | 상태 | 참고 POC | 테스트 파일 |
|-------|------|----------|------------|
| Phase 1: 도메인 모델 구현 | 🟢 GREEN | — | tests/test_models.py |
| Phase 2: MVC 골격 (인메모리) | 🟢 GREEN | POC1 | tests/test_controllers.py |
| Phase 3: SQLite 영속성 계층 | 🟢 GREEN | POC2 | tests/test_repositories.py, tests/test_db_manager.py |
| Phase 4: 컨트롤러 DB 연동 | ⬜ 미시작 | POC1+2 | (기존 테스트로 검증) |
| Phase 5: 더미 데이터 생성 도구 | ⬜ 미시작 | POC4 | tests/test_generators.py |
| Phase 6: 데이터 모니터링 도구 | ⬜ 미시작 | POC3 | tests/test_monitor.py |
| Phase 7: E2E 통합 시나리오 | ⬜ 미시작 | — | tests/test_e2e.py |
