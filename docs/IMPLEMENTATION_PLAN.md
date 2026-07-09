# Duri Implementation Plan v0.1

> This is an execution plan, not a new product decision. PRD, DATA_MODEL, ADRs,
> and RFC 0001 remain the source of truth.

## 1. Current State

Design Gates are closed and implementation may begin.

Completed implementation readiness:

- GitHub Actions CI exists.
- `scripts/ci.sh` is the single local/remote CI entrypoint.
- CI currently checks committed whitespace, working/staged whitespace, and local
  Markdown links.

Next implementation work must preserve the Gate structure from
[agents_chatroom/00-gatekeeping-principles.md](../agents_chatroom/00-gatekeeping-principles.md):

- Gate Acceptance Spec tests are written first.
- The tests fail before implementation.
- Implementation follows until CI is green.
- Gate review requests require green CI.

## 2. Gate Boundary

The following code areas are Gate 대상 and must wait for Fable Gate Acceptance
Spec before final implementation:

- Log write, modify, and delete paths
- Original photo write path
- `metadata.json` write integrity
- Backup/export implementation
- Authentication, device registration, and session revocation

The following work can proceed without Fable Gate review, as long as it does not
write original data or implement security behavior:

- CI and repository checks
- App scaffold and developer tooling after stack approval
- Read-only UI shells
- Read-only parsing fixtures
- Documentation and changelog updates

## 3. Recommended Implementation Sequence

### Step 0 — CI Baseline

Status: done.

Future Gate Acceptance Spec tests must be added to `scripts/ci.sh` or a script it
invokes before Gate review.

### Step 1 — App Stack Decision and Scaffold

Status: approved by CEO on 2026-07-03; scaffold in progress.

Approved stack:

- Frontend: TypeScript + Next.js
- Backend: Python + FastAPI
- Realtime: FastAPI WebSocket
- Index DB: SQLite
- Source of Truth: filesystem `DuriStorage/`
- Package managers: npm for frontend, uv or pip for backend
- Deployment: self-hosted Mini PC with persistent disk/volume

Reason:

- ADR-004 requires a responsive web application.
- Next.js is a good fit for mobile-first responsive UI.
- FastAPI keeps realtime, file storage, EXIF/metadata extraction, and future Python
  local processing in a clear backend boundary.
- SQLite is enough for two-person auth/session/search indexes and remains a cache,
  not the source of truth.
- `DuriStorage/` remains the canonical archive.

Rejected for now:

- Native mobile app: conflicts with Responsive Web First.
- External auth/database platform: conflicts with ADR-005 and ownership goals.
- DB as canonical archive: conflicts with ADR-001 and ADR-007.
- Next.js-only backend: would put realtime, file storage, and metadata extraction inside
  the web framework instead of a dedicated backend.

Approved implementation scope:

- frontend/backend scaffold
- dependency installation
- lint/typecheck/test setup
- basic CI
- empty healthcheck endpoints
- WebSocket proof-of-connection test

Not yet approved for implementation:

- authentication/device sessions
- photo upload persistence
- public photo upload endpoint
- backup/export implementation

### Step 2 — Storage Writer TDD

Status: Gate passed in Fable 9th review.

Implemented test subjects:

- Media writes use temp file, hash/size verification, then atomic rename.
- Monthly `metadata.json` is rewritten via temp file and atomic rename.
- `messages.md` is regenerated from `metadata.json`.
- A failed `messages.md` regeneration does not corrupt canonical storage.
- Orphan media recovery is defined and tested.
- Monthly partition writes are serialized.
- Temp media is verified by size/sha256 before atomic rename.
- `created_at` and `ingested_at` are normalized into app timezone before storage.

Notes:

- Spec v1.1 tests live in `apps/api/tests/gate_spec/test_storage_writer.py`.
- Tests are marked with `pytest.mark.gate_spec`.
- Initial red test was confirmed before implementation:
  `ModuleNotFoundError: No module named 'duri_api.storage'`.
- C1/C2 red tests were confirmed after Spec v1.1:
  corrupted temp media did not fail before rename, and mixed timezone logs sorted
  incorrectly before normalization.
- The writer is internal backend code only; it is not yet exposed through public upload
  endpoints.

### Step 3 — Auth and Session TDD

Status: Gate passed in Fable 11th review.

Implemented test subjects:

- Only two users can register.
- Invite codes are one-time use.
- Invite code and refresh token originals are never stored.
- Signing keys and stored-hash keys are separated.
- Device sessions can be revoked independently.
- Data access requires authentication.

Notes:

- Spec v1.2 tests live in `apps/api/tests/gate_spec/test_auth_session.py`.
- Tests are marked with `pytest.mark.gate_spec`.
- Initial red test was confirmed before implementation:
  `ModuleNotFoundError: No module named 'duri_api.auth'`.
- C1 red test was confirmed after Spec v1.2:
  signing-key rotation made the existing refresh token unfindable before key
  domain separation.
- Auth operational state is stored in SQLite outside `DuriStorage/`.
- `DuriStorage/` remains reserved for original Message/Photo canonical storage.
- This step exposes only protected placeholder data endpoints; message/photo upload
  persistence remains gated separately.
- The planned one-time adversarial security review is deferred until registration/login
  HTTP endpoints and upload persistence exist, immediately before first deployment.

### Step 4 — Timeline and Search

Status: initial read-only API and frontend shell implemented.

Expected behavior:

- Timeline sorts by `Log.created_at`.
- Search/index data is rebuildable from `DuriStorage/`.
- Metadata exploration remains derived and disposable.
- This step may connect read-only Timeline/Search APIs to `DuriStorage/` and
  rebuildable indexes.
- Initial implementation reads canonical `metadata.json` files directly from
  `DuriStorage/` and requires AuthService access validation.
- Frontend shell can call the read-only APIs when a future auth flow provides an
  access token.
- Timeline/Search support read-only `period` and `type` filters.
- Timeline Summary exposes read-only period/type counts for exploration controls.
- SQLite Timeline/Search index helpers can rebuild full-log read/search results
  from `DuriStorage/`.

Gate boundary:

- Read-only Timeline/Search connection can proceed without a new Gate request.
- Registration/login/refresh/revocation HTTP auth endpoints remain Gate 대상.
- Photo upload persistence remains Gate 대상.

### Step 5 — Backup Spec and Implementation

Status: blocked on separate backup decisions before implementation.

Required CEO/Fable topics:

- Backup schedule
- Restore test cadence
- Offsite or external copy location
- Encryption key storage
- Whether both users can access the backup key
- Offline key copy policy

## 4. Current Next Action

Continue read-only Timeline/Search integration and UI refinement. Request Fable
review before implementing HTTP auth endpoints, upload persistence, backup/export,
or any new original-data write path.
