# Duri Data Model v0.3 Draft

> 이 문서는 [PRD](./PRD.md)의 Everything is a Log / Timeline First /
> Vault / AI as Reader 원칙과 CEO Decisions for DATA_MODEL을 데이터 모델
> 수준으로 구체화한다.
>
> **Status: Draft — Pending Fable Gate Review.**
>
> **v0.3 Draft 변경 요약**: MVP Log Type을 `Message`, `Photo`로 제한하고,
> Metadata는 AI 해석 없이 원본에서 기계적으로 추출 가능한 값만 저장한다.
> ADR-005에 따라 Authentication 엔터티(`User`, `Device`, `InviteCode`,
> `Session`)를 추가했고, ADR-006에 따라 위치 원본 Metadata는 사진 EXIF의
> GPS 좌표까지만 저장한다.

## 0. Decision Record Scope

이 Draft는 다음 CEO DATA_MODEL 결정을 하나의 Gate 승인 범위로 묶어 기록한다.

- MVP Log Type 제한: `Message`, `Photo`만 지원
- Metadata 추출 전용 원칙: 해석/AI/NLP 없음
- Vault 경계: 사용자 큐레이션 원본과 Metadata Exploration View/Index 분리
- Authentication 데이터 모델: `User`, `InviteCode`, `Device`, `Session`

별도 ADR로 분리한 결정:

- ADR-006 Proposed: Raw GPS Location Metadata
- ADR-007 Proposed: Storage is Export

---

## 1. Design Principles

1. **Log is the only atomic unit.** 모든 기록은 `Log`라는 동일한 봉투로
   저장된다. MVP에서 지원하는 Log Type은 `Message`, `Photo` 두 가지뿐이다.
2. **Metadata extracts, never interprets.** Metadata는 원본에서 기계적으로
   추출 가능한 값만 저장한다. 사람 이름, 장소명, 여행/데이트 분류, AI 요약,
   AI 태깅은 MVP에서 하지 않는다.
3. **Timeline First.** Log는 Event를 거치지 않고 바로 Timeline에 시간순으로
   쌓인다. Event Engine은 Future Work다.
4. **Vault separates curation from exploration.** 사용자가 직접 만든 Vault
   폴더와 그 안의 `log_ids`는 원본 사용자 큐레이션이다. Metadata 기반 탐색
   조건과 검색 결과는 재생성 가능한 View/Index로 취급하며 원본 Vault 엔터티에
   저장하지 않는다.
5. **AI as Reader.** AI는 원본 데이터(Log, Media, Timeline, Vault)를 생성하거나
   수정하지 않는다. AI 산출물은 원본에서 재생성 가능한 `View`로만 취급한다.
6. **Storage is export.** 저장 구조 자체가 Export다. 앱이 없어도 파일 탐색기와
   표준 도구로 Markdown, JSON, 원본 사진 파일을 확인할 수 있어야 한다.
7. **DB is an index, not the source of truth.** DB와 검색 인덱스는 성능을 위한
   파생 캐시다. 원본 데이터는 Human Readable 저장 구조에 보존된다.
8. **Authentication is part of the MVP data model.** 공개 URL 배포를 전제로,
   모든 데이터 접근은 Self-hosted JWT + Invite Code 인증 이후에만 가능하다.

---

## 2. Entity Overview

### 2.1 Memory Archive Entities

| Entity | 정의 | MVP 여부 |
|--------|------|----------|
| `Log` | 발생한 사실 하나를 표현하는 최소 기록 단위 | MVP |
| `MediaRef` | 원본 미디어 파일에 대한 참조와 무결성 정보 | MVP |
| `Timeline` | 모든 Log를 `created_at` 기준으로 정렬한 인덱스/뷰 | MVP |
| `VaultFolder` | 사용자가 직접 만든 폴더와 그 안에 담은 Log 목록 | MVP |
| `View` | AI 또는 시스템이 원본에서 만든 파생 결과 | Future Work 중심 |

### 2.2 Authentication Entities

| Entity | 정의 | MVP 여부 |
|--------|------|----------|
| `User` | Duri를 사용하는 두 사람 중 한 명 | MVP |
| `InviteCode` | 1회용 등록 코드 | MVP |
| `Device` | 사용자가 인증한 기기 | MVP |
| `Session` | 기기별로 폐기 가능한 Refresh Session | MVP |

MVP 관계:

