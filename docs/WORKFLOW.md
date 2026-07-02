# Duri Workflow v0.4

> 이 문서는 사용자의 일상 행동이 어떻게 Log → Timeline → Search로 이어지는지,
> 그리고 이 저장소에서 설계/구현을 진행하는 절차는 무엇인지를 정리한다.
> 데이터 구조는 [DATA_MODEL.md](./DATA_MODEL.md), Future Work인 자동 클러스터링
> 로직은 [EVENT_ENGINE.md](./EVENT_ENGINE.md) 참고.
>
> **v0.4 변경 요약**: CEO Decisions for DATA_MODEL에 따라 MVP Log Type은
> `Message`, `Photo` 두 가지로 제한한다. Metadata는 AI 해석 없이 원본에서
> 기계적으로 추출 가능한 값만 저장하며, VaultFolder Curation은 Future Work로
> 둔다. Responsive Web URL 접근을 MVP 전달 방식으로 둔다.

---

## 1. Product Workflow (MVP: End-to-End)

```
사용자 행동                Duri 시스템 반응
──────────────            ─────────────────────────────
채팅한다           ───▶   Log(Message) 생성 + Metadata 자동 생성
사진을 보낸다       ───▶   Log(Photo) 생성 + 원본 무손실 저장 + Metadata(EXIF 등) 생성 + 자동 백업
사진 Metadata        ───▶   EXIF/GPS/해상도/파일 크기/파일 해시 추출 (해석 없음)
                            │
                            ▼
                     Timeline에 시간순 반영 (즉시, Event 단계 없음)
                            │
                            ▼
                       Metadata 기반 Timeline 탐색
                            │
                            ▼
        기간 / 메시지에 직접 등장한 단어 / 사진 Metadata 등으로 다시 탐색
```

사용자가 명시적으로 수행하는 행동은 **기록을 만드는 행동(채팅, 사진 업로드)**과,
선택적으로 **검색/탐색**뿐이다. Log 저장, Timeline 반영, Metadata 생성,
자동 백업은 시스템이 자동으로 수행한다
([PRD §5](./PRD.md#5-core-user-experience)).

### 1.1 MVP 범위에서의 워크플로우

[PRD §6 MVP Goal](./PRD.md#6-mvp-goal) 기준으로, 초기 구현은 아래 흐름만
검증하면 된다.

1. 1:1 채팅 / 사진 전송 → `Message`, `Photo` Log 생성
2. 원본 사진 저장 + 자동 백업
3. Log 생성 시 기계적으로 추출 가능한 Metadata 생성
4. Timeline에서 시간순 확인 (Event 클러스터링 없이 Log를 그대로 나열)
5. 검색으로 다시 찾기
6. Responsive Web URL로 접근 가능

Event 자동 생성, VaultFolder Curation, AI 자동 분류, 여행/데이트 자동 생성,
AI Memory, 다양한 View 자동 생성은 모두 **Future Work**다
([PRD §6](./PRD.md#6-mvp-goal), [§11 Non Goals](./PRD.md#11-non-goals)).
Metadata 기반 탐색 조건과 결과는 재생성 가능한 View/Index다. AI 자동 정리는
하지 않는다.

### 1.2 실패/예외 처리 원칙

- Metadata 생성이 실패하거나 지연되어도 Log 저장/조회는 항상 가능해야
  한다. Metadata는 원본에서 추출 가능한 파생 정보이므로 재계산 가능해야
  한다. Metadata는 해석하지 않는다.
- 원본 미디어(사진 등)는 어떤 자동화 실패와도 무관하게 항상 보존된다
  ([PRD §9](./PRD.md#9-long-term-design-goals)).
- AI가 생성하는 모든 View(요약/추천/분류 제안 등)는 원본을 변경하지 않고,
  실패해도 Log/Timeline은 영향받지 않는다
  ([PRD §4.5 AI as Reader](./PRD.md#45-ai-as-reader)).

---

## 2. Future Work Workflow (참고용 스케치)

Timeline 보존과 Search 경험이 검증된 이후 다음이 추가될 수 있다
([PRD §6 Future Work](./PRD.md#6-mvp-goal)).

```
Timeline에 축적된 Log + Metadata
        │
        ▼
Event Engine이 자동 클러스터링 (EVENT_ENGINE.md)
        │
        ▼
AI가 Event를 근거로 Vault 폴더 배치를 "제안" (View)
        │
        ▼
사용자가 제안을 확인/수정 후 Vault에 반영
```

이 단계에서도 AI는 Reader로만 동작한다: Event/제안은 모두 Log로부터
재생성 가능한 파생 View이며, 원본 Log를 직접 수정하지 않는다.

---

## 3. Engineering Workflow (이 저장소에서 작업하는 방법)

### 3.1 문서 우선순위

1. **PRD** — 왜(Why)를 정의한다. 모든 결정의 최상위 기준
   ([PRD §3 First Principle](./PRD.md#3-first-principle)).
2. **DATA_MODEL / EVENT_ENGINE** — 무엇(What)을 정의한다. 핵심 구조.
3. **ADR** ([docs/adr](./adr/README.md)) — 이미 내린 아키텍처 결정과 그 이유를 기록.
4. **RFC** ([docs/rfc](./rfc/README.md)) — 아직 확정되지 않은 것을 논의하고 합의하는 절차.

새 기능/구조를 제안할 때는 먼저 PRD의 두 원칙을 통과하는지 확인한다
([PRD §3 First Principle](./PRD.md#3-first-principle)):

> «사용자는 기록하지 않는다. 사용자는 살아간다. Duri는 삶을 기록한다.»
>
> «Duri는 데이터를 똑똑하게 저장하지 않는다. 데이터를 오래 보존하고,
> 필요할 때 똑똑하게 읽는다.»

### 3.2 변경 절차

1. 데이터 모델이나 핵심 로직에 영향을 주는 변경은 먼저 `docs/rfc`에 제안서를
   작성한다.
2. 논의 후 방향이 정해지면, 결정 사항을 `docs/adr`에 짧은 ADR로 기록한다.
3. 구현은 ADR/RFC에서 합의된 범위를 따른다. 구현 중 설계가 바뀌면 문서를
   먼저 갱신한다(문서와 코드가 어긋나지 않도록).

### 3.3 원칙

- Human Readable First: 어떤 저장 포맷을 설계하든, 사람이 파일을 직접 열어
  이해할 수 있는지를 항상 확인한다.
- Store simply, read smart: 저장 스키마를 영리하게 만들려 하지 말고,
  "똑똑함"은 AI가 원본을 읽어 View를 만드는 단계에서만 발휘한다
  ([PRD §3](./PRD.md#3-first-principle)).
- AI as Reader: AI/자동화 로직은 Log/Timeline 원본을 절대 직접 수정하지
  않는다. Future Work로 VaultFolder가 추가되더라도 AI 산출물은 원본으로부터
  재생성 가능한 View로 취급한다
  ([PRD §4.5](./PRD.md#45-ai-as-reader)).
- Non Goals ([PRD §11](./PRD.md#11-non-goals))를 벗어나는 기능(범용 메신저화,
  SNS화, 수익화, MVP 단계의 AI 자동 분류/Event 정확도 추구 등)은 제안하지
  않는다.

이 문서는 v0.4이며, 실제 구현 과정에서 ADR/RFC를 통해 갱신된다.
