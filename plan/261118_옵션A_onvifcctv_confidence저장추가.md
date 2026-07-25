# 옵션 A: D:\onvifcctv 에 YOLO confidence 저장 추가 — 구현 계획서 (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** YOLO 1차 검출 중 **알림 트리거의 원인이 된 박스들의 conf 값을 영구 저장**한다. 단일 컬럼 `yolo_confidence REAL` 1개만 추가하며, 값은 **트리거 박스들의 최소 conf**(=이 알림이 살아남는 임계점)다. 석사 논문 4.2(PR curve)·4.3(LLM FAR) 분석에 직결.

**Architecture:** Detector(`HazardDetector`/`DangerDetector`)가 warning을 만드는 시점에 트리거 박스의 conf 리스트(`trigger_confs`)를 warning dict에 함께 담는다. AlertHandler가 history INSERT 직전 모든 trigger_confs를 통합하여 `min()` 한 값을 row의 `yolo_confidence`로 저장. 신호선 추가 없음, 기존 payload 그대로 활용. 기존 DB는 `ALTER TABLE ADD COLUMN`로 무중단 마이그레이션.

**Tech Stack:** Python 3.12 / SQLite (PRAGMA WAL) / PyQt6 / pytest. `.venv312_cuda/Scripts/python.exe` 환경 사용 (CLAUDE.md 규칙 12).

**작성일:** 2026-05-18 (v2: 트리거 박스 min 규칙 채택, JSON 컬럼 폐기)
**예상 작업 시간:** 코드 수정 2~3시간 + 실알림 검증 30분~수십 분 = **합계 2.5~3.5시간**

---

## v1 대비 변경 사항

| 항목 | v1 (폐기) | v2 (현행) |
|---|---|---|
| 신규 컬럼 | `yolo_confidence` + `yolo_conf_detail` (JSON) | **`yolo_confidence` 1개만** (맨 뒤에 추가) |
| 값 결정 규칙 | warn_key별 max (hazard_*: class match, 그 외: global max) | **트리거 박스들의 min conf** (사용자 요구사항) |
| Detector 수정 | 없음 (AlertHandler에서 추정) | **있음**: `trigger_confs: List[float]` 필드를 warning에 추가 |
| 작업 시간 | 1.5~2h | 2.5~3.5h |

**v1이 틀린 이유:** 사람 10명이 화면에 있어도 트리거된 사람은 1명일 수 있다. 멀리 있어 conf=0.3인 다른 사람은 트리거가 아니므로 conf 값에 반영되면 안 된다. 또한 근접 경고는 (사람, 중장비) 쌍이 트리거인데 어느 쌍의 어느 박스가 트리거인지 Detector만이 안다 — AlertHandler 단에서는 복원 불가.

---

## 배경

- `Detection.confidence`는 `src/ai/hazard_detector.py:289` 에서 set
- `VideoThread.alert_request_signal` payload 에 `'detection_result': (detections, warnings, ...)` 형태로 그대로 전달됨
- 현재 warnings dict 는 `{warn_key: {'count': N, 'msg': '...'}}` 만 들고 있고 **트리거 박스 식별 정보가 없다**
- 즉 conf 값을 "트리거 박스만" 정확히 뽑으려면 warnings dict 스키마를 확장해야 함
- 알림 기록 진입점은 `AlertHandler._record_combined_history`(정탐/미실시) + `_record_blocked`(오탐/오류) 두 곳

## 데이터 모델

`history` 테이블 컬럼 (변경 후):

```
id, timestamp, camera_name, content, telegram_id, remarks,
second_judgment, second_reason, llm_model, ai_elapsed,
snapshot_path, prompt_profile, user_correction,
created_at,
yolo_confidence   ← 신규 (맨 끝)
```

```sql
yolo_confidence REAL NOT NULL DEFAULT 0
-- 해당 알림을 발생시킨 모든 트리거 박스의 conf 중 최솟값.
-- 의미: 이 임계값을 conf 컷오프로 잡으면 이 알림이 살아남는다(임계점).
-- 1차 단독 시뮬레이션·PR curve 임계값 sweep에 그대로 사용.
```

**SQLite ALTER TABLE 의 컬럼 추가는 항상 끝에 붙기 때문에**, 신규 DB의 `_CREATE_TABLE_SQL` 도 같은 순서로 두어 기존/신규 DB 컬럼 순서를 통일한다.

## warnings dict 스키마 확장

모든 `_check_*` 메서드와 `hazard_<class>` 생성부가 다음 키를 추가:

```python
warnings[<warn_key>] = {
    'count': N,
    'msg': '...',
    'trigger_confs': [float, ...]   # ← 신규: 이 경고를 트리거한 박스들의 conf 리스트
}
```

각 항목의 `trigger_confs` 모음 규칙:

| warn_key | 트리거 박스 정의 | trigger_confs |
|---|---|---|
| `hazard_NO-Hardhat` 등 | 해당 class detection 전부 | 그 detection들의 conf 리스트 |
| `warning_people_in_controlled_area` (Cone 영역 진입) | 영역 안에 들어간 사람들 | 그 사람 detection들의 conf 리스트 |
| `warning_close_to_machinery` / `_to_vehicle` (근접) | 위험 거리 안에 있는 (사람, 중장비) 쌍 각각 | **쌍별 min(person.conf, mv.conf)** 의 리스트 |
| `warning_people_in_utility_pole_controlled_area` | 폴 영역 안 사람들 | 사람 conf 리스트 |
| `detect_machinery_close_to_pole` | 폴 근접 중장비들 | 중장비 conf 리스트 |