- `User (1) -> (N) Log`
- `Log (N) -> (1) Timeline position`
- `Log (N) -> (N) VaultFolder`
- `User (1) -> (N) Device`
- `Device (1) -> (N) Session`
- `InviteCode (1) -> (0..1) User`

Event는 MVP에 존재하지 않는다.

---

## 3. MVP Log Types

MVP에서 처음부터 기록하는 대상은 두 가지다.

1. `Message`
2. `Photo`

Future Work:

- `Schedule`
- `Place`
- `Gift`
- `Note`
- `Voice`
- 기타 Log Type

MVP는 Log Type을 많이 늘리는 것이 아니라, 가장 자주 발생하는 Message와
Photo를 완전하게 저장하는 것을 우선한다.

---

## 4. Log

Log는 모든 기록의 공통 봉투(envelope)다. `type`에 따라 `payload`만 달라진다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 정렬 가능한 고유 식별자 |
| `type` | `Message` \| `Photo` | MVP Log Type |
| `created_at` | ISO 8601 datetime | 사건이 발생한 시각 |
| `ingested_at` | ISO 8601 datetime | 시스템이 실제로 저장한 시각 |
| `actor_id` | `User.id` \| `system` | Log를 만든 사람 또는 시스템 |
| `source` | string | 수집 경로. 예: `chat`, `photo_upload` |
| `media_refs` | `MediaRef[]` | 원본 미디어 참조 |
| `payload` | object | Log Type별 원본 본문 |
| `metadata` | object | 원본에서 기계적으로 추출한 값 |

Log에는 `event_id`가 없다. Event 레이어가 MVP에 존재하지 않기 때문이다.

### 4.1 Message Payload

```json
{
  "message_id": "01J...",
  "text": "오늘 저녁 뭐 먹을까?",
  "thread_id": "default"
}
```

MVP Message에서 별도 `metadata`에 저장할 값은 없다. CEO Decision의 Message
Metadata(송신자, 생성 시각, Message ID)는 각각 `actor_id`, `created_at`,
`payload.message_id`라는 원본 필드로 저장한다. 같은 값을 `metadata`에 중복
저장하지 않는다.

MVP에서 하지 않는 것:

- 사람 이름 추출
- 장소 이름 추출
- 날짜 의미 해석
- AI 요약
- AI 태깅

### 4.2 Photo Payload

```json
{
  "media_ref_id": "01J...",
  "caption": null
}
```

MVP Photo Metadata:

| Field | Description |
|-------|-------------|
| `captured_at` | EXIF 촬영 시각. 없으면 null |
| `gps` | EXIF GPS 좌표. 없으면 null |
| `exif` | 원본 EXIF에서 보존 가능한 값 |
| `width` | 이미지 너비 |
| `height` | 이미지 높이 |
| `size_bytes` | 파일 크기 |
| `sha256` | 파일 해시 |

MVP에서 하지 않는 것:

- GPS -> 장소명 변환
- GPS -> 행정구역 변환
- AI 장소 추론
- 자동 여행/데이트 분류

위치 원본 Metadata는 사진 EXIF의 GPS 좌표만 저장한다. 의미는 나중에
파생 View나 사용자가 정의한 Alias로 부여한다.

---

## 5. MediaRef

`MediaRef`는 원본 미디어 파일을 잃지 않기 위한 참조 엔터티다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `log_id` | `Log.id` | 이 미디어를 포함한 Log |
| `original_filename` | string? | 업로드 시 원래 파일명 |
| `mime_type` | string | 예: `image/jpeg` |
| `storage_path` | string | Export 저장 구조 안의 상대 경로 |
| `size_bytes` | integer | 파일 크기 |
| `sha256` | string | 원본 무결성 검증용 해시 |
| `created_at` | datetime | 저장 시각 |

사진 원본은 변환하거나 압축하지 않고 그대로 보존한다. 썸네일이나 최적화 이미지는
파생 캐시로만 취급한다.

---

## 6. Timeline

Timeline은 별도의 원본 엔터티라기보다, 모든 Log를 `created_at` 기준으로
정렬한 인덱스/뷰다. Log가 저장되는 순간 자동으로 Timeline에 반영된다.

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | `Log.id` | 참조 |
| `position_at` | datetime | 정렬 기준 시각 |

Timeline 조회는 기간, 사람, 타입, 사진 GPS 존재 여부 같은 Metadata 조건으로
필터링할 수 있어야 한다.

