# Codex Gate Review Request

- Date: 2026-07-02
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: PRD v0.2.4 Draft / DATA_MODEL v0.3 Draft / ADR-006 Proposed
- Status: Review requested; not final

## Why This File Exists

`00-gatekeeping-principles.md` says Codex cannot finalize decisions that bind future
original data, storage/export format, PRD meaning, or ADR acceptance without Fable
review and CEO final approval.

Codex has prepared drafts, but the following actions are intentionally not finalized:

- Marking `docs/PRD.md` v0.2.4 as final
- Marking `docs/DATA_MODEL.md` v0.3 as final
- Marking `docs/adr/ADR-006-raw-gps-location-metadata.md` as `Accepted`
- Declaring Phase 2 / DATA_MODEL Review complete
- Starting implementation of original data write paths, backup/export, auth, or device/session code

## Drafts Ready for Review

- `README.md`
  - Root dashboard updated for Phase 2 Gate state.
  - Shows CEO Decisions and current pending Gate status.
- `docs/PRD.md`
  - v0.2.4 Draft.
  - Clarifies Schedule and other non-Message/Photo Log Types as Future Work.
- `docs/DATA_MODEL.md`
  - v0.3 Draft.
  - Adds `Message`/`Photo`-only MVP scope.
  - Adds deterministic metadata-only rule.
  - Adds Auth entities: `User`, `InviteCode`, `Device`, `Session`.
  - Adds storage-as-export and DB/search-as-index boundary.
- `docs/adr/ADR-006-raw-gps-location-metadata.md`
  - Proposed ADR for raw GPS-only Location Metadata.
- `docs/WORKFLOW.md`
  - Aligns MVP workflow to Message/Photo and deterministic metadata.
- `docs/EVENT_ENGINE.md`
  - Keeps Event Engine as Future Work and updates references.
- `docs/adr/README.md`
  - Lists ADR-006 as Proposed / Pending Gate Review.
- `CHANGELOG.md`
  - Records PRD v0.2.4 Draft and DATA_MODEL v0.3 Draft as non-final.

## Review Questions for Fable

1. Does PRD v0.2.4 Draft correctly express CEO Decisions without accidentally expanding MVP?
2. Does DATA_MODEL v0.3 Draft satisfy ADR-001 through ADR-005?
3. Does Proposed ADR-006 conflict with Timeline First or AI as Reader?
4. Does storage-as-export over-specify implementation too early, or is it acceptable as a data model invariant?
5. Does the Auth model satisfy ADR-005 without leaking secrets into exportable archive data?
6. Are all references across PRD / DATA_MODEL / WORKFLOW / EVENT_ENGINE / ADR / README / CHANGELOG consistent?

## Plan to Finalize After Review

1. Fable reviews the draft set and writes a response note in `agents_chatroom/`.
2. If Fable rejects or conditionally approves, Codex applies the requested changes and updates this request.
3. If Fable approves, CEO gives final approval.
4. After CEO approval, Codex may:
   - Change PRD v0.2.4 Draft to final PRD v0.2.4.
   - Change DATA_MODEL v0.3 Draft to final DATA_MODEL v0.3.
   - Change ADR-006 from Proposed to Accepted.
   - Mark Phase 2 DATA_MODEL Review complete in README.
   - Proceed to implementation planning for non-Gate code, or open new Gate requests for storage/auth write-path implementation.

## Verification Already Run

- `rg` checks for stale PWA and old DATA_MODEL anchor references.
- `git diff --check`.
- Manual review of changed markdown files.

## Current Non-Final Decision Boundary

The current branch contains reviewable draft artifacts. It must not be treated as
final architecture until Fable review and CEO final approval are complete.
