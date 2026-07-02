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

- original storage writes
- authentication/device sessions
- photo upload persistence
- metadata write path

### Step 2 — Storage Writer TDD

Status: wait for Fable Gate Acceptance Spec.

Expected test subjects:

- Media writes use temp file, hash/size verification, then atomic rename.
- Monthly `metadata.json` is rewritten via temp file and atomic rename.
- `messages.md` is regenerated from `metadata.json`.
- A failed `messages.md` regeneration does not corrupt canonical storage.
- Orphan media recovery is defined and tested.
- Monthly partition writes are serialized.

### Step 3 — Auth and Session TDD

Status: wait for Fable Gate Acceptance Spec.

Expected test subjects:

- Only two users can register.
- Invite codes are one-time use.
- Invite code and refresh token originals are never stored.
- Device sessions can be revoked independently.
- Data access requires authentication.

### Step 4 — Timeline and Search

Status: can proceed after scaffold, but endpoint access must respect Auth Gate work.

Expected behavior:

- Timeline sorts by `Log.created_at`.
- Search/index data is rebuildable from `DuriStorage/`.
- Metadata exploration remains derived and disposable.

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

Finish the approved scaffold, verify CI, and then wait for Fable Gate Acceptance Spec
before implementing original storage writes or authentication/session behavior.