**AlertHandler 측 최종 집계:**
```python
all_trigger_confs = []
for wk in confirmed_warnings:
    all_trigger_confs.extend(warnings[wk].get('trigger_confs', []))
row_yolo_conf = min(all_trigger_confs) if all_trigger_confs else 0.0
```

여러 경고가 한 row 에 묶이는 경우(통합 엔트리)도 모든 trigger_confs 의 min 을 채택한다.

## 영향받는 파일

| 파일 | 변경 종류 | 책임 |
|---|---|---|
| `src/history_store.py` | **수정** | 스키마 + insert/update + 마이그레이션 + entry 컬럼 리스트 |
| `src/database.py` | **수정** | `add_history_entry` 시그니처에 `yolo_confidence` kwarg 추가 |
| `src/ai/hazard_detector.py` | **수정** | `hazard_<class>` warning 생성 시 trigger_confs 수집 |
| `src/ai/danger_detector.py` | **수정** | 5개 `_check_*` 메서드 모두 trigger_confs 수집 |
| `src/utils/alert_handler.py` | **수정** | `_record_combined_history`, `_record_blocked` 에서 모든 trigger_confs 모아 min 계산 후 전달 |
| `tests/database/test_history_yolo_conf.py` | **신규** | 스키마/마이그레이션/CRUD 단위 테스트 |
| `tests/ai/test_danger_detector_trigger_confs.py` | **신규** | DangerDetector 의 trigger_confs 수집 동작 검증 |
| `tests/utils/test_alert_handler_conf.py` | **신규** | warnings dict → row min 집계 검증 |

> i18n 영향 없음. spec 파일(build_cuda/dml) hiddenimports 변경 없음. UI 변경 없음.

---

## Task 1: HistoryStore 스키마·마이그레이션·CRUD 확장 (단일 컬럼)

**Files:**
- Modify: `src/history_store.py` (스키마, `_UPDATABLE_COLUMNS`, `_ENTRY_COLUMNS`, `_init_db`, `insert`, `migrate_from_json`)
- Test: `tests/database/test_history_yolo_conf.py`

### Step 1.1 — 실패 테스트 작성

- [ ] **Step 1.1.1: `tests/database/test_history_yolo_conf.py` 신규 작성**

```python
"""HistoryStore.yolo_confidence 컬럼 동작 검증."""
from __future__ import annotations
import sqlite3
import pytest

from src.history_store import HistoryStore


@pytest.fixture
def store(tmp_path):
    return HistoryStore(str(tmp_path / "history.db"))


def test_schema_has_yolo_confidence(store):
    conn = sqlite3.connect(store._db_path)
    try:
        cur = conn.execute("PRAGMA table_info(history)")
        cols = {row[1] for row in cur.fetchall()}
    finally:
        conn.close()
    assert "yolo_confidence" in cols


def test_insert_stores_yolo_confidence(store):
    entry = store.insert(
        camera_name="cam1", content="hazard NO-Hardhat",
        telegram_id="123", yolo_confidence=0.42,
    )
    assert entry["yolo_confidence"] == pytest.approx(0.42)

    fetched = store.fetch_by_id(entry["id"])
    assert fetched["yolo_confidence"] == pytest.approx(0.42)


def test_insert_default_zero_when_omitted(store):
    entry = store.insert(camera_name="cam1", content="x", telegram_id="")
    assert entry["yolo_confidence"] == 0.0


def test_update_yolo_confidence(store):
    entry = store.insert(camera_name="cam1", content="x", telegram_id="")
    ok = store.update(entry["id"], yolo_confidence=0.55)
    assert ok is True
    assert store.fetch_by_id(entry["id"])["yolo_confidence"] == pytest.approx(0.55)


def test_migration_adds_column_to_existing_db(tmp_path):
    """v4.93 이전 스키마 시뮬레이션 → 인스턴스화 시 ALTER 자동 적용."""
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE history (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL DEFAULT '',
            camera_name TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            telegram_id TEXT NOT NULL DEFAULT '',
            remarks TEXT NOT NULL DEFAULT '',
            second_judgment TEXT NOT NULL DEFAULT '',
            second_reason TEXT NOT NULL DEFAULT '',
            llm_model TEXT NOT NULL DEFAULT '',
            ai_elapsed REAL NOT NULL DEFAULT 0,
            snapshot_path TEXT NOT NULL DEFAULT '',
            prompt_profile TEXT NOT NULL DEFAULT '',
            user_correction TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO history (id, camera_name) VALUES ('old-1', 'cam')")
    conn.commit()
    conn.close()

    HistoryStore(str(db_path))  # ALTER 발동

    conn = sqlite3.connect(db_path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(history)").fetchall()}
        assert "yolo_confidence" in cols
        # 기존 row 의 디폴트 0 확인
        v = conn.execute("SELECT yolo_confidence FROM history WHERE id='old-1'").fetchone()[0]
        assert v == 0.0
    finally:
        conn.close()


def test_migration_idempotent(tmp_path):
    db_path = tmp_path / "history.db"
    HistoryStore(str(db_path))
    HistoryStore(str(db_path))  # 두 번째 호출도 정상
```

