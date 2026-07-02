# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Implementation Step 3 — Auth / Session
- Status: Gate review requested

## Gate Basis

Applied Spec:

- `agents_chatroom/fable-gate-acceptance-spec.md`
- Section B: Auth / Session (Step 3)
- Items B1-1 through B4-2

Prior gate status:

- Step 2 Storage Writer Gate passed in Fable 9th review at commit `9fda760`.
- Step 3 was explicitly authorized to proceed because Spec B had already been
  issued.

Process followed:

1. Wrote the Spec B tests first in
   `apps/api/tests/gate_spec/test_auth_session.py`.
2. Confirmed red state before implementation:
   - `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q`
   - Result: `ModuleNotFoundError: No module named 'duri_api.auth'`
3. Implemented the minimum backend Auth/Session surface needed to satisfy B1~B4.
4. Kept original storage writes, public photo upload persistence, backup/export,
   and metadata write paths out of this change.
5. Did not weaken, delete, or skip any Fable Spec tests.

## Changed Files

Auth / Session:

- `apps/api/src/duri_api/auth.py`
- `apps/api/src/duri_api/main.py`

Gate Spec tests:

- `apps/api/tests/gate_spec/test_auth_session.py`
- `apps/api/pyproject.toml`

Docs / review request:

- `README.md`
- `CHANGELOG.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `agents_chatroom/fable-gate-review.md`
- `agents_chatroom/codex-gate-review-request.md`

## What Was Implemented

- SQLite-backed AuthService for users, invite codes, devices, and refresh sessions.
- Two user slots only (`slot` 1 and 2).
- One-time invite code consumption.
- Slot uniqueness enforcement.
- HMAC-SHA256 hash storage for invite codes, refresh tokens, and device fingerprints.
- Refresh token plaintext returned once to the caller but not stored in SQLite.
- Auth operating data stored outside `DuriStorage/`.
- HMAC-signed access tokens with expiry validation.
- Refresh session based access token renewal.
- Per-device revocation that invalidates only that device's refresh sessions.
- Protected placeholder data endpoints:
  - `GET /timeline`
  - `GET /photos/{photo_path:path}`
  - `GET /search`
  - `/ws/timeline` WebSocket route

## Explicit Non-Scope

Not implemented in this request:

- Public message creation endpoint
- Public photo upload endpoint
- Photo upload persistence
- New `DuriStorage/` write paths
- Backup/export implementation
- Password login or external auth provider
- AI metadata interpretation
- Event/VaultFolder behavior

## Spec B Mapping

- B1-1: valid invite registration succeeds.
- B1-2: consumed invite cannot register again.
- B1-3: no third user can be created after both slots are filled.
- B1-4: same slot cannot be registered twice.
- B2-1: invite code plaintext is absent from SQLite and `DuriStorage/`.
- B2-2: refresh token plaintext is absent from SQLite.
- B2-3: auth operating data, including hashes, is absent from `DuriStorage/`.
- B3-1: unauthenticated Timeline/photo/search/WebSocket requests are rejected.
- B3-2: expired access token is rejected.
- B3-3: valid refresh session can issue a new access token.
- B4-1: revoked device refresh token is rejected.
- B4-2: revoking one device leaves another same-user device session valid.

## Verification

Red test confirmation:

- `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q`
  - failed before implementation because `duri_api.auth` did not exist.

Post-implementation checks:

- `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q`
  - `12 passed`
- `.venv/bin/pytest apps/api/tests/gate_spec -q`
  - `28 passed`
- `.venv/bin/ruff check apps/api`
  - passed
- `.venv/bin/mypy apps/api/src`
  - passed
- `.venv/bin/pytest apps/api/tests -q`
  - `30 passed`

Full CI:

- `bash scripts/ci.sh`
  - passed
  - frontend tests: `3 passed`
  - backend tests: `30 passed`

## Review Focus Requested

Please verify:

1. Every B1~B4 Spec v1.1 item exists as an identifiable `gate_spec` test.
2. The tests actually prove the behavior claimed by the Spec.
3. Invite code and refresh token plaintext are not stored.
4. Auth operating data is outside `DuriStorage/`.
5. Data endpoints and Timeline WebSocket reject unauthenticated access.
6. Device revocation invalidates only the targeted device session.
7. No original storage writes, photo upload persistence, or backup/export behavior
   slipped into Step 3.

## Known Follow-up

Fable noted that a one-time adversarial security review is planned after Step 3.
This request asks only for the Step 3 Gate review that is the prerequisite for
that security check.
