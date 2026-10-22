# ADR-009: DuriStorage canonical metadata format (sink format vs RFC 0001)

- Status: Proposed — **결정 전**. CEO 결정이 필요하다.
- Date: 2026-10-22
- Related: [ADR-007 Storage is Export](./ADR-007-storage-is-export.md), [RFC 0001 Storage Layout](../rfc/0001-storage-layout.md), 코드 리뷰 H5

## Decision

아직 결정하지 않았다. 아래 두 안 중 하나를 고른다.

결정 전까지 적용하는 임시 가드(포맷 결정은 아님)는 다음과 같다.

- API reader(`timeline.py`)는 `schema_version`이 없는 `metadata.json`을 건너뛰고 경고 로그를 남긴다.
- Storage writer(`storage.py`)는 `schema_version`이 없는 기존 `metadata.json`에 쓰기를 거부한다(`StorageWriteError`). 파일은 바뀌지 않는다.

## Context

같은 이름의 `DuriStorage/` 트리에 서로 호환되지 않는 두 포맷이 있다.

| 항목 | 운영 중인 Bubblelab sink (`_src/duri-sink`) | 이 레포 RFC 0001 / API |
|---|---|---|
| 최상위 | `{month, logs}` | `{schema_version, period, timezone, participants, logs}` |
| Log 식별 | `seq` | `id` |
| 시각 | `at` (epoch ms) | `created_at` (ISO 8601, offset 포함) |
| 타입 | `"message"` (소문자) | `"Message"`, `"Photo"` |
| 월 파티션 기준 | UTC (KST 00~09시는 전날 달로 들어감) | 앱 타임존 |

실제로 쌓이고 있는 원본은 sink 포맷이다. 이 API를 sink 폴더에 연결하면 가드가 없을 때
`/timeline/summary`가 `period: "None"`을 반환하고, writer는 `KeyError: 'created_at'`으로
그 달의 쓰기를 전부 실패한다. 저장 포맷은 되돌리기 어려운 결정이다(ADR-007).

## Alternatives Considered

### 안 A. sink 포맷을 정본(v1)으로 채택하고, API reader에 어댑터를 둔다

- 이미 쌓인 데이터를 마이그레이션하지 않아도 된다.
- RFC 0001 §3·§4를 sink 포맷 기준으로 개정해야 한다(UTC 파티션 포함).
- API writer도 sink 포맷으로 쓰도록 바꾸거나 쓰기를 sink에만 맡겨야 한다.
- `participants`, `media_refs`, sha256 같은 RFC 필드가 sink 포맷에 없다면 그 정보를 어디에 둘지 다시 정해야 한다.

### 안 B. sink가 RFC 0001 포맷으로 쓰게 한다

- 정본 스펙(RFC 0001, Gate Spec A1~A5)을 그대로 유지한다.
- sink 코드(bubblelab 레포)를 수정해야 하고, 이미 쌓인 sink 데이터는 일회성으로 마이그레이션해야 한다.
- 월 파티션 기준을 UTC에서 앱 타임존으로 바꾸면서 경계에 걸린 Log를 옮겨야 한다.

## Reason

결정 전이다.

## Consequences

결정 전이다. 결정이 나면 이 ADR을 Accepted로 바꾸고, 임시 가드를 제거하거나 어댑터로 대체한다.