- [ ] **Step 1.1.2: 실패 확인**

Run:
```
.venv312_cuda/Scripts/python.exe -m pytest tests/database/test_history_yolo_conf.py -v
```
Expected: 모두 FAIL.

### Step 1.2 — 스키마·상수 갱신

- [ ] **Step 1.2.1: `src/history_store.py:39-56` 의 `_CREATE_TABLE_SQL` 교체** (yolo_confidence 를 created_at 뒤 맨 끝에)

```python
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id              TEXT PRIMARY KEY,
    timestamp       TEXT NOT NULL DEFAULT '',
    camera_name     TEXT NOT NULL DEFAULT '',
    content         TEXT NOT NULL DEFAULT '',
    telegram_id     TEXT NOT NULL DEFAULT '',
    remarks         TEXT NOT NULL DEFAULT '',
    second_judgment TEXT NOT NULL DEFAULT '',
    second_reason   TEXT NOT NULL DEFAULT '',
    llm_model       TEXT NOT NULL DEFAULT '',
    ai_elapsed      REAL NOT NULL DEFAULT 0,
    snapshot_path   TEXT NOT NULL DEFAULT '',
    prompt_profile  TEXT NOT NULL DEFAULT '',
    user_correction TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    yolo_confidence REAL NOT NULL DEFAULT 0
)
"""
```

- [ ] **Step 1.2.2: `_UPDATABLE_COLUMNS`/`_ENTRY_COLUMNS` 교체**

```python
_UPDATABLE_COLUMNS: frozenset[str] = frozenset({
    "timestamp", "camera_name", "content", "telegram_id", "remarks",
    "second_judgment", "second_reason", "llm_model", "ai_elapsed",
    "snapshot_path", "prompt_profile", "user_correction",
    "yolo_confidence",
})

_ENTRY_COLUMNS: tuple[str, ...] = (
    "id", "timestamp", "camera_name", "content", "telegram_id", "remarks",
    "second_judgment", "second_reason", "llm_model", "ai_elapsed",
    "snapshot_path", "prompt_profile", "user_correction",
    "yolo_confidence",
)
```

### Step 1.3 — `_init_db()` 에 ALTER TABLE 추가

- [ ] **Step 1.3.1: `src/history_store.py:137-146` 의 `_init_db` 교체**

```python
def _init_db(self) -> None:
    with self._lock:
        conn = self._get_conn()
        try:
            conn.execute(_CREATE_TABLE_SQL)
            # 기존 v4.93 이전 DB 대비 ALTER. 컬럼이 이미 있으면 OperationalError 무시.
            try:
                conn.execute(
                    "ALTER TABLE history ADD COLUMN yolo_confidence REAL NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            for idx_sql in _CREATE_INDEXES_SQL:
                conn.execute(idx_sql)
            conn.commit()
        finally:
            conn.close()
```

### Step 1.4 — `insert()` 시그니처 확장

- [ ] **Step 1.4.1: `src/history_store.py:151-205` 의 `insert` 교체**

```python
def insert(
    self,
    camera_name: str,
    content: str,
    telegram_id: str,
    remarks: str = "",
    second_judgment: str = "",
    second_reason: str = "",
    llm_model: str = "",
    ai_elapsed: float = 0.0,
    snapshot_path: str = "",
    prompt_profile: str = "",
    yolo_confidence: float = 0.0,
) -> dict[str, Any]:
    """알림 이력 1건 추가. entry dict 반환.

    yolo_confidence: 이 알림을 트리거한 박스들 중 min(conf).
                     PR curve 임계값 sweep용 단일 스칼라.
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conf_value = float(yolo_confidence or 0.0)
    entry: dict[str, Any] = {
        "id": entry_id,
        "timestamp": timestamp,
        "camera_name": camera_name,
        "content": content,
        "telegram_id": telegram_id,
        "remarks": remarks,
        "second_judgment": second_judgment,
        "llm_model": llm_model,
        "second_reason": second_reason,
        "ai_elapsed": round(ai_elapsed, 1),
        "snapshot_path": snapshot_path,
        "prompt_profile": prompt_profile,
        "user_correction": "",
        "yolo_confidence": conf_value,
    }
    with self._lock:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO history (
                    id, timestamp, camera_name, content, telegram_id, remarks,
                    second_judgment, second_reason, llm_model, ai_elapsed,
                    snapshot_path, prompt_profile, user_correction,
                    yolo_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id, timestamp, camera_name, content, telegram_id, remarks,
                    second_judgment, second_reason, llm_model, round(ai_elapsed, 1),
                    snapshot_path, prompt_profile, "",
                    conf_value,
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            _logger.error(f"[HistoryStore] insert failed: {e}", category="HistoryStore")
            raise
        finally:
            conn.close()
    return entry
```

### Step 1.5 — `update()` 에 float 캐스팅 분기 추가

- [ ] **Step 1.5.1: `src/history_store.py:207-238` 의 `update`에서 valid 빌드 루프를 교체**

