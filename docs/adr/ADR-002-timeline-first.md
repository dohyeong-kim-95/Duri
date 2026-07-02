# ADR-002: Timeline First (Event Engine은 Future Work)

- Status: Accepted
- Date: 2026-07-02
- Related: PRD §4.3 Logs become Events, §6 MVP Goal

## Decision

MVP는 **Timeline 저장과 Metadata 자동 생성**까지만 구현한다.

Log를 자동으로 묶어 Event를 생성하는 **Event Engine은 Future Work**로 미루고, MVP 범위에서 제외한다.

## Context

PRD의 장기 구조는 Log → Event → Timeline → Vault이다. 그러나 MVP가 검증해야 하는 경험은 «채팅만 했는데 추억이 자동으로 정리된다»이며, 이는 Log가 시간순 Timeline으로 쌓이고 메타데이터가 자동으로 붙는 것만으로도 충분히 검증 가능하다. Event 자동 생성은 시간·장소·맥락 추론이 필요한 고난도 기능으로, MVP에 포함하면 범위가 크게 늘어난다.

## Alternatives Considered

1. **MVP에 Event Engine 포함** — 철학을 가장 완전하게 구현하지만, 추론 품질 확보에 시간이 오래 걸리고 MVP 검증이 지연된다.
2. **수동 Event 생성 기능 제공** — 구현은 쉽지만 "사용자는 기록하지 않는다"는 First Principle에 정면으로 어긋난다.
3. **Timeline 없이 채팅만 우선 출시** — 가장 빠르지만 "자동으로 정리된다"는 핵심 가설을 전혀 검증하지 못한다.

## Reason

- Event는 잘 쌓인 Log + Metadata에서 나중에 얼마든지 파생 가능하다(ADR-003과 일관).
- MVP 범위를 줄여 핵심 가설 검증에 집중한다.
- Event Engine의 품질은 축적된 데이터가 있어야 오히려 개선하기 쉽다.

## Consequences

- (+) MVP 범위가 명확해지고 출시가 빨라진다.
- (+) Event 생성 로직을 실데이터 기반으로 나중에 설계할 수 있다.
- (−) MVP에서는 시간순 Timeline만 제공되며, "서울숲 데이트" 같은 의미 단위 묶음은 아직 없다.
- Log와 Metadata 스키마(DATA_MODEL.md)는 **미래의 Event 생성을 염두에 두고** 시간·장소·맥락 정보를 처음부터 보존해야 한다.