---

## 7. VaultFolder and Metadata Exploration

MVP의 Vault는 두 층을 분리한다.

1. **VaultFolder**: 사용자가 직접 만든 폴더와 그 안에 담은 Log 목록. 원본
   사용자 큐레이션이다.
2. **Metadata Exploration**: 기간, 타입, GPS 존재 여부 같은 조건으로 Timeline과
   Log를 탐색하는 재생성 가능한 View/Index다. 원본 VaultFolder에 저장하지 않는다.

자동 Event 생성이나 AI 분류는 하지 않는다.

VaultFolder는 Export 저장 구조이기도 하다. 사용자는 Duri 앱이 없어도 폴더와
파일을 열어 데이터를 확인할 수 있어야 한다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `path` | string | 사람이 읽을 수 있는 폴더 경로 |
| `name` | string | 표시 이름 |
| `parent_id` | `VaultFolder.id?` | 상위 폴더 |
| `log_ids` | `Log.id[]` | 사용자가 이 폴더에 직접 담은 Log 목록 |
| `cover_ref` | `MediaRef?` | 대표 이미지 |
| `updated_at` | datetime | 마지막 갱신 시각 |

`metadata_filter`나 조건 기반 검색 결과는 `VaultFolder` 필드가 아니다.
저장된 검색, 스마트 폴더, AI 제안이 나중에 도입되더라도 실제 원본
VaultFolder를 직접 변경하지 않고 `View` 또는 재생성 가능한 인덱스로만 제공한다.

---

## 8. View

`View`는 원본에서 재생성 가능한 파생 결과다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `kind` | string | `metadata_exploration`, `search_result`, `location_alias`, `summary`, `classification_suggestion` 등 |
| `source_log_ids` | `Log.id[]` | View 생성에 사용된 원본 Log |
| `generated_by` | string | 생성한 로직 또는 모델 |
| `content` | any | View 본문 |
| `generated_at` | datetime | 생성 시각 |

MVP에서 AI View는 필수 기능이 아니다. 특히 다음은 Future Work다.

- AI 요약
- AI 태깅
- AI 자동 분류
- Location Alias 자동 생성
- 여행/데이트 자동 생성

`metadata_exploration` View는 AI 없이도 생성될 수 있다. 예를 들어 기간, 타입,
GPS 존재 여부 같은 조건으로 Timeline을 필터링한 결과는 원본 VaultFolder가
아니라 재생성 가능한 View/Index다.

### 8.1 Future Work: Location Alias

사용자는 나중에 직접 권역 Alias를 정의할 수 있다.

예:

- 서울숲
- 청주 집 근처
- 부산 여행
- 우리 단골 카페

Alias는 원본 Metadata가 아니라 `View` 계층으로 관리한다.

원본은 GPS 좌표만 저장하고, 의미는 나중에 부여한다.

---

## 9. Authentication

MVP는 공개 URL에서 제공되므로 Authentication은 필수다. 인증 방식은
Self-hosted JWT + Invite Code다. 외부 Auth Provider는 사용하지 않는다.

### 9.1 User

등록 가능한 사용자는 정확히 2명이다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `slot` | `1` \| `2` | 두 사용자 중 어느 슬롯인지 |
| `display_name` | string | 표시 이름 |
| `created_at` | datetime | 등록 시각 |
| `status` | `active` \| `disabled` | 사용자 상태 |

### 9.2 InviteCode

Invite Code는 1회 사용 후 만료된다. 원문 코드는 저장하지 않고 해시만 저장한다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `code_hash` | string | 초대 코드 해시 |
| `intended_slot` | `1` \| `2` | 등록 대상 사용자 슬롯 |
| `created_at` | datetime | 생성 시각 |
| `expires_at` | datetime? | 만료 시각 |
| `consumed_at` | datetime? | 사용 시각 |
| `consumed_by_user_id` | `User.id?` | 등록된 사용자 |

### 9.3 Device

기기는 사용자별로 기억되며, 서버에서 개별 폐기할 수 있어야 한다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `user_id` | `User.id` | 소유 사용자 |
| `label` | string? | 사용자가 알아볼 수 있는 이름 |
| `fingerprint_hash` | string? | 기기 식별 보조값. 원문 fingerprint는 저장하지 않음 |
| `created_at` | datetime | 등록 시각 |
| `last_seen_at` | datetime? | 마지막 사용 시각 |
| `revoked_at` | datetime? | 폐기 시각 |