```python
        valid: dict[str, Any] = {}
        for k, v in kwargs.items():
            if k not in _UPDATABLE_COLUMNS:
                continue
            if k == "user_correction":
                valid[k] = _serialize_user_correction(v)
            elif k == "yolo_confidence":
                valid[k] = float(v or 0.0)
            else:
                valid[k] = v
```

### Step 1.6 — `migrate_from_json` 에 신규 컬럼 채우기

- [ ] **Step 1.6.1: `migrate_from_json` 의 rows.append / executemany 교체**

```python
                rows.append((
                    entry.get("id") or str(uuid.uuid4()),
                    entry.get("timestamp", ""),
                    entry.get("camera_name", ""),
                    entry.get("content", ""),
                    entry.get("telegram_id", ""),
                    entry.get("remarks", ""),
                    entry.get("second_judgment", ""),
                    entry.get("second_reason", ""),
                    entry.get("llm_model", ""),
                    float(entry.get("ai_elapsed", 0) or 0),
                    entry.get("snapshot_path", ""),
                    entry.get("prompt_profile", ""),
                    _serialize_user_correction(entry.get("user_correction", "")),
                    float(entry.get("yolo_confidence", 0) or 0),
                ))
            conn.executemany(
                """
                INSERT OR IGNORE INTO history (
                    id, timestamp, camera_name, content, telegram_id, remarks,
                    second_judgment, second_reason, llm_model, ai_elapsed,
                    snapshot_path, prompt_profile, user_correction,
                    yolo_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
```

### Step 1.7 — 테스트 통과 + 커밋

- [ ] **Step 1.7.1: 실행**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/database -v
```
Expected: 신규 6 PASS + 기존 회귀 0 FAIL.

- [ ] **Step 1.7.2: 커밋**

```bash
git add src/history_store.py tests/database/test_history_yolo_conf.py
git commit -m "feat(history): yolo_confidence REAL 컬럼 추가 + ALTER 마이그레이션

논문 4.2(PR curve)·4.3(FAR) 분석을 위해 알림 이력 row 당 트리거 박스의
최소 conf 1개를 저장. 단일 컬럼으로 단순화.

- _CREATE_TABLE_SQL: yolo_confidence REAL 컬럼을 created_at 뒤 맨 끝에 추가
- _init_db: ALTER TABLE ADD COLUMN 무중단 마이그레이션 (idempotent)
- insert/update/migrate_from_json: yolo_confidence kwarg 시그니처
"
```

---

## Task 2: CameraManager 위임 시그니처 확장

**Files:**
- Modify: `src/database.py:112-129`

### Step 2.1 — `add_history_entry` 시그니처 교체

- [ ] **Step 2.1.1: 교체**

```python
    def add_history_entry(
        self, camera_name, content, telegram_id, remarks="",
        second_judgment="", second_reason="", llm_model="",
        ai_elapsed=0.0, snapshot_path="", prompt_profile="",
        yolo_confidence: float = 0.0,
    ):
        """알림 이력 1건 추가 (SQLite). entry dict 반환."""
        return self._history_store.insert(
            camera_name=camera_name,
            content=content,
            telegram_id=telegram_id,
            remarks=remarks,
            second_judgment=second_judgment,
            second_reason=second_reason,
            llm_model=llm_model,
            ai_elapsed=ai_elapsed,
            snapshot_path=snapshot_path,
            prompt_profile=prompt_profile,
            yolo_confidence=yolo_confidence,
        )
```

> `update_history_entry`는 `**kwargs` 위임이라 변경 불필요.

- [ ] **Step 2.1.2: 커밋**

```bash
git add src/database.py
git commit -m "feat(db): CameraManager.add_history_entry에 yolo_confidence kwarg 추가"
```

---

## Task 3: DangerDetector 트리거 박스 conf 수집

**Files:**
- Modify: `src/ai/danger_detector.py` (5개 메서드 모두)
- Test: `tests/ai/test_danger_detector_trigger_confs.py`

### Step 3.1 — 실패 테스트 작성

- [ ] **Step 3.1.1: `tests/ai/test_danger_detector_trigger_confs.py` 신규**

```python
"""DangerDetector 가 trigger_confs 를 정확히 수집하는지 검증.

datas 형식: [x1, y1, x2, y2, conf, class_id, ...]
class_id: 5=Person, 8=Machinery, 10=Vehicle, 9=Pole.
"""
from __future__ import annotations
import pytest


@pytest.fixture
def det():
    from src.ai.danger_detector import DangerDetector
    return DangerDetector()


def test_proximity_machinery_pair_min_conf(det):
    """사람(0.85) + 중장비(0.40) 근접 → trigger_confs == [0.40]"""
    # 두 박스를 명확히 겹치게 배치 (is_dangerously_close 통과)
    person = [100, 100, 200, 300, 0.85, 5]
    mv =     [180, 100, 280, 300, 0.40, 8]
    warnings, _, _ = det.detect_danger([person, mv])
    if 'warning_close_to_machinery' not in warnings:
        pytest.skip("근접 알고리즘이 본 좌표에서 트리거되지 않음 — 좌표 조정 필요")
    confs = warnings['warning_close_to_machinery']['trigger_confs']
    assert confs == [pytest.approx(0.40)]


