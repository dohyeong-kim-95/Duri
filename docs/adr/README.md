# Architecture Decision Records (ADR)

ADR은 Duri의 아키텍처/설계와 관련해 **이미 내려진 결정**과 그 배경, 대안,
결과를 기록하는 문서다. "왜 이렇게 만들었는가"를 나중에 다시 찾아볼 수
있게 하는 것이 목적이다.

- 논의 중이거나 아직 합의되지 않은 제안은 [docs/rfc](../rfc/README.md)에 먼저 작성한다.
- RFC가 합의되어 실제 결정으로 확정되면, 그 결정을 요약한 ADR을 이곳에 남긴다.

## 파일 규칙

- 파일명: `ADR-NNN-short-title.md` (예: `ADR-001-human-readable-first.md`)
- 번호는 순차 증가하며 재사용하지 않는다.
- 상태(status)가 바뀌어도 과거 ADR은 삭제하지 않고 `Superseded by ADR-NNN`으로 표시한다.

## 템플릿

```markdown
# ADR-NNN: <결정 제목>

- Status: Proposed | Accepted | Deprecated | Superseded by ADR-NNN
- Date: YYYY-MM-DD
- Related: 관련 PRD 섹션, 문서, ADR

## Decision

무엇을 하기로 했는가.

## Context

이 결정이 필요했던 배경/문제.

## Alternatives Considered

검토했지만 채택하지 않은 대안과 그 이유.

## Reason

대안 대신 이 결정을 선택한 이유.

## Consequences

이 결정으로 얻는 이점과 감수해야 하는 트레이드오프.
```

## Index

| No. | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./ADR-001-human-readable-first.md) | Human Readable First | Accepted | 2026-07-02 |
| [ADR-002](./ADR-002-timeline-first.md) | Timeline First (Event Engine은 Future Work) | Accepted | 2026-07-02 |
| [ADR-003](./ADR-003-ai-generates-views-not-data.md) | AI generates Views, not Data | Accepted | 2026-07-02 |
| [ADR-004](./ADR-004-responsive-web-first.md) | Responsive Web First (CEO Decision #004) | Accepted | 2026-07-02 |
| [ADR-005](./ADR-005-invite-code-two-person-auth.md) | Invite-code based two-person authentication (CEO Decision #005) | Accepted | 2026-07-02 |
| [ADR-006](./ADR-006-raw-gps-location-metadata.md) | Raw GPS Location Metadata (CEO Decision #006) | Proposed — Pending Gate Review | 2026-07-02 |
| [ADR-007](./ADR-007-storage-is-export.md) | Storage is Export (CEO DATA_MODEL decision) | Proposed — Pending Gate Review | 2026-07-02 |
