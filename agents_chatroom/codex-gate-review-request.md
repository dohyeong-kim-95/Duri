# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: VaultFolder Future Work de-scope / PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 / ADR-008 Accepted
- Status: Complete — Fable Pass and CEO final approval recorded

## Review Outcome

Fable 4차 Re-Review verdict: Pass.

CEO final approval:

1. PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 Draft 해제
2. ADR-008 -> Accepted

Applied by Codex:

- `docs/PRD.md` title changed to `Duri PRD v0.2.5`.
- `docs/DATA_MODEL.md` title/footer changed to `v0.4`.
- `docs/WORKFLOW.md` title/footer changed to `v0.4`.
- `docs/adr/ADR-008-preservation-first-mvp-vaultfolder-future-work.md` status changed to `Accepted`.
- `docs/adr/README.md` ADR-008 status changed to `Accepted`.
- `README.md` updated to show the VaultFolder De-scope Gate complete and the next
  Storage Layout RFC 0001 Gate still pending.
- `CHANGELOG.md` records the final approval.

## Finalized Decisions

- MVP excludes VaultFolder Curation.
- ADR-008 records Preservation-first MVP: VaultFolder Curation is Future Work.
- Auth operating data remains excluded from Export.
- Participant display names are memory display identity and are included in Export so
  `messages.md` can remain human readable.

## Still Draft

Storage Layout RFC 0001 remains Draft.

Before implementation touches original-data write paths, backup/export, auth, or
device/session code, RFC 0001 or its successor must pass a separate Gate.

Open questions for that Gate:

1. Month-level `metadata.json` vs per-day partitions.
2. Target deployment server filesystem durability guarantees.

## Verification

Codex ran:

- `rg` checks for stale `Draft` / `Proposed` status on finalized documents.
  - Remaining matches are expected historical entries, explicit "Draft 해제" text, or
    RFC 0001's intentional Draft status.
- `git diff --check`.
- Manual README and ADR status review.