def test_proximity_far_person_excluded(det):
    """가까운 쌍(0.6,0.5) + 멀리 있는 사람(0.30) → trigger_confs 는 가까운 쌍의 min(0.5)만."""
    near_person = [100, 100, 200, 300, 0.60, 5]
    mv         = [180, 100, 280, 300, 0.50, 8]
    far_person  = [900, 900, 950, 950, 0.30, 5]  # 멀리
    warnings, _, _ = det.detect_danger([near_person, mv, far_person])
    if 'warning_close_to_machinery' not in warnings:
        pytest.skip("좌표 조정 필요")
    confs = warnings['warning_close_to_machinery']['trigger_confs']
    assert confs == [pytest.approx(0.50)]
    assert 0.30 not in [pytest.approx(c) for c in confs]


def test_warning_has_trigger_confs_key(det):
    """모든 발동된 warning은 'trigger_confs' 키를 가져야 한다 (빈 리스트도 허용 X — 발동 시 ≥1)."""
    person = [100, 100, 200, 300, 0.70, 5]
    mv =     [180, 100, 280, 300, 0.65, 8]
    warnings, _, _ = det.detect_danger([person, mv])
    for wk, info in warnings.items():
        assert 'trigger_confs' in info, f"{wk} missing trigger_confs"
        assert isinstance(info['trigger_confs'], list)
        assert len(info['trigger_confs']) >= 1
        assert all(isinstance(c, float) for c in info['trigger_confs'])
```

- [ ] **Step 3.1.2: 실패 확인**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/ai/test_danger_detector_trigger_confs.py -v
```
Expected: FAIL (trigger_confs 키 없음).

### Step 3.2 — `_check_proximity_violations` 수정

- [ ] **Step 3.2.1: `src/ai/danger_detector.py:107-138` 교체**

```python
    def _check_proximity_violations(self, persons, machinery_vehicles, warnings):
        machinery_trigger_confs: list[float] = []
        vehicle_trigger_confs: list[float] = []

        for person in persons:
            for mv in machinery_vehicles:
                label = 'machinery' if mv[5] == 8 else 'vehicle'
                if Utils.is_dangerously_close(person[:4], mv[:4], label):
                    pair_min = float(min(person[4], mv[4]))
                    if label == 'machinery':
                        machinery_trigger_confs.append(pair_min)
                    else:
                        vehicle_trigger_confs.append(pair_min)

        if machinery_trigger_confs:
            if _i18n_available:
                msg = f"{t('warn_machinery_proximity')}: {len(machinery_trigger_confs)}{t('warn_person_count')}"
            else:
                msg = f'중장비 접근 위험: {len(machinery_trigger_confs)}명'
            warnings['warning_close_to_machinery'] = {
                'count': len(machinery_trigger_confs),
                'msg': msg,
                'trigger_confs': machinery_trigger_confs,
            }

        if vehicle_trigger_confs:
            if _i18n_available:
                msg = f"{t('warn_vehicle_proximity')}: {len(vehicle_trigger_confs)}{t('warn_person_count')}"
            else:
                msg = f'차량 접근 위험: {len(vehicle_trigger_confs)}명'
            warnings['warning_close_to_vehicle'] = {
                'count': len(vehicle_trigger_confs),
                'msg': msg,
                'trigger_confs': vehicle_trigger_confs,
            }
```

### Step 3.3 — `_check_cone_restricted_area` 수정

`Utils.calculate_people_in_controlled_area` 가 사람 수만 반환하므로, 영역 안 사람 박스 자체를 얻는 헬퍼가 필요할 수 있다. 우선 본 단계에서는 `datas` 에서 person(class_id==5) 필터 + Shapely 내포 검사로 직접 conf 수집.

- [ ] **Step 3.3.1: `_check_cone_restricted_area` 교체**

```python
    def _check_cone_restricted_area(self, datas, warnings, polygons):
        new_polygons = Utils.detect_polygon_from_cones(datas, self.clusterer)
        if not new_polygons:
            return
        polygons.extend(new_polygons)

        # 사람 박스 중 폴리곤 안에 들어간 것만 conf 수집
        trigger_confs: list[float] = []
        from shapely.geometry import Point as _Point
        for d in datas:
            if d[5] != 5:  # not Person
                continue
            cx = (d[0] + d[2]) / 2.0
            cy = (d[1] + d[3]) / 2.0
            pt = _Point(cx, cy)
            if any(poly.contains(pt) for poly in new_polygons):
                trigger_confs.append(float(d[4]))

        if not trigger_confs:
            return
        if _i18n_available:
            msg = f"{t('warn_restricted_entry')}: {len(trigger_confs)}{t('warn_person_count')}"
        else:
            msg = f'위험구역 진입: {len(trigger_confs)}명'
        warnings['warning_people_in_controlled_area'] = {
            'count': len(trigger_confs),
            'msg': msg,
            'trigger_confs': trigger_confs,
        }
```

> 참고: `Utils.calculate_people_in_controlled_area` 와 카운트가 정확히 일치하는지 검증할 것 (좌표 정의가 다를 수 있음). 일치하지 않으면 Utils 함수의 내부 로직을 같은 기준으로 맞추거나, 본 함수가 count 도 동일 로직으로 산출하므로 `warnings['count'] = len(trigger_confs)` 로 통일하면 됨.

