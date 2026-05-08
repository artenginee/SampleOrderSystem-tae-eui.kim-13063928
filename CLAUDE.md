# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

콘솔 기반 시료 주문 시스템. 고객 주문 담당자와 생산 담당자가 시료를 등록·주문·승인·생산·출고하는 흐름을 관리한다.

- 상세 기능 명세: `docs/PRD.md`
- 단계별 구현 계획: `docs/PLAN.md`
- POC 참고 저장소 4개 (아래 아키텍처 섹션 참조)

---

## 개발 방식: Agentic Engineering (TDD + Verify Harness)

모든 기능 구현은 아래 순서를 반드시 따른다:

```
1. RED    — 실패하는 테스트 작성 → python -m pytest -x 로 실패 확인
2. GREEN  — 테스트를 통과시키는 최소 구현
3. VERIFY — python -m pytest tests/ -v 전체 스위트 GREEN 확인
4. COMMIT — Phase 단위 커밋
```

**철의 법칙:** 실패하는 테스트가 먼저 존재하지 않는 한 프로덕션 코드를 작성하지 않는다.  
코드를 먼저 작성했다면 삭제하고 처음부터 시작한다. 예외 없음.

Phase 진입 조건: 현재 Phase 모든 테스트 GREEN + 이전 Phase 테스트 깨지지 않음.  
Phase 완료 후 `docs/PLAN.md` 상태 테이블을 업데이트한다.

### Verify Harness 에이전트 구성

`.claude/agents/`에 4개의 서브에이전트가 정의되어 있다:

| 에이전트 | 역할 | 실행 시점 |
|----------|------|----------|
| `doc-validation` | PRD·PLAN·CLAUDE.md 문서 정합성 검증 | ai-action 실행 전 |
| `ai-action` | TDD 사이클로 테스트·구현 코드 작성 | doc-validation PASS 후 |
| `test-verify` | 전체 테스트 스위트 실행 및 품질 점검 | ai-action 완료 후 (병렬) |
| `compliance-verify` | PRD·아키텍처·POC 패턴 정합성 정적 분석 | ai-action 완료 후 (병렬) |

**실행 흐름:**
```
doc-validation → ai-action → test-verify ┐ (병렬)
                                          ├→ 최종 판정
                             compliance-verify ┘
```

---

## 테스트 실행

```bash
# 전체 (verify harness)
python -m pytest tests/ -v

# RED 확인 (첫 실패에서 중단)
python -m pytest tests/ -x

# 단일 파일
python -m pytest tests/test_controllers.py -v

# 단일 테스트
python -m pytest tests/test_controllers.py::test_approve_with_stock -v
```

`pytest` 단독 명령은 패키지를 못 찾으므로 반드시 `python -m pytest`를 사용한다.

---

## 아키텍처 (POC 기반 MVC)

계층 의존 방향: `views → controllers(interfaces) → repositories → database`  
모니터링·더미 생성 도구는 독립 진입점으로 분리한다.

```
SampleOrderSystem/
├── models/              # 순수 dataclass, 외부 의존 없음
├── interfaces/          # ABC 기반 추상 계약 (ISampleController 등)
├── database/            # DatabaseManager 싱글톤 (SQLite)
├── repositories/        # DB CRUD 계층 (BaseRepository 상속)
├── controllers/         # 비즈니스 로직, 인터페이스 구현, Repository 주입받음
├── views/               # 콘솔 UI, 컨트롤러 인터페이스만 호출
├── monitor/             # 별도 모니터링 도구 (dashboard, renderer, panels)
├── generators/          # 더미 데이터 생성 도구
├── utils/               # 커스텀 예외 등
├── main.py              # 메인 애플리케이션 진입점
├── monitor_main.py      # 모니터링 도구 진입점
└── dummy_data_tool.py   # 더미 데이터 생성 도구 진입점
```

### 실행 방법

```bash
python main.py                        # 메인 애플리케이션
python monitor_main.py                # 모니터링 대시보드
python monitor_main.py --interval 3  # 갱신 주기 3초
python dummy_data_tool.py             # 더미 데이터 생성
```

