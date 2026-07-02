# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: VaultFolder Future Work de-scope / PRD v0.2.5 Draft / DATA_MODEL v0.4 Draft / WORKFLOW v0.4 Draft / Storage Layout RFC 0001 Draft
- Status: Review Requested

## Why This Needs Gate Review

`00-gatekeeping-principles.md` requires Fable review before finalizing PRD meaning
changes, MVP scope changes, data model changes, and storage/export format decisions.

This update changes the MVP boundary:

- Before: VaultFolder Curation was treated as MVP.
- Now: VaultFolder Curation is Future Work.

## CEO Decision Applied

CEO Decision — VaultFolder is Future Work:

- MVP includes only:
  - Message Log storage
  - Photo Log storage
  - Timeline storage
  - Deterministic Metadata
  - Search
  - Storage-as-Export
  - Auth
- MVP excludes VaultFolder Curation.
- VaultFolder is a future feature where users manually create memory folders or AI
  suggests curation.
- MVP goal is preservation, not curation:
  - "채팅과 사진을 잃지 않고 시간순으로 보존하는 것"

## Changed Artifacts

- `README.md`
  - Removed `Manual VaultFolder Curation` from Current MVP.
  - Updated Core Concept to:
    - `Timeline -> View/Index`
    - Future Work: `VaultFolder`, `AI View`
  - Updated Next Gate bullets to remove VaultFolder export design from MVP scope.

- `docs/PRD.md`
  - Bumped to `v0.2.5 Draft`.
  - Replaced PRD §4.4 with "Search Now, Vault Later".
  - MVP exploration is now Timeline + Deterministic Metadata + Search.
  - VaultFolder, Location Alias, AI summary/recommendation/classification are Future Work.

- `docs/DATA_MODEL.md`
  - Bumped to `v0.4 Draft`.
  - Moved `VaultFolder` from MVP entity to Future Work entity.
  - Removed `Log -> VaultFolder` MVP relationship.
  - Replaced `VaultFolder and Metadata Exploration` section with `Search and Metadata Exploration`.
  - Added Future Work section for VaultFolder principles.
  - Confirmed Auth/User/Device operating data is excluded from Export.

- `docs/WORKFLOW.md`
  - Bumped to `v0.4 Draft`.
  - Reframed MVP workflow as Log -> Timeline -> Search.
  - Removed "user puts items into VaultFolder" from MVP path.

- `docs/rfc/0001-storage-layout.md`
  - Kept status as Draft.
  - Removed `vault/folders/` from proposed MVP layout.
  - Removed VaultFolder Export question.
  - Added rejection rationale for including VaultFolder Curation in MVP storage.

- `docs/adr/ADR-002-timeline-first.md`
  - Added 2026-07-03 amendment note.
  - Kept Timeline First decision.
  - Corrected the older "Vault starts in MVP" clause to match the new CEO decision.

- `docs/EVENT_ENGINE.md`
  - Updated Future Work wording from "Timeline + Vault" to "Timeline 보존 + Search".
  - Updated broken links caused by PRD/DATA_MODEL section heading changes.

- `CHANGELOG.md`
  - Recorded this as `PRD v0.2.5 Draft / DATA_MODEL v0.4 Draft`.

## Fable Review Focus

Please review:

1. Whether VaultFolder is fully removed from MVP scope across README, PRD, DATA_MODEL,
   WORKFLOW, RFC, ADR-002, and EVENT_ENGINE.
2. Whether the new MVP boundary still satisfies:
   - Human Readable First
   - Timeline First
   - AI as Reader
   - Storage-as-Export
3. Whether amending ADR-002 is acceptable, or whether this should instead become a new
   ADR that supersedes part of ADR-002.
4. Whether PRD v0.2.5 Draft and DATA_MODEL v0.4 Draft can proceed toward CEO final
   approval after review.
5. Whether Storage Layout RFC 0001 remains a valid Draft for the next Phase 3 Gate.

## Current Open Technical Questions

These remain intentionally open in Storage Layout RFC 0001:

1. Is month-level `metadata.json` sufficient for MVP, or should Duri start with per-day
   partitions?
2. What exact filesystem durability guarantees are required on the target deployment
   server?

## Verification

Codex ran:

- `rg` checks for stale MVP VaultFolder/Vault wording.
  - Remaining matches are in historical CHANGELOG entries, this review request, or explicit
    "MVP excludes / Future Work" wording.
- Markdown diff review.
- `git diff --check`.

## Non-Final Boundary

This request does not authorize implementation of original-data write paths, backup/export,
auth, or device/session code.

No ADR is being newly accepted in this change. Storage Layout RFC 0001 remains Draft.