### Step 3.4 — `_check_pole_restricted_area` 수정

- [ ] **Step 3.4.1: 교체**

```python
    def _check_pole_restricted_area(self, datas, warnings, pole_polygons):
        pole_union_poly = Utils.build_utility_pole_union(datas, self.clusterer)
        if pole_union_poly.is_empty:
            return
        pole_polygons.append(pole_union_poly)

        from shapely.geometry import Point as _Point
        trigger_confs: list[float] = []
        for d in datas:
            if d[5] != 5:
                continue
            cx = (d[0] + d[2]) / 2.0
            cy = (d[1] + d[3]) / 2.0
            if pole_union_poly.contains(_Point(cx, cy)):
                trigger_confs.append(float(d[4]))

        if not trigger_confs:
            return
        if _i18n_available:
            msg = f"{t('warn_pole_entry')}: {len(trigger_confs)}{t('warn_person_count')}"
        else:
            msg = f'전신주 위험구역 진입: {len(trigger_confs)}명'
        warnings['warning_people_in_utility_pole_controlled_area'] = {
            'count': len(trigger_confs),
            'msg': msg,
            'trigger_confs': trigger_confs,
        }
```

### Step 3.5 — `_check_machinery_near_utility_pole` 수정

- [ ] **Step 3.5.1: `intersect_count += 1` 부분을 trigger_confs 수집으로 교체**

`src/ai/danger_detector.py:156-211` 의 메서드에서 `intersect_count = 0` → `trigger_confs = []`, `intersect_count += 1` → `trigger_confs.append(float(mv[4]))`, 마지막 if 블록:

```python
        if trigger_confs:
            if _i18n_available:
                msg = f"{t('warn_pole_proximity')}: {len(trigger_confs)}{t('warn_count_unit')}"
            else:
                msg = f'중장비 전신주 근접: {len(trigger_confs)}건'
            warnings['detect_machinery_close_to_pole'] = {
                'count': len(trigger_confs),
                'msg': msg,
                'trigger_confs': trigger_confs,
            }
```

### Step 3.6 — 테스트 통과 + 커밋

- [ ] **Step 3.6.1: 실행**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/ai/test_danger_detector_trigger_confs.py -v
```
Expected: PASS. (테스트가 좌표 의존성으로 skip 되는 경우, `Utils.is_dangerously_close` 좌표를 조정해 실 발동시킬 것)

- [ ] **Step 3.6.2: 커밋**

```bash
git add src/ai/danger_detector.py tests/ai/test_danger_detector_trigger_confs.py
git commit -m "feat(danger): 모든 warning에 trigger_confs 리스트 수집

근접/영역진입/전신주 모든 위험 경고가 어떤 박스가 트리거인지 conf 리스트로
남긴다. 근접 쌍은 쌍별 min(person, mv) 으로 압축.

논문 4.2 PR curve는 트리거 박스의 min conf 만 알면 임계값 sweep 가능."
```

---

## Task 4: HazardDetector `hazard_<class>` 에 trigger_confs

**Files:**
- Modify: `src/ai/hazard_detector.py:305-323` (warnings 빌드 부분)

### Step 4.1 — 교체

- [ ] **Step 4.1.1: `hazard_counts` 수집 루프와 warnings 빌드 부분 교체**

`src/ai/hazard_detector.py:308-323` 부근:

```python
            # (1) Simple Hazard Classes (NO-Hardhat, NO-Mask, NO-Safety Vest)
            hazard_class_confs: dict[str, list[float]] = {}
            for d in detections:
                if d.class_id in self.HAZARD_CLASSES:
                    hazard_class_confs.setdefault(d.class_name, []).append(float(d.confidence))

            for class_name, confs in hazard_class_confs.items():
                if _i18n_available:
                    warn_msg = f"{class_name} {t('warn_not_wearing')}"
                else:
                    warn_msg = f"{class_name} 미착용 감지"
                warnings[f"hazard_{class_name}"] = {
                    'count': len(confs),
                    'msg': warn_msg,
                    'trigger_confs': confs,
                }
```

- [ ] **Step 4.1.2: 기존 hazard_detector 테스트가 있다면 회귀 확인**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/ -v -k hazard
```
Expected: 통과 (기존 테스트는 'count'/'msg' 키만 검사한다고 가정).

- [ ] **Step 4.1.3: 커밋**

```bash
git add src/ai/hazard_detector.py
git commit -m "feat(hazard): hazard_<class> warning에 trigger_confs 리스트 추가"
```

---

## Task 5: AlertHandler 에서 모든 trigger_confs → min 계산 후 저장

**Files:**
- Modify: `src/utils/alert_handler.py` (`_record_combined_history`, `_record_blocked`)
- Test: `tests/utils/test_alert_handler_conf.py`

### Step 5.1 — 실패 테스트 작성

- [ ] **Step 5.1.1: `tests/utils/test_alert_handler_conf.py` 신규**

