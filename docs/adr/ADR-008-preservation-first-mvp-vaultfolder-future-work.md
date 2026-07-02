# ADR-008: Preservation-first MVP — VaultFolder Curation is Future Work

- Status: Accepted
- Date: 2026-07-03
- Related: PRD §4.4 Search Now, Vault Later; DATA_MODEL §7 Search and Metadata Exploration; WORKFLOW §1 MVP workflow; ADR-002 Decision 3

## Decision

MVP에서 VaultFolder Curation은 제외한다.

MVP는 다음 범위까지만 한다.

- Message Log 저장
- Photo Log 저장
- Timeline 저장
- Deterministic Metadata 저장
- Search
- Storage-as-Export
- Auth

VaultFolder는 Future Work다. 사용자가 직접 추억 폴더를 만들거나, AI가 큐레이션을
제안하는 기능은 MVP 이후에 다시 설계한다.

Storage Layout RFC 0001의 MVP 구조에도 `vault/folders/`를 포함하지 않는다.

## Context

이전 ADR-002 Decision 3은 "Vault는 Event 기반 자동 분류가 아니라, 사람이
관리하는 폴더 구조로 MVP를 시작한다"고 결정했다. 이후 CEO는 MVP의 목적을
큐레이션이 아니라 다음 문장으로 재정의했다.

> 채팅과 사진을 잃지 않고 시간순으로 보존하는 것

VaultFolder는 좋은 탐색/회상 기능이지만, 사용자가 직접 추억 폴더를 만들고
관리하는 순간 MVP는 보존 시스템에서 큐레이션 제품으로 확장된다. 지금 필요한
검증은 "정리"가 아니라 "잃지 않음"이다.

## Alternatives Considered

1. **Manual VaultFolder Curation을 MVP에 유지** — 사람이 이해하기 쉬운 폴더
   경험을 빠르게 제공할 수 있지만, MVP 범위가 보존에서 큐레이션으로 커진다.
2. **Storage Layout에 `vault/folders/`만 미리 포함** — 나중 확장을 준비하는
   장점은 있지만, Future Work 기능의 Export 의미와 중복 미디어 정책을 너무
   일찍 고정한다.
3. **AI VaultFolder 제안을 MVP에 포함** — Duri의 장기 비전에는 맞지만,
   MVP의 "AI는 해석하지 않는다" 원칙과 충돌하고 품질 검증 부담이 크다.

## Reason

- MVP 핵심 가설은 "채팅과 사진을 시간순으로 보존하면 추억을 잃지 않는다"이다.
- Message와 Photo를 완전하게 저장하고 검색 가능하게 만드는 것이 큐레이션보다
  우선이다.
- VaultFolder를 제외하면 저장 구조가 Timeline 원본과 재생성 가능한 Index/View로
  단순해진다.
- Future Work로 미루면 실제 데이터와 사용 패턴을 본 뒤 VaultFolder가 원본
  큐레이션인지, generated View인지, 별도 Export View인지 다시 결정할 수 있다.

## Consequences

- (+) MVP 범위가 보존, 검색, 인증, Export에 집중된다.
- (+) Storage Layout RFC 0001이 원본 Timeline 저장소 중심으로 단순해진다.
- (+) VaultFolder의 원본성, 중복 미디어, Export UX를 지금 고정하지 않아도 된다.
- (−) MVP 사용자는 직접 만든 추억 폴더를 사용할 수 없다.
- (−) "부산 여행", "2026 여름" 같은 큐레이션 경험은 Search와 Timeline 탐색으로만
  근사한다.

## Directive

VaultFolder를 MVP로 다시 올리려면 새 CEO Decision과 Fable Gate Review가 필요하다.
Future Work로 재도입할 때는 원본 Log/Timeline을 수정하지 않는 방식으로 설계한다.
