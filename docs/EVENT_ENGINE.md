# Duri Event Engine v0.1 (Future Work)

> **Status: Future Work — not part of MVP.**
> [PRD v0.2.5 §4.3 Timeline First](./PRD.md#43-timeline-first)는 MVP에서
> Event를 생성하지 않는다고 명시한다. MVP는 Log를 Timeline에 직접 쌓고,
> 이후 Event Engine이 활용할 수 있도록 [Metadata](./DATA_MODEL.md#4-log)를
> 축적하는 데 집중한다 ([PRD §6 Future Work](./PRD.md#6-mvp-goal)).
>
> 이 문서는 Timeline 보존과 Search 경험이 검증된 이후 착수할 Event Engine의
> 설계 스케치를 미리 남겨두는 문서다. MVP 제외 범위는
> [DATA_MODEL.md §12 Future Work](./DATA_MODEL.md#12-future-work)를 따른다.

---

## 1. Purpose

Event Engine은 사용자가 아무 행동도 추가로 하지 않아도, 쌓인 `Log`들을
시간·장소·맥락 기준으로 묶어 `Event`를 자동으로 만들고 갱신하는 시스템이다.
Timeline First 원칙([PRD §4.3](./PRD.md#43-timeline-first)) 아래 MVP에서는
존재하지 않지만, 향후 도입 시에도 사용자가 Event를 직접 만들지는 않는다.

핵심 성공 기준(향후): 사진 여러 장 + 채팅 + 위치 + 일정이 들어오면, 이를
"2026-07-12 서울숲 데이트" 같은 하나의 Event로 자동 정리한다.

---

## 2. Design Principles

1. **Incremental, not batch-only.** 새 Log가 하나 들어올 때마다 즉시(또는
   짧은 지연 후) 기존 Event에 붙일지, 새 Event를 만들지 판단한다. 다만
   야간 배치로 전체 재클러스터링을 통해 오탐을 보정하는 것도 허용한다.
2. **Reversible.** 자동 생성은 항상 되돌리거나 수정할 수 있어야 한다
   (병합/분리/재배정). Event Engine의 판단은 최종 진실이 아니라 최선의 추정치다.
3. **Explainable.** 왜 이 Log들이 하나의 Event로 묶였는지 `confidence`와
   근거(공유된 시간대, 장소, 참여자 등)를 남긴다.
4. **Extensible by Log Type.** 새로운 Log Type이 추가되어도 Event Engine의
   핵심 파이프라인은 바뀌지 않는다. Log Type별로 "특징 추출기(feature
   extractor)"만 추가하면 된다.

---

## 3. Pipeline

```
        ┌───────────┐
 New Log│  Ingest   │  Log 저장 완료 (source 무관: chat, upload, calendar_sync ...)
        └─────┬─────┘
              ▼
        ┌───────────┐
        │  Feature  │  time / geo / participants / thread / semantic embedding 추출
        │ Extraction│
        └─────┬─────┘
              ▼
        ┌───────────┐
        │ Candidate │  최근 Event 중 결합 가능한 후보 검색
        │  Lookup   │  (시간 윈도우 + 공간 반경 + 참여자 겹침으로 1차 필터)
        └─────┬─────┘
              ▼
        ┌───────────┐
        │  Scoring  │  후보별 결합 점수(confidence) 계산
        └─────┬─────┘
              ▼
        ┌───────────┐
        │  Decide   │  score >= threshold → 기존 Event에 attach
        │           │  score < threshold  → 새 Event 생성
        └─────┬─────┘
              ▼
        ┌───────────┐
        │ Materialize│ Event.title / summary / place / participants 갱신 (필요 시 AI 요약 호출)
        └─────┬─────┘
              ▼
        ┌───────────┐
        │  Timeline  │ Event 정렬 인덱스 갱신
        │  & Views   │ 제안 View 재생성 (신규/변경된 Event만)
        └───────────┘
```

---

## 4. Feature Extraction

Log Type과 무관하게 다음 공통 feature를 뽑는다. 타입별 payload에서
가능한 것만 채운다(없으면 null).

| Feature        | Source |
|----------------|--------|
| `time`         | `Log.created_at` |
| `geo`          | `Photo.metadata.gps` 또는 Future Work의 위치 신호 |
| `participants` | `Log.actor_id` (+ Future Work의 인물 언급 신호) |
| `thread`       | 채팅 스레드 등 명시적 연속성 신호 |
| `embedding`    | 텍스트/이미지 캡션 기반 semantic vector (선택, AI 사용) |

---

## 5. Clustering Rules

1차는 규칙 기반, 2차는 semantic 보정으로 정확도를 올리는 하이브리드 접근을
기본으로 한다.

### 5.1 Hard rules (반드시 만족)

- **Time window**: 후보 Event의 `[started_at, ended_at]`을 기준 마진
  (예: ±3시간, Log Type별로 조정 가능)만큼 확장한 범위 안에 새 Log의 `time`이
  있어야 한다.
- **Participants overlap**: 새 Log의 `actor`가 후보 Event의 `participants`와
  겹치거나, 둘 다뿐인 관계에서는 항상 겹친다고 간주(2인 시스템 특성상 기본 True).

### 5.2 Soft signals (점수에 가산)

- **Geo proximity**: 두 지점 간 거리가 가까울수록 높은 점수 (예: 500m 이내 강한 가산).
- **Thread continuity**: 같은 채팅 스레드/연속 대화 흐름이면 강한 가산.
- **Semantic similarity**: 텍스트/이미지 임베딩 코사인 유사도.
- **Density**: 짧은 시간 안에 여러 Log가 몰려 있으면(사진 다수 업로드 등)
  하나의 Event일 가능성 가산.

### 5.3 Threshold

- `score >= accept_threshold` → 자동 attach, `status = auto`.
- `low_threshold <= score < accept_threshold` → attach하되
  `confidence`를 낮게 기록, 추후 사용자 확인 유도 대상으로 표시.
- `score < low_threshold` → 새 Event 생성.

임계값은 하드코딩하지 않고 설정값으로 분리하며, 실제 값은 구현 시 RFC로 정한다.

---

## 6. Merge / Split / Correction

- **Merge**: 두 Event가 사실 하나의 사건이었던 경우, `status = merged`로
  표시하고 하나로 통합. 병합 이력은 남긴다(추후 재클러스터링 시 재분리 방지 신호로 사용).
- **Split**: 하나의 Event가 서로 다른 사건이 섞인 경우, Log 단위로 재배정.
- **User correction**: 사용자가 수동으로 Log를 다른 Event로 옮기면
  `status = edited`로 표시하고, 이후 자동 재클러스터링에서 이 배정을
  우선순위 높은 제약으로 취급한다(자동 로직이 사용자 결정을 되돌리지 않음).

---

## 7. Event Materialization

Event가 생성/갱신될 때:

- `title`: 대표 장소/날짜/맥락을 조합해 규칙 기반 초안 생성, 필요 시 AI로 다듬음.
- `summary`: AI가 포함된 Log들(사진 캡션, 채팅 요약 등)을 바탕으로 생성.
  실패해도 Event 자체는 유효해야 한다(요약은 optional 필드).
- `place`: 포함 Log 중 대표 좌표 선정(최빈값 또는 클러스터 중심).

AI 호출은 Event Engine의 핵심 클러스터링 로직과 분리되어야 한다
(AI가 느리거나 실패해도 Event 생성/Timeline 갱신은 막히지 않아야 함).

---

## 8. Future VaultFolder Suggestion (연계)

VaultFolder는 MVP가 아니라 Future Work다
([PRD §4.4](./PRD.md#44-search-now-vault-later),
[DATA_MODEL.md §12.1](./DATA_MODEL.md#121-future-work-vaultfolder)).
Event Engine이 도입되더라도 VaultFolder에 Log를 직접 넣는 것은 아니다.
대신 확정된 Event를 근거로 "이 Log들을 OO 폴더에 담는 게 어떤가요?" 같은
**제안(View)**만 만들고, 실제 큐레이션 반영은 사용자가 결정한다
([PRD §4.5 AI as Reader](./PRD.md#45-ai-as-reader)). 상세 알고리즘은 추후
RFC에서 다룬다.

---

## 9. Open Questions

- 초기 threshold/시간 윈도우 기본값은 얼마로 시작할 것인가?
- Semantic embedding을 Event Engine 1차 버전에 포함하는가, 이후 단계로
  미루는가? (규칙 기반만으로도 1차 버전 시작 가능)
- 재클러스터링 배치는 얼마나 자주 도는가?
- Event Engine 착수 시점을 가늠할 기준(Timeline 보존 + Search 경험이
  "충분히 검증됐다"고 판단하는 조건)은 무엇인가?

이 문서는 v0.1이며, 실제 구현 과정에서 ADR/RFC를 통해 갱신된다.
