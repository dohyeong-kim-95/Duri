# Duri Data Model v0.2

> 이 문서는 [PRD](./PRD.md)의 4.2 ~ 4.5 (Everything is a Log / Timeline First /
> Vault / AI as Reader)를 데이터 모델 수준으로 구체화한다.
>
> **v0.2 변경 요약**: PRD v0.2.2에서 MVP는 Event를 생성하지 않는다
> ([PRD §4.3 Timeline First](./PRD.md#43-timeline-first)). Log는 Event를
> 거치지 않고 곧바로 Timeline에 쌓이며, Vault는 Event가 아닌 Log를 폴더
> 구조로 직접 담는다. Event는 [Future Work](#7-future-work-event)로 이동했다.

---

## 1. Design Principles

1. **Log is the only atomic unit.** Message, Photo, Schedule, Place, Gift, Note,
   Voice 등 모든 기록 타입은 `Log`라는 동일한 개념으로 저장된다.
   새로운 기능은 새로운 Log Type을 추가하는 것으로 확장된다.
2. **Timeline First.** Log는 파생 없이 바로 Timeline에 시간순으로 쌓인다.
   Event 같은 상위 클러스터링 레이어는 MVP에 존재하지 않는다
   ([PRD §4.3](./PRD.md#43-timeline-first)). 대신 미래에 Event Engine이나
   AI가 활용할 수 있도록 Log 생성 시점에 **Metadata를 최대한 축적**한다.
3. **Store simply, read smart.** ([PRD §3](./PRD.md#3-first-principle))
   원본은 단순하고 안정적인 구조로 저장하고, "똑똑함"은 저장이 아니라
   읽기(View 생성) 단계에서만 발휘한다. 저장 스키마 자체를 영리하게
   만들려는 시도를 지양한다.
4. **Vault is folders, not tags.** ([PRD §4.4](./PRD.md#44-vault)) Vault는
   태그 기반 자동 분류 시스템이 아니라, 사람이 이해할 수 있는 폴더
   계층이다. 폴더는 저장 구조인 동시에 탐색 UX다.
5. **AI as Reader.** ([PRD §4.5](./PRD.md#45-ai-as-reader)) AI는 Log/Timeline/
   Vault 원본을 생성하거나 수정하지 않는다. 검색·회상·요약·분류·View 생성만
   수행하며, 그 결과물은 언제든 원본으로부터 재생성 가능해야 한다. AI 산출물은
   원본과 분리된 **derived View**로만 저장한다.
6. **Human Readable First, originals never lost.**
   ([PRD §9](./PRD.md#9-long-term-design-goals)) 모든 엔티티는 앱이 죽어도
   사람이 파일 시스템에서 직접 열어볼 수 있는 형태(JSON/Markdown + 원본
   미디어 파일)로 저장되는 것을 원칙으로 한다. 사진 등 원본 미디어는
   무손실로 별도 보관한다.

---

## 2. Entity Overview

| Entity     | 정의 | 생성 주체 |
|------------|------|-----------|
| `Log`      | 발생한 사실 하나를 표현하는 최소 기록 단위 (원본) | 사용자 행동(직접) 또는 시스템(자동 수집) |
| `Timeline` | 모든 Log를 시간순으로 나열한 뷰/인덱스 | 시스템이 자동 유지 (Log 저장과 동시) |
| `Vault`    | 사람이 만든 폴더 구조로 Log를 다시 담는 탐색 공간 | 사용자(수동) + 시스템 제안(선택) |
| `View`     | AI가 원본으로부터 만들어내는 파생 결과(요약/분류/추천 등) | AI (읽기 전용, 원본과 분리 저장) |

MVP 관계: `Log (N) — (1) Timeline position` (자동), `Log (N) — (N) Vault`
(사용자가 폴더에 담음). Event는 MVP에 존재하지 않는다 (§7 참고).

---

## 3. Log

Log는 모든 기록의 공통 봉투(envelope)다. `type`에 따라 `payload`의 형태만 달라진다.

| Field         | Type                | Description |
|---------------|---------------------|-------------|
| `id`          | ULID                | 정렬 가능한 고유 식별자 |
| `type`        | `LogType`           | Message / Photo / Schedule / Place / Gift / Note / Voice ... |
| `created_at`  | ISO 8601 datetime   | Log가 발생한 시각 (수집 시각이 아닌 원 사건 시각 우선) |
| `ingested_at` | ISO 8601 datetime   | 시스템이 실제로 수집한 시각 |
| `actor`       | `person` reference  | 이 Log를 만든 사람(두 사용자 중 1명) 또는 `system` |
| `source`      | string              | 수집 경로 (예: `chat`, `upload`, `calendar_sync`) |
| `location`    | `GeoPoint?`         | 선택. 위도/경도 + 원문 주소 |
| `media_refs`  | `MediaRef[]`        | 원본 파일 참조 (사진/음성 등). 파일 자체는 별도 스토리지에 원본 보존 |
| `payload`     | `LogType`별 스키마  | 타입별 본문 (아래 3.1 참고) |
| `metadata`    | `object`            | 시스템이 자동 생성하는 부가 정보 (아래 3.2 참고). **원본 payload는 절대 덮어쓰지 않는다** |
| `tags`        | string[]            | 자유 태그 (사용자 입력 또는 metadata에서 승격). Vault 폴더링의 보조 신호일 뿐, 필수 아님 |

Log에는 `event_id`가 없다. Event 레이어가 MVP에 존재하지 않기 때문이다
(구버전 v0.1 모델과의 주요 차이).

### 3.1 Payload by LogType (초기 스케치)

- `Message`: `{ text, thread_id }`
- `Photo`: `{ media_ref, caption?, exif? }`
- `Schedule`: `{ title, start_at, end_at?, place? }`
- `Place`: `{ name, address, geo }`
- `Gift`: `{ title, from, to, memo? }`
- `Note`: `{ text }`
- `Voice`: `{ media_ref, transcript? }`

> 세부 스키마는 각 Log Type이 실제 구현될 때 RFC로 확정한다
> ([docs/rfc](./rfc/README.md) 참고).

### 3.2 Metadata (MVP 핵심 기능)

PRD v0.2.2의 MVP 기능 중 하나가 "Metadata 자동 생성"이다
([PRD §6](./PRD.md#6-mvp-goal)). Metadata는 Log 생성 시점에 최대한
자동으로 채워지는 부가 정보로, **지금 당장 쓰이지 않아도 미래의 Event
Engine/AI가 활용할 수 있도록 축적**하는 것이 목적이다.

예시:

- Photo: EXIF(촬영 시각/GPS/카메라 정보), 이미지 해상도, 파일 해시
- Message: 언급된 장소/인물/날짜 후보(추출 시), 언어
- 공통: 요일, 시간대, 대략적 위치 지명(역지오코딩 결과)

metadata는 **파생 정보이며 신뢰도가 있을 수 있다**. payload(원본 입력)와
분리해서 저장하고, metadata 생성 로직이 바뀌면 언제든 재계산해서
덮어쓸 수 있어야 한다(payload는 절대 재계산 대상이 아님).

---

## 4. Timeline

Timeline은 별도의 저장 엔티티라기보다, 모든 Log를 `created_at` 기준으로
정렬한 **인덱스/뷰**다. Log가 저장되는 순간 자동으로 Timeline에 반영된다.
MVP에서는 Event 같은 중간 집계 레이어 없이 Log가 곧 Timeline의 항목이다.

| Field        | Type       | Description |
|--------------|------------|--------------|
| `log_id`     | `Log.id`   | 참조 |
| `position_at`| datetime   | 정렬 기준 시각 (`Log.created_at`) |

Timeline 조회는 기간(예: "2026년 여름"), 장소, 사람, 타입 등으로 필터링할
수 있어야 한다 ([PRD §5](./PRD.md#5-core-user-experience)).

---

## 5. Vault

Vault는 태그가 아니라 **폴더** 기반이다 ([PRD §4.4](./PRD.md#44-vault)).
Log를 의미 단위로 다시 담아두는 사용자 주도 탐색 공간이며, MVP에서는
자동 분류 정확도를 목표로 하지 않는다 ([PRD §11](./PRD.md#11-non-goals)).

| Field        | Type          | Description |
|--------------|---------------|--------------|
| `id`         | ULID          | 고유 식별자 |
| `name`       | string        | 폴더 이름 (예: "부산 여행", "2026년 여름") |
| `parent_id`  | `Vault.id?`   | 상위 폴더 (계층 구조 허용, 없으면 최상위) |
| `log_ids`    | `Log.id[]`    | 이 폴더에 담긴 Log 목록 (사용자가 직접 담거나, 시스템이 제안) |
| `cover_ref`  | `MediaRef?`   | 대표 이미지 |
| `updated_at` | datetime      | 마지막 갱신 시각 |

하나의 Log는 여러 Vault 폴더에 동시에 속할 수 있다(예: "부산 여행" 폴더와
"2026년 여름" 폴더에 같은 사진이 동시에 들어갈 수 있음) — 파일 시스템의
심볼릭 링크와 유사한 개념으로 이해하면 된다.

---

## 6. View (AI as Reader의 산출물)

AI가 만드는 모든 결과—검색 결과, 요약, 추천, 자동 분류 제안, 그 밖의
다양한 관점—는 `View`로 취급하며, **Log/Timeline/Vault 원본과 분리해서
저장**한다 ([PRD §4.5](./PRD.md#45-ai-as-reader)).

| Field         | Type       | Description |
|---------------|------------|--------------|
| `id`          | ULID       | 고유 식별자 |
| `kind`        | string     | `summary` / `search_result` / `classification_suggestion` / ... |
| `source_log_ids` | `Log.id[]` | 이 View를 생성하는 데 사용된 원본 Log |
| `generated_by`| string     | 생성한 모델/로직 식별자 (재생성 가능성 추적용) |
| `content`     | any        | View 본문 |
| `generated_at`| datetime   | 생성 시각 |

View는 캐시로 취급한다. 삭제되어도 `source_log_ids`로부터 언제든 다시
생성할 수 있어야 하며, 어떤 View도 Log/Timeline/Vault의 원본 필드를
직접 변경해서는 안 된다.

---

## 7. Future Work: Event

Event(Log를 시간·장소·맥락으로 자동 클러스터링한 상위 개념)는 MVP
범위 밖이다 ([PRD §6 Future Work](./PRD.md#6-mvp-goal)). 설계 스케치는
[EVENT_ENGINE.md](./EVENT_ENGINE.md)에 유지하되, 실제 구현은 Timeline +
Vault 경험이 검증된 이후 진행한다. Event가 도입되더라도 원본 Log를
변경하지 않는 파생 레이어로 설계한다는 원칙(§1)은 유지된다.

---

## 8. Storage Layout (원칙 스케치)

Human Readable First 원칙에 따라, DB(색인/캐시)와 별개로 파일시스템에도
사람이 읽을 수 있는 형태로 미러링하는 것을 목표로 한다.

```
storage/
├── logs/
│   └── 2026/07/12/
│       ├── <log_id>.json          # Log 메타데이터 + payload (사람이 읽을 수 있는 JSON)
│       └── media/<log_id>.jpg     # 원본 미디어 (무손실)
├── vaults/
│   └── <vault_path>/              # 폴더 계층 그대로 (예: 부산 여행/)
│       └── index.json             # 소속 log_id 목록
└── views/
    └── <view_kind>/<view_id>.json # AI가 생성한 파생 View (원본과 분리, 언제든 재생성 가능)
```

> 구체적인 파일 포맷/디렉토리 규칙은 아직 확정되지 않았다. 실제 구현 전
> RFC로 논의한다.

---

## 9. Open Questions

- Metadata 자동 생성의 범위를 MVP에서 어디까지 구현할 것인가
  (EXIF만 vs 텍스트 엔티티 추출까지)?
- Vault 폴더를 시스템이 "제안"하는 기능을 MVP에 포함할 것인가, 완전히
  수동으로 시작할 것인가? ([PRD §11](./PRD.md#11-non-goals)는 자동 분류
  "정확도"를 목표하지 않는다고만 명시 — 제안 자체의 포함 여부는 열려 있음)
- Export 포맷(백업/이전용)의 정확한 스펙은? ([PRD §9](./PRD.md#9-long-term-design-goals))

이 문서는 v0.2이며, 실제 구현 과정에서 ADR/RFC를 통해 갱신된다.