```python
"""AlertHandler 의 trigger_confs → row min conf 집계 검증."""
from __future__ import annotations
import pytest


def test_extract_row_min_conf_from_warnings():
    from src.utils.alert_handler import _extract_row_min_conf

    confirmed_warning_keys = ['hazard_NO-Hardhat', 'warning_close_to_machinery']
    full_warnings_dict = {
        'hazard_NO-Hardhat': {'count': 2, 'msg': 'x',
                              'trigger_confs': [0.87, 0.62]},
        'warning_close_to_machinery': {'count': 1, 'msg': 'y',
                                       'trigger_confs': [0.40]},  # 쌍 min
        # 다른 미확정 warning 은 포함하지 않음
    }
    # 모든 confirmed 의 trigger_confs 모두 모음 → min
    result = _extract_row_min_conf(confirmed_warning_keys, full_warnings_dict)
    assert result == pytest.approx(0.40)


def test_extract_row_min_conf_only_confirmed():
    """confirmed 가 아닌 경고의 trigger_confs 는 무시되어야 한다."""
    from src.utils.alert_handler import _extract_row_min_conf

    confirmed = ['hazard_NO-Mask']
    all_warnings = {
        'hazard_NO-Mask': {'trigger_confs': [0.75]},
        'hazard_NO-Hardhat': {'trigger_confs': [0.30]},  # 미확정 — 무시
    }
    assert _extract_row_min_conf(confirmed, all_warnings) == pytest.approx(0.75)


def test_extract_row_min_conf_empty_returns_zero():
    from src.utils.alert_handler import _extract_row_min_conf
    assert _extract_row_min_conf([], {}) == 0.0
    assert _extract_row_min_conf(['hazard_x'], {'hazard_x': {}}) == 0.0  # trigger_confs 키 없음
```

- [ ] **Step 5.1.2: 실패 확인**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/utils/test_alert_handler_conf.py -v
```
Expected: FAIL with ImportError.

### Step 5.2 — `_extract_row_min_conf` 헬퍼 추가

- [ ] **Step 5.2.1: `src/utils/alert_handler.py` 상단(약 line 52, `cleanup_old_snapshots` 위)에 추가**

```python
def _extract_row_min_conf(confirmed_warning_keys, all_warnings) -> float:
    """confirmed 된 warn_key 들의 trigger_confs 를 모두 모아 min 반환.

    Detector 가 warnings 각 항목에 'trigger_confs': List[float] 를 채워준다.
    이 알림 row 의 단일 yolo_confidence = min(전체 trigger_confs).
    값이 없으면 0.0.
    """
    confs: list[float] = []
    for wk in confirmed_warning_keys:
        info = all_warnings.get(wk) if isinstance(all_warnings, dict) else None
        if not isinstance(info, dict):
            continue
        tc = info.get('trigger_confs')
        if isinstance(tc, list):
            for c in tc:
                try:
                    confs.append(float(c))
                except (TypeError, ValueError):
                    continue
    return min(confs) if confs else 0.0
```

### Step 5.3 — `_record_combined_history` 에서 호출

`detection_result[1]` 가 detector 가 만든 warnings dict (HazardDetector.predict 의 반환값 구조 참조). VideoThread payload 의 `confirmed_warnings` 는 이미 확정된 키 집합.

- [ ] **Step 5.3.1: `_record_combined_history` 본문 마지막 try 블록 직전에 다음 추가**

```python
        # 논문 4장 분석용: 트리거 박스의 min conf
        all_warnings = {}
        if detection_result and len(detection_result) >= 2:
            all_warnings = detection_result[1] or {}
        confirmed_keys = [wk for wk, _ in valid_msgs]
        row_min_conf = _extract_row_min_conf(confirmed_keys, all_warnings)
```

그리고 그 아래의 두 `get_camera_manager().add_history_entry(...)` 호출 모두에 `yolo_confidence=row_min_conf` kwarg 추가:

```python
                get_camera_manager().add_history_entry(
                    camera_name, full_msg, combined_ids, remarks_text,
                    "정탐", second_reason_text, llm_model,
                    ai_elapsed=total_elapsed, snapshot_path=snapshot_path,
                    prompt_profile=prompt_label_with_fs,
                    yolo_confidence=row_min_conf,
                )
            else:
                get_camera_manager().add_history_entry(
                    camera_name, full_msg, combined_ids, remarks_text,
                    "미실시", "", "",
                    ai_elapsed=0, snapshot_path=snapshot_path,
                    prompt_profile="",
                    yolo_confidence=row_min_conf,
                )
```

### Step 5.4 — `_record_blocked` 에서 호출

`_record_blocked` 는 단일 warn_key 만 받는다.

- [ ] **Step 5.4.1: `_record_blocked` 의 `add_history_entry` 호출 직전에 추가**

```python
            all_warnings = {}
            if detection_result and len(detection_result) >= 2:
                all_warnings = detection_result[1] or {}
            row_min_conf = _extract_row_min_conf([warn_key], all_warnings)

            get_camera_manager().add_history_entry(
                camera_name, blocked_msg, "", remarks_text, judgment, reason, llm_model,
                ai_elapsed=ai_elapsed, snapshot_path=snapshot_path,
                prompt_profile=prompt_label,
                yolo_confidence=row_min_conf,
            )
