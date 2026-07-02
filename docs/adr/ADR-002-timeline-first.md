# ADR-002: Timeline First (Event Engine은 Future Work)

- Status: Accepted
- Date: 2026-07-02
- Amended: 2026-07-03 — Decision 3 superseded by ADR-008; Decision 4 wording updated from "Timeline + Vault" to "Timeline preservation + Search"
- Related: PRD §4.3 Timeline First, §6 MVP Goal, [EVENT_ENGINE.md](../EVENT_ENGINE.md), [ADR-008](./ADR-008-preservation-first-mvp-vaultfolder-future-work.md)

## Decision

1. MVP에서는 Event를 생성하지 않는다. Log는 Event를 거치지 않고 곧바로 Timeline에 시간순으로 쌓인다.
2. Log 생성 시점에 Metadata를 최대한 자동으로 축적한다. 지금 당장 쓰이지 않아도, 미래의 Event Engine과 AI가 활용할 수 있도록 준비해 둔다.
3. Vault는 Event 기반 자동 분류가 아니라, 사람이 관리하는 폴더 구조로 MVP를 시작한다. **Superseded by [ADR-008](./ADR-008-preservation-first-mvp-vaultfolder-future-work.md): MVP에서 VaultFolder Curation은 제외한다.**
4. Event Engine의 설계는 폐기하지 않고 [EVENT_ENGINE.md](../EVENT_ENGINE.md)에 Future Work로 보존한다. Timeline 보존과 Search 경험이 검증된 이후 착수 여부를 다시 판단한다.

## Context

PRD v0.2.1까지는 Log가 시간·장소·맥락 기준으로 자동 클러스터링되어 Event를 형성하고, Event가 Timeline과 Vault의 기본 단위가 되는 구조였다. 그러나 Event 자동 생성은 클러스터링 정확도를 보장하기 어렵고, 잘못된 Event가 오히려 신뢰를 떨어뜨릴 위험이 있다. PRD v0.2.2는 이를 반영해 철학을 재정의했다: «Duri는 데이터를 똑똑하게 저장하지 않는다. 데이터를 오래 보존하고, 필요할 때 똑똑하게 읽는다.»

## Alternatives Considered

1. **MVP에 Event Engine 포함** — 철학을 가장 완전하게 구현하지만, 클러스터링 알고리즘·threshold 튜닝·merge/split UX까지 필요해 MVP 검증이 크게 지연된다.
2. **수동 Event 생성 기능 제공** — 구현은 쉽지만 "사용자는 기록하지 않는다"는 First Principle에 정면으로 어긋난다.
3. **Timeline 없이 채팅만 우선 출시** — 가장 빠르지만 "추억을 잃지 않는다"는 핵심 가설을 전혀 검증하지 못한다.

## Reason

- MVP의 핵심 가설(«채팅만 했는데 추억을 잃지 않는다»)은 Event 없이도 Log가 시간순으로 안전하게 보존되고 다시 찾을 수 있으면 검증된다.
- 자동화 로직이 원본 구조(Event)를 생성하는 것은 "AI는 원본을 만들거나 수정하지 않는다"(ADR-003)와 긴장 관계에 있다. Event는 잘 쌓인 Log + Metadata에서 나중에 파생하는 것이 일관적이다.
- Event Engine의 품질은 축적된 실데이터가 있어야 오히려 개선하기 쉽다.

## Consequences

- (+) MVP 구현 범위가 크게 줄어들고 출시가 빨라진다.
- (+) 원본 데이터가 항상 단순하고 예측 가능한 구조를 유지한다 — 클러스터링 오류가 원본을 오염시킬 위험이 없다.
- (+) AI 모델/로직이 바뀌어도 Log/Timeline/Vault는 영향받지 않는다.
- (−) MVP 사용자는 "2026-07-12 서울숲 데이트" 같은 자동 요약을 얻지 못하고, 스스로 Vault 폴더를 정리하거나 Timeline을 직접 훑어봐야 한다. **VaultFolder 관련 부분은 [ADR-008](./ADR-008-preservation-first-mvp-vaultfolder-future-work.md)로 대체됐다.**
- Log와 Metadata 스키마([DATA_MODEL.md](../DATA_MODEL.md))는 미래의 Event 생성을 염두에 두고 시간·장소·맥락 정보를 처음부터 보존해야 한다.
- Event Engine 재도입 시점에 대한 판단 기준은 아직 정해지지 않았다 ([EVENT_ENGINE.md §9 Open Questions](../EVENT_ENGINE.md#9-open-questions)).
