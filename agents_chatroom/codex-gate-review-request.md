# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: None currently active
- Status: No active Gate review request

## Current Gate Status

- Step 2 Storage Writer Gate passed in Fable 9th review.
- Step 3 Auth / Session Gate passed in Fable 11th review.
- Spec A(16) + Spec B(13) = 29 gate tests exist and pass in CI.

## Next Work Classification

Can proceed without a new Gate request:

- Further read-only Timeline UI integration
- Further read-only Search UI integration
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

No Fable review is being requested by this file at this moment. Initial read-only
Timeline/Search API connection is implemented. Codex must update this file before
any future Gate 대상 implementation review request.
