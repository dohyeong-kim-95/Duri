# Codex Gate Review Request

- Date: 2026-07-02
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: PRD v0.2.4 / DATA_MODEL v0.3 / ADR-006 Accepted / ADR-007 Accepted
- Status: Complete — Fable Pass and CEO final approval recorded

## Why This File Exists

`00-gatekeeping-principles.md` says Codex cannot finalize decisions that bind future
original data, storage/export format, PRD meaning, or ADR acceptance without Fable
review and CEO final approval.

Fable passed the re-review and CEO gave final approval. The following actions are now complete:

- `docs/PRD.md` v0.2.4 finalized.
- `docs/DATA_MODEL.md` v0.3 finalized.
- `docs/adr/ADR-006-raw-gps-location-metadata.md` marked `Accepted`.
- `docs/adr/ADR-007-storage-is-export.md` marked `Accepted`.
- Phase 2 / DATA_MODEL Review marked complete in `README.md`.

Still not authorized without a new Gate:

- Starting implementation of original data write paths, backup/export, auth, or device/session code.

## Response to Fable Conditional Review

Fable reviewed commit `fd2c391` and gave a Conditional Pass. Codex addressed all
blocking conditions in this revision:

### C1. Vault original vs derived boundary

Applied:

- `DATA_MODEL.md` now separates `VaultFolder` from Metadata Exploration.
- `VaultFolder.log_ids` is only user-curated original membership.
- `metadata_filter`, saved searches, smart folders, and search results are excluded from
  `VaultFolder` and represented as regenerable View/Index.
- PRD §4.4 now states the same split.

### C2. Message canonical source

Applied:

- `DATA_MODEL.md §10` now defines `metadata.json` as the canonical source for Message
  text and structured Log data.
- `messages.md` is documented as a human-readable derivative regenerated from
  `metadata.json`.

### C3. CEO Decision ledger

Applied:

- Storage-as-Export was recorded as `docs/adr/ADR-007-storage-is-export.md` during review
  and is now `Accepted` after CEO approval.
- LogType limit, metadata extraction-only, Vault boundary, and Auth entity details are
  bundled under DATA_MODEL v0.3 approval scope. Fable confirmed this ledger structure is
  sufficient and no additional ADRs are required.

### C4. Metadata extraction-only principle in PRD

Applied:

- PRD §4.3 now states that MVP Metadata only extracts mechanically available values and
  does not interpret names, places, trips/dates, summaries, or tags.

### Recommendations

Applied:

- R1: Auth operating data, including token/session/invite hashes, is excluded from Export.
- R2: Message metadata duplication removed; sender/time/message ID are canonical envelope
  or payload fields.
- R3: WORKFLOW version normalized to v0.3.
- R4: WORKFLOW Non Goals label corrected to §11.

## Finalized Artifacts

- `README.md`
  - Root dashboard updated for Phase 2 Gate state.
  - Shows CEO Decisions, Phase 2 completion, and the next Storage Layout RFC Gate.
- `docs/PRD.md`
  - v0.2.4.
  - Clarifies Schedule and other non-Message/Photo Log Types as Future Work.
- `docs/DATA_MODEL.md`
  - v0.3.
  - Adds `Message`/`Photo`-only MVP scope.
  - Adds deterministic metadata-only rule.
  - Adds Auth entities: `User`, `InviteCode`, `Device`, `Session`.
  - Adds storage-as-export and DB/search-as-index boundary.
- `docs/adr/ADR-006-raw-gps-location-metadata.md`
  - Accepted ADR for raw GPS-only Location Metadata.
- `docs/adr/ADR-007-storage-is-export.md`
  - Accepted ADR for Storage-as-Export.
- `docs/WORKFLOW.md`
  - Aligns MVP workflow to Message/Photo and deterministic metadata.
- `docs/EVENT_ENGINE.md`
  - Keeps Event Engine as Future Work and updates references.
- `docs/adr/README.md`
  - Lists ADR-006 and ADR-007 as Accepted.
- `CHANGELOG.md`
  - Records PRD v0.2.4, DATA_MODEL v0.3, ADR-006 Accepted, and ADR-007 Accepted.

## Review Outcome

Fable re-review verdict: Pass.

CEO approval: Approved. Draft removed, ADR-006 and ADR-007 accepted, Phase 2 Gate marked complete.

## Next Gate

Before implementation touches original-data write paths, backup/export, auth, or device/session
code, open a Storage Layout RFC. It should address:

1. VaultFolder curation export representation.
2. `Vault/` root name vs `VaultFolder` terminology conflict.
3. File naming rules.
4. Month/day partition criteria.
5. `metadata.json` write integrity strategy.

## Verification Already Run

- `rg` checks for stale PWA and old DATA_MODEL anchor references.
- `git diff --check`.
- Manual review of changed markdown files.

## Current Non-Final Decision Boundary

Phase 2 artifacts are final. Implementation work that affects original data or security still
requires a new Gate.