---

## POC 참고 사항

### POC1 — MVC 골격 (ConsoleMVC)

인터페이스 기반 DI 구조. View는 구체 Controller가 아닌 Interface에만 의존한다.

```python
# controllers/production_controller.py 핵심 구조
class ProductionController(IProductionController):
    def __init__(self):
        self._current_job: ProductionJob | None = None
        self._queue: deque[ProductionJob] = deque()   # FIFO

    def update_status(self, job_id, new_status):
        # 완료 처리 시 _try_start_next() 자동 호출
```

모델 ID 체계 (인메모리): Sample → `S001`, Order → `O1` (자동 증가 문자열)

### POC2 — SQLite 영속성 (DataPersistence)

DB 연결은 싱글톤, 모든 쿼리는 `DatabaseManager`를 통한다. 직접 `sqlite3.connect()` 호출 금지.

```python
db = DatabaseManager.get_instance("data/order_system.db")
# PRAGMA foreign_keys = ON, journal_mode = WAL 자동 설정
```

ID 체계 (DB): `INTEGER PRIMARY KEY AUTOINCREMENT` — 정수형, 문자열 아님.  
Repository의 `create()`는 `lastrowid`로 DB 할당 ID를 모델에 반영해 반환한다.

### POC3 — 모니터링 도구 (DataMonitor)

대시보드는 `IMonitorDataProvider.get_snapshot()` 하나만 호출한다.  
모든 패널이 동일한 `MonitorSnapshot`을 사용해 렌더링 중 데이터 불일치를 방지한다.

```python
# ANSI 렌더러 핵심 — 컬럼 정렬 시 반드시 사용
visible_len(s)       # ANSI 코드 제외 실제 표시 길이
ljust_v(s, width)    # ANSI 고려 패딩
```

Windows 환경: `conftest.py`에서 UTF-8 강제, `enable_ansi()`로 Virtual Terminal 활성화.

### POC4 — 더미 데이터 생성 (DummyDataGenerator)

생산량 계산 (POC4 기준, PRD 공식과 차이 있음):
```python
shortage     = max(0, order.quantity - sample.stock)
planned_qty  = ceil(shortage / (yield_rate * 0.9))   # ceil 사용
total_time   = avg_production_time * planned_qty
```

주문 상태 분포: CONFIRMED 30%, RESERVED 25%, PRODUCING 20%, RELEASE 15%, REJECTED 10%  
DB 경로: `data/order_system.db` (POC4의 `data/semiconductor.db`에서 통일)

---

## 도메인 핵심 규칙

### 주문 상태 흐름

```
RESERVED  →  CONFIRMED   (approve, 재고 충분)
RESERVED  →  PRODUCING   (approve, 재고 부족 → 생산 큐 자동 등록)
RESERVED  →  REJECTED    (reject)
PRODUCING →  CONFIRMED   (complete_production)
CONFIRMED →  RELEASE     (release)
```

잘못된 상태에서 전이 메서드 호출 시 `ValueError`.

### 재고 상태

| 상태 | 조건 |
|------|------|
| SUFFICIENT (여유) | 재고 ≥ 주문량 |
| SHORTAGE (부족) | 0 < 재고 < 주문량 |
| DEPLETED (고갈) | 재고 == 0 |

### 생산 라인

- 스케줄링: FIFO (`collections.deque`)
- 현재 작업(`_current_job`)과 대기 큐(`_queue`) 분리 관리
- 작업 완료 시 다음 대기 작업 자동 시작 (`_try_start_next()`)
- `JobStatus`: WAITING → IN_PROGRESS → COMPLETED

---

## 현재 상태

**Phase 1 — 완료 (🟢 GREEN)**  
**Phase 2 — 완료 (🟢 GREEN)**  
**Phase 3 — 완료 (🟢 GREEN)**  
**Phase 4 — 완료 (🟢 GREEN)**  
**Phase 5 — 진행 중**: `tests/test_generators.py` 작성부터 시작한다. 상세 계획은 `docs/PLAN.md` 참조.