### 9.4 Session

Access Token은 짧게 살고, 장기 로그인은 기기별 Refresh Session으로 관리한다.
서버는 Refresh Session을 폐기해 특정 기기만 로그아웃시킬 수 있어야 한다.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | 고유 식별자 |
| `user_id` | `User.id` | 사용자 |
| `device_id` | `Device.id` | 인증된 기기 |
| `refresh_token_hash` | string | Refresh Token 해시 |
| `issued_at` | datetime | 발급 시각 |
| `expires_at` | datetime? | 만료 시각 |
| `last_used_at` | datetime? | 마지막 사용 시각 |
| `revoked_at` | datetime? | 폐기 시각 |

보안 원칙:

- Invite Code와 Refresh Token 원문은 저장하지 않는다.
- Access JWT는 짧게 유지하고 서버 저장 원본으로 취급하지 않는다.
- 모든 데이터 접근은 인증 이후에만 가능하다.

---

## 10. Storage Layout / Export v1

저장 구조 자체가 Export다. DB 없이도 사람이 폴더와 파일을 열어 데이터를
확인할 수 있어야 한다.

예시:

```text
Vault/
  2026/
    2026-07/
      photos/
        2026-07-12T19-30-22_01J...jpg
      metadata.json
      messages.md
```

원칙:

- `metadata.json`은 canonical source다. Log ID, Message ID, Message text,
  MediaRef, EXIF, 해시, Timeline 정렬 정보를 포함하는 구조화된 원본 기록이다.
- `messages.md`는 사람이 읽기 쉬운 월별 대화 기록이며, `metadata.json`에서
  재생성 가능한 파생 파일이다. 두 파일이 충돌하면 `metadata.json`이 우선한다.
- `photos/`는 원본 사진 파일을 무손실로 보존한다.
- DB와 검색 인덱스는 이 구조에서 다시 만들 수 있어야 한다.
- Auth 운영 데이터(`InviteCode`, `Session`, token hash 포함)는 Export에서
  전면 제외하고 별도 보안 저장소에 보관한다. Export에 포함할 수 있는 인증
  관련 정보는 사용자가 이해할 수 있는 `User`/`Device` 표시 목록 정도로 제한한다.

---

## 11. Search and Indexes

검색은 MVP 필수 기능이지만, 검색 인덱스는 원본이 아니다.

허용되는 인덱스:

- 메시지 전문 검색 인덱스
- Timeline 정렬 인덱스
- Photo Metadata 인덱스
- GPS 존재 여부 / 기간 / 사용자 필터 인덱스

모든 인덱스는 Markdown, JSON, 원본 사진 파일에서 재생성 가능해야 한다.

---

## 12. Future Work

다음은 MVP에 포함하지 않는다.

- Event Engine
- AI 자동 분류
- 여행/데이트 자동 생성
- AI Memory
- 다양한 AI View 자동 생성
- GPS -> 장소명 변환
- Location Alias
- Schedule / Place / Gift / Note / Voice Log Type

---

## 13. Gate Review Checklist

DATA_MODEL Review에서 확인할 항목:

- [x] MVP Log Type이 `Message`, `Photo`로 제한되어 있다.
- [x] Metadata가 "추출"만 하고 "해석"하지 않는다는 원칙이 명시되어 있다.
- [x] Auth 엔터티 `User`, `InviteCode`, `Device`, `Session`이 포함되어 있다.
- [x] 기기별 Session 폐기 모델이 표현되어 있다.
- [x] 저장 구조 자체가 Export라는 원칙이 명시되어 있다.
- [x] DB/Search Index가 파생 캐시임이 명시되어 있다.
- [x] Location 원본 Metadata가 GPS 좌표까지만임이 명시되어 있다.
- [x] Event Engine과 AI 자동 정리는 Future Work로 남아 있다.
- [x] VaultFolder 원본과 Metadata Exploration/View가 분리되어 있다.
- [x] Message text의 canonical source가 `metadata.json`임이 명시되어 있다.
- [x] Auth 운영 데이터와 token hash가 Export에서 제외되어 있다.

이 문서는 v0.3 Draft이며, Fable Gate Review와 CEO 최종 승인 전까지 확정본이
아니다. 구현 중 세부 스키마가 바뀌면 RFC/ADR을 통해 갱신한다.