```

### Step 5.5 — 테스트 통과 + 커밋

- [ ] **Step 5.5.1: 실행**

```
.venv312_cuda/Scripts/python.exe -m pytest tests/utils tests/database tests/ai -v
```
Expected: 전부 PASS.

- [ ] **Step 5.5.2: 커밋**

```bash
git add src/utils/alert_handler.py tests/utils/test_alert_handler_conf.py
git commit -m "feat(alert): 알림 row마다 트리거 박스 min conf를 yolo_confidence 컬럼에 저장

- _extract_row_min_conf: confirmed warning 의 trigger_confs 모두 모아 min
- _record_combined_history (정탐/미실시) + _record_blocked (오탐/오류)
  모두 동일 컬럼에 저장
- 의미: 이 값 이상 임계값에서는 알림이 살아남는다 (PR curve 임계점)
"
```

---

## Task 6: 실 알림 통합 검증

### Step 6.1 — 앱 실행 + 알림 1건 발생

- [ ] **Step 6.1.1: dev 실행 (사용자가 직접 종료할 때까지 유지 — CLAUDE.md 규칙 13)**

```
.venv312_cuda/Scripts/python.exe main.py
```

- [ ] **Step 6.1.2: 알림 1건 이상 발생 시키기**

체크리스트:
- [ ] 카메라 연결, AI 토글 ON
- [ ] 텔레그램/앱 수신자 등록
- [ ] 위험 행위 시뮬레이션 (안전모 미착용 등) → 알림 1건 수신

### Step 6.2 — DB 직접 조회 검증

- [ ] **Step 6.2.1: 사용자 데이터 디렉토리 확인**

```
.venv312_cuda/Scripts/python.exe -c "from src.utils.user_data import get_user_data_dir; print(get_user_data_dir())"
```

- [ ] **Step 6.2.2: 스키마 + 값 동시 확인 (한 줄)**

```
.venv312_cuda/Scripts/python.exe -c "import sqlite3, os; p=os.path.join(r'<USER_DATA_DIR>', 'history.db'); c=sqlite3.connect(p); print('COLS:', [r[1] for r in c.execute('PRAGMA table_info(history)')]); print('---'); [print(r) for r in c.execute('SELECT timestamp, camera_name, second_judgment, yolo_confidence FROM history ORDER BY created_at DESC LIMIT 10')]; c.close()"
```

Expected:
- COLS 출력에 `yolo_confidence` 포함
- 최근 row 의 `yolo_confidence` 가 0 이 아닌 실수 (예: 0.40 ~ 0.95)
- 정탐 + 오탐 양쪽 케이스 모두 값이 채워짐

### Step 6.3 — 재시작 후 마이그레이션 idempotent 확인

- [ ] **Step 6.3.1: 앱 종료(사용자 동의 후) → 재시작 → 에러 없는지 확인**

---

## 완료 후 보고 양식

1. **수정 파일 + 라인 수**
   - `src/history_store.py`, `src/database.py`, `src/ai/hazard_detector.py`,
     `src/ai/danger_detector.py`, `src/utils/alert_handler.py`
2. **단위 테스트 결과** — pytest 출력 `X passed`
3. **실 알림 검증** — Step 6.2.2 출력 (스키마 + 최근 row)
4. **회귀 없음 확인** — 앱 정상 실행/종료

---

## 진행 후 분석 SQL 예시 (논문 4장 작업 참고)

### 4.2 PR curve 데이터

```sql
-- 정탐 vs 오탐 + yolo_confidence
SELECT yolo_confidence, second_judgment
  FROM history
 WHERE yolo_confidence > 0
 ORDER BY yolo_confidence DESC;
-- → CSV로 export 후 옵션 B 분석 스크립트에서 sklearn PrecisionRecallCurve
```

### 4.3 1차 단독 vs 2단계 FAR

```sql
-- 1차 단독 가정: yolo_confidence >= 0.3 모두 알림
SELECT COUNT(*) AS yolo_only_alerts
  FROM history WHERE yolo_confidence >= 0.3;
-- 2단계 시스템: 실제 정탐만
SELECT COUNT(*) AS twostage_alerts
  FROM history WHERE second_judgment = '정탐';
-- 차이 = LLM 이 줄여준 FAR
```

### 4.4 Few-shot 효과

```sql
SELECT prompt_profile, second_judgment, COUNT(*)
  FROM history
 WHERE yolo_confidence > 0
 GROUP BY prompt_profile, second_judgment;
```

---

## 주의 (CLAUDE.md 규칙)

- **규칙 1 (Read 필수):** 각 수정 전 Read 후 Edit.
- **규칙 5 (build_*.spec):** hiddenimports 변경 없음 — spec 수정 금지.
- **규칙 12 (.venv312_cuda):** 모든 python 호출 절대 경로 사용.
- **규칙 13 (백그라운드 앱 자동 kill 금지):** Task 6 실행 앱은 사용자 종료 대기.
- **i18n 영향 없음.**
- **Gist 영향 없음** (사용자 보이는 기능 변경 아님, 버전 bump 불필요).

---

## 후속 작업

옵션 B (`261118_옵션B_분석프로젝트골격생성.md`) — 며칠~몇 주 운영 데이터 누적 후 분석 도구 구축. 본 옵션 A 적용 후 history.db 만 읽어도 4.2/4.3 분석이 가능 (재추론 불필요).
