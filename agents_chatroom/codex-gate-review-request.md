# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Code review fixes (storage write path, auth, A2-3 Gate test change)
- Status: Review request open (2026-10-23, see Current Action)

## Current Gate Status

- Step 2 Storage Writer Gate passed in Fable 9th review.
- Step 3 Auth / Session Gate passed in Fable 11th review.
- Spec A(16) + Spec B(13) = 29 gate tests exist and pass in CI.

## Next Work Classification

Can proceed without a new Gate request:

- Further read-only Timeline/Search UI refinement
- Derived index/cache reads or rebuilds from `DuriStorage/`

Requires Gate review before implementation:

- Registration/login/refresh/revocation HTTP auth endpoints
- Public message write endpoint
- Photo upload persistence
- Any new original-data write path
- Backup/export implementation

## Adversarial Security Review Timing

The planned one-time adversarial security review is deferred until after
registration/login HTTP endpoints and upload persistence exist, immediately before
the first deployment.

Starting checklist for that future review:

- Public URL rate limiting / lockout for online guessing
- WebSocket token transport path and proxy/log exposure
- Refresh token rotation
- Duplicate fingerprint / duplicate invite code error handling
- Key rotation and existing-user reauthentication runbook
- Any newly exposed registration/refresh/revocation HTTP endpoint behavior

## Current Action

2026-10-23: 코드 리뷰 수정(H1~H5, M1~M9, L1~L8)에 대한 Fable review 요청이 열려 있다 —
[fable-review-request-review-fixes.md](./fable-review-request-review-fixes.md).

No Fable review is being requested by this file at this moment. Initial read-only
Timeline/Search API connection, frontend shell, read-only filters, and rebuildable
SQLite Timeline/Search index helpers are implemented. Read-only Timeline Summary
facets are also implemented for UI filter options. Codex must update this file
before any future Gate 대상 implementation review request.
