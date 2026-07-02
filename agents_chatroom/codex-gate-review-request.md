# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Implementation Step 3 — Auth / Session
- Status: Re-review requested after 10th review C1 fix

## Gate Basis

Applied Spec:

- `agents_chatroom/fable-gate-acceptance-spec.md`
- Version: v1.2
- Section B: Auth / Session (Step 3)
- Items B1-1 through B4-2, including B2-4

10th review condition addressed:

- C1: JWT signing key and stored-hash key domain separation

Prior gate status:

- Step 2 Storage Writer Gate passed in Fable 9th review at commit `9fda760`.
- Step 3 received 10th review Conditional Pass at commit `597849c`.

Process followed:

1. Added the Spec v1.2 B2-4 test first in
   `apps/api/tests/gate_spec/test_auth_session.py`.
2. Confirmed red state before implementation:
   - `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q -k b2_4`
   - Result: `AuthError: refresh session not found`
   - Cause: changing `jwt_secret` changed the refresh token hash lookup key.
3. Separated token signing and stored-hash keys.
4. Kept original storage writes, public photo upload persistence, backup/export,
   and metadata write paths out of this change.
5. Did not weaken, delete, or skip any Fable Spec tests.

## Changed Files

Auth / Session:

- `apps/api/src/duri_api/auth.py`

Gate Spec tests:

- `apps/api/tests/gate_spec/test_auth_session.py`

Fable Spec / review records:

- `agents_chatroom/fable-gate-acceptance-spec.md`
- `agents_chatroom/fable-gate-review.md`

Docs / review request:

- `README.md`
- `CHANGELOG.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `agents_chatroom/codex-gate-review-request.md`

## What Was Implemented

- `AuthService` now requires separate `jwt_secret` and `hash_secret` values.
- `hash_secret` must be non-empty and distinct from `jwt_secret`.
- JWT access token signing continues to use `jwt_secret`.
- Stored hashes use `hash_secret`.
- Stored hashes also include purpose-specific HMAC domains:
  - `invite-code`
  - `refresh-token`
  - `device-fingerprint`
- Signing-key rotation now invalidates old access tokens without invalidating
  existing refresh-token hash lookup.

## Explicit Non-Scope

Not implemented in this request:

- Public message creation endpoint
- Public photo upload endpoint
- Photo upload persistence
- New `DuriStorage/` write paths
- Backup/export implementation
- Password login or external auth provider
- Rate limiting / lockout
- Refresh token rotation
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
- B2-4: signing-key rotation rejects old access tokens but keeps existing refresh
  token hash lookup valid when `hash_secret` is unchanged.
- B3-1: unauthenticated Timeline/photo/search/WebSocket requests are rejected.
- B3-2: expired access token is rejected.
- B3-3: valid refresh session can issue a new access token.
- B4-1: revoked device refresh token is rejected.
- B4-2: revoking one device leaves another same-user device session valid.

## Verification

Red test confirmation:

- `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q -k b2_4`
  - failed before implementation with `AuthError: refresh session not found`.

Post-implementation checks:

- `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q -k b2_4`
  - `1 passed, 12 deselected`
- `.venv/bin/pytest apps/api/tests/gate_spec/test_auth_session.py -q`
  - `13 passed`
- `.venv/bin/pytest apps/api/tests/gate_spec -q`
  - `29 passed`
- `.venv/bin/ruff check apps/api`
  - passed
- `.venv/bin/mypy apps/api/src`
  - passed
- `.venv/bin/pytest apps/api/tests -q`
  - `31 passed`

Full CI:

- `bash scripts/ci.sh`
  - passed
  - frontend tests: `3 passed`
  - backend tests: `31 passed`

## Review Focus Requested

Please verify:

1. B2-4 Spec v1.2 exists as an identifiable `gate_spec` test.
2. B2-4 proves old access token rejection and existing refresh token renewal after
   signing-key rotation.
3. Hashes no longer depend on `jwt_secret`.
4. `jwt_secret` and `hash_secret` cannot be accidentally configured as the same value.
5. Existing B1~B4 tests were not weakened.
6. No original storage writes, photo upload persistence, or backup/export behavior
   slipped into this C1 fix.

## Known Follow-up

Fable noted that a one-time adversarial security review is planned after Step 3.
This request asks only for the Step 3 C1 re-review that is the prerequisite for
that security check.
