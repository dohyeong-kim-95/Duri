# 0002. DuriStorage canonical metadata format (sink format vs RFC 0001)

- Status: Draft — **결정 전**. CEO 결정이 필요하다.
- Date: 2026-10-22 (2026-10-23: ADR-009 Proposed에서 RFC로 이동)
- Related: [ADR-007 Storage is Export](../adr/ADR-007-storage-is-export.md), [RFC 0001 Storage Layout](./0001-storage-layout.md), 코드 리뷰 H5

> 처음에는 `docs/adr/ADR-009`(Proposed)로 작성했다. [ADR README](../adr/README.md) 규칙상
> 아직 합의되지 않은 제안은 RFC에 먼저 둔다. 그래서 RFC로 옮겼다. ADR-009 번호는 재사용하지 않는다.
> 결정이 나면 그 결과를 새 ADR로 요약한다.

## Summary

같은 이름의 `DuriStorage/` 트리에 서로 호환되지 않는 두 `metadata.json` 포맷이 있다.
둘 중 어느 쪽을 정본으로 할지 정해야 한다. 이 RFC는 선택지만 정리하고 결정하지 않는다.

## Motivation

ADR-007(Storage is Export)과 "앱이 없어도 읽을 수 있다"는 원칙은 정본 포맷이 하나일 때만
성립한다. 저장 포맷은 미래 데이터 전체를 구속하므로 되돌리기 어렵다
([Gate ④](../../agents_chatroom/00-gatekeeping-principles.md)).

| 항목 | 운영 중인 Bubblelab sink (`_src/duri-sink`) | 이 레포 RFC 0001 / API |
|---|---|---|
| 최상위 | `{month, logs}` | `{schema_version, period, timezone, participants, logs}` |
| Log 식별 | `seq` | `id` |
| 시각 | `at` (epoch ms) | `created_at` (ISO 8601, offset 포함) |
| 타입 | `"message"` (소문자) | `"Message"`, `"Photo"` |
| 월 파티션 기준 | UTC (KST 00~09시는 전날 달로 들어감) | 앱 타임존 |

실제로 쌓이고 있는 원본은 sink 포맷이다. 가드가 없으면 이 API를 sink 폴더에 연결했을 때
`/timeline/summary`가 `period: "None"`을 반환하고, writer는 `KeyError: 'created_at'`으로
그 달의 쓰기를 전부 실패한다.

### 결정 전까지의 임시 가드 (포맷 결정 아님)

- API reader(`timeline.py`)는 `schema_version`이 지원 버전(현재 `1`, 정수)이 아닌
  `metadata.json`을 건너뛰고 경고 로그를 남긴다.
- Storage writer(`storage.py`)는 그런 기존 `metadata.json`에 쓰기를 거부한다(`StorageWriteError`).
  파일은 바뀌지 않는다.
- 결과: 이 API를 지금의 sink 폴더에 연결하면 Timeline이 **빈 화면**으로 보이고, 흔적은
  서버 로그의 경고뿐이다.

## Proposal

아직 없다. 아래 두 안 중 하나를 고른다.

## Alternatives Considered

### 안 A. sink 포맷을 정본(v1)으로 채택하고, API reader에 어댑터를 둔다

- 이미 쌓인 데이터를 마이그레이션하지 않아도 된다.
- RFC 0001 §3·§4를 sink 포맷 기준으로 개정해야 한다(UTC 파티션 포함).
- API writer도 sink 포맷으로 쓰도록 바꾸거나, 쓰기를 sink에만 맡겨야 한다.
- `participants`, `media_refs`, sha256 같은 RFC 필드가 sink 포맷에 없다면 그 정보를 어디에 둘지 다시 정해야 한다.

### 안 B. sink가 RFC 0001 포맷으로 쓰게 한다

- 정본 스펙(RFC 0001, Gate Spec A1~A5)을 그대로 유지한다.
- sink 코드(bubblelab 레포)를 수정해야 하고, 이미 쌓인 sink 데이터는 일회성으로 마이그레이션해야 한다.
- 월 파티션 기준을 UTC에서 앱 타임존으로 바꾸면서 경계에 걸린 Log를 옮겨야 한다.

## Open Questions

- 안 A와 안 B 중 무엇을 고를지 (CEO 결정).
- 결정 후 임시 가드를 없앨지, 어댑터로 바꿀지.
- sink 사진 파일명 `<UTC stamp>_<seq 12자리>.ext`가 orphan 복구 정규식에 매치된다. 가드를 풀 때 함께 확인해야 한다.
