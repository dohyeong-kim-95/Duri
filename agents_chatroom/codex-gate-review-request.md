# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Storage Layout RFC 0001 Final Review
- Status: Review Requested

## Why This Needs Gate Review

`00-gatekeeping-principles.md` requires Fable review before finalizing storage/export
formats and before implementation touches original-data write paths, backup/export,
auth, or device/session code.

Storage Layout RFC 0001 defines where canonical Message/Photo Logs, original photos,
monthly metadata, generated message views, and rebuildable indexes live under
`DuriStorage/`.

## CEO Decisions Applied

### 1. `metadata.json` Partition

Decision:

- MVP keeps month-level `metadata.json`.
- Example: `DuriStorage/timeline/2026/2026-07/metadata.json`.
- Day-level partitions are Future Work if file size or performance becomes a problem.

Reason:

- MVP is a two-person system.
- MVP supports only Message and Photo.
- Month-level files are simpler for initial implementation and file browsing.

### 2. Server Filesystem Durability

Decision:

- `DuriStorage/` must be stored on persistent server-local storage or a mounted
  persistent volume.
- `DuriStorage/` must not be stored on an ephemeral filesystem.
- Server restart, redeploy, or container recreation must not delete original data.

Required:

- Original photos, Message text, and `metadata.json` are higher-priority preservation
  targets than the DB.
- DB/search indexes are performance caches and are not the original store.
- `metadata.json` is written to a temp file first, verified, then renamed.
- Use fsync or platform-equivalent durability calls where available.
- Keep a separate backup in addition to the primary persistent volume.

## Changed Artifacts

- `docs/rfc/0001-storage-layout.md`
  - Resolved both previous Open Questions.
  - Added month-level partition as MVP decision.
  - Added persistent storage requirements.
  - Added day-level partitioning as rejected for MVP / Future Work.
  - Expanded write integrity strategy with persistent volume, fsync best effort, and
    backup requirements.
- `README.md`
  - Updated current phase to `Storage Layout RFC 0001 Gate Review Requested`.
  - Marked monthly `metadata.json` and persistent disk/volume decisions complete.
  - Shows remaining steps: Fable final review and CEO final approval.
- `CHANGELOG.md`
  - Records Storage Layout RFC 0001 Gate Review Request.
- `agents_chatroom/2026-07-03-storage-layout-rfc-0001-gate-plan.md`
  - Captures the review plan and acceptance boundary for this Gate.

## Review Focus

Please verify:

1. RFC 0001 is consistent with ADR-001 Human Readable First.
2. RFC 0001 is consistent with ADR-007 Storage is Export.
3. RFC 0001 does not reintroduce VaultFolder Curation into MVP.
4. Month-level `metadata.json` is sufficiently justified for MVP.
5. Persistent disk/volume requirements are strong enough to protect original data.
6. Auth operating data remains excluded while participant display identity remains
   included for memory readability.
7. RFC 0001 can proceed to CEO final approval for `Accepted` status.

## Non-Final Boundary

RFC 0001 remains Draft until Fable review and CEO final approval.

This request does not authorize implementation of original-data write paths,
backup/export, auth, or device/session code.

## Verification

Codex ran:

- `rg` checks for unresolved Open Questions and stale partition/durability wording.
  - RFC 0001 no longer has an `Open Questions` section.
  - Remaining Open Questions mention is this request's "resolved previous Open Questions"
    summary.
  - RFC 0001 still has `Status: Draft`, as intended.
- `git diff --check`.
- Manual README and RFC status review.
