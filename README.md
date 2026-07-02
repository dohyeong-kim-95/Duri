# Duri

> «Live together. Log automatically. Remember forever.»

Duri는 우리 둘이 함께 살아가는 모든 순간을 자동으로 기록하고, 구조화하며, 평생 간직할 수 있도록 돕는 **Personal Life System**이다.

- 제품 정의: [docs/PRD.md](docs/PRD.md) (v0.2.3)
- 변경 이력: [CHANGELOG.md](CHANGELOG.md)
- 아키텍처 결정: [docs/adr/](docs/adr/)

---

## CEO Dashboard

### Current Phase

**Phase 1** — Gate 완료 (본 커밋 기준)

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

Phase 2 — `DATA_MODEL.md` 작성

### Next Gate

DATA_MODEL Review

---

## Phase 1 Gate Completion Criteria

- [x] PRD.md에 Decision #004, #005가 반영되어 있다. (PRD v0.2.3 §7, §8)
- [x] ADR-001 ~ ADR-005가 리포지토리에 기록되어 있다.
- [x] README가 CEO Dashboard 역할을 수행한다.
