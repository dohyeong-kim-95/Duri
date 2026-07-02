# Duri

> «Live together. Log automatically. Remember forever.»

Duri는 우리 둘이 함께 살아가는 모든 순간을 자동으로 기록하고, 구조화하며,
평생 간직할 수 있도록 돕는 **Personal Life System**이다.

메신저를 만드는 것이 목적이 아니다. 채팅, 사진, 일정, 장소, 메모, 선물,
데이트 같은 일상의 기록을 잃지 않도록 시간순으로 보존하고, 미래에 어떤
방식으로든 다시 활용할 수 있는 형태로 남기는 시스템을 만드는 것이 목적이다.

자세한 배경과 원칙은 [docs/PRD.md](docs/PRD.md)를 참고한다.

---

## CEO Dashboard

### Current Phase

**Phase 1 — 완료** (PRD v0.2.3 / ADR-001~005 / CEO Dashboard)

### Current MVP

- Responsive Web
- 1:1 Chat
- Photo Sharing
- Timeline
- Metadata
- Search
- Authentication (Invite Code)
- Device Registration

### Deployment

https://duri.bubblelab.dev

### Current Decisions

| # | Decision | Record |
|---|----------|--------|
| ADR-001 | Human Readable First | [docs/adr/ADR-001](docs/adr/ADR-001-human-readable-first.md) |
| ADR-002 | Timeline First (Event Engine은 Future Work) | [docs/adr/ADR-002](docs/adr/ADR-002-timeline-first.md) |
| ADR-003 | AI generates Views, not Data | [docs/adr/ADR-003](docs/adr/ADR-003-ai-generates-views-not-data.md) |
| ADR-004 | Responsive Web First (CEO Decision #004) | [docs/adr/ADR-004](docs/adr/ADR-004-responsive-web-first.md) |
| ADR-005 | Invite-code based two-person authentication (CEO Decision #005) | [docs/adr/ADR-005](docs/adr/ADR-005-invite-code-two-person-auth.md) |

### Next Phase

Phase 2 — DATA_MODEL.md 확정 (현재 v0.2 초안에 Authentication 엔터티 — User / Device / InviteCode / Session — 반영 필요, [ADR-005](docs/adr/ADR-005-invite-code-two-person-auth.md) 참고)

### Next Gate

DATA_MODEL Review

---

## Core Concept

```
Chat / Photo / Schedule / Place / Note ...
        │  (사용자는 그냥 살아간다)
        ▼
      Log            모든 기록의 최소 단위 (원본, Metadata 자동 축적)
        ▼
   Timeline          Log가 시간 순으로 그대로 이어진 기록 (MVP는 Event 없이 바로 여기로)
        ▼
     Vault           사용자가 직접 정리하는 폴더 기반 탐색 공간
        ▼
      View           AI가 원본을 읽어 만드는 검색/요약/추천 (원본은 절대 수정하지 않음)
```

Duri는 **Timeline First**를 따른다. MVP에서는 Event를 자동 생성하지
않으며([PRD §4.3](docs/PRD.md#43-timeline-first)), Event 자동 클러스터링은
Timeline과 Vault 경험이 검증된 이후의 Future Work다.

## Documents

- [docs/PRD.md](docs/PRD.md) — 제품 정의 (v0.2.3)
- [CHANGELOG.md](CHANGELOG.md) — PRD/주요 결정 변경 이력
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — Log / Timeline / Vault / View 데이터 모델
- [docs/WORKFLOW.md](docs/WORKFLOW.md) — 사용자 행동부터 Vault 정리까지 이어지는 전체 워크플로우
- [docs/EVENT_ENGINE.md](docs/EVENT_ENGINE.md) — (Future Work) Log가 Event로 자동 연결되는 규칙과 파이프라인 스케치
- [docs/adr](docs/adr) — Architecture Decision Records
- [docs/rfc](docs/rfc) — Request for Comments

## Ownership

모든 데이터와 코드는 우리 둘만을 위한 것이다. 공개 서비스나 수익화를
목표로 하지 않는다. 공개 URL로 배포되더라도 인증을 통해 두 사용자만
접근할 수 있다. 자세한 내용은 [docs/PRD.md](docs/PRD.md#10-ownership),
[docs/PRD.md](docs/PRD.md#11-non-goals) 참고.

---

## Phase 1 Gate Completion Criteria

- [x] PRD.md에 Decision #004, #005가 반영되어 있다. (PRD v0.2.3 §7, §8)
- [x] ADR-001 ~ ADR-005가 리포지토리에 기록되어 있다.
- [x] README가 CEO Dashboard 역할을 수행한다.
