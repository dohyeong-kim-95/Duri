# Gate Note: DATA_MODEL v0.3 Draft

- Date: 2026-07-02
- Role: Architect
- Audience: Claude Code Fable / Gate Keeper
- Status: Ready for Fable Gate Review; not final until CEO approval

## CEO Decisions Applied

1. MVP Log Types are `Message` and `Photo` only.
2. Metadata extracts only; it does not interpret. No AI/NLP in MVP metadata.
3. Vault is metadata-based exploration/organization; AI auto-organization is Future Work.
4. Storage structure is Export v1. DB/search indexes are rebuildable caches.
5. Authentication uses Self-hosted JWT + Invite Code + device-bound Refresh Sessions.
6. Location Metadata stores raw EXIF GPS only. Location Alias is a Future Work `View`.

## Files Changed

- `README.md`
  - Current Phase moved to Phase 2 DATA_MODEL Review preparation.
  - CEO decisions summarized in the root README because the user reads this surface.
  - ADR-006 added to the decision table.
- `docs/DATA_MODEL.md`
  - Rewritten as v0.3 Draft.
  - Added auth entities: `User`, `InviteCode`, `Device`, `Session`.
  - Added `MediaRef`, export-as-storage, search/index boundary, and gate checklist.
- `docs/WORKFLOW.md`
  - Removed stale PWA success wording.
  - Narrowed MVP workflow to Message/Photo and deterministic metadata.
- `docs/EVENT_ENGINE.md`
  - Updated stale PRD/DATA_MODEL references.
- `docs/adr/ADR-006-raw-gps-location-metadata.md`
  - New Proposed ADR for raw GPS-only location metadata.
- `docs/adr/README.md`
  - ADR-006 added to index.
- `CHANGELOG.md`
  - DATA_MODEL v0.3 Draft section added.

## Gate Review Focus

Please verify:

- DATA_MODEL v0.3 Draft satisfies ADR-001 through ADR-005 and does not conflict with Proposed ADR-006.
- No Future Work has accidentally become an MVP requirement.
- Auth model is representable without external Auth Provider.
- Storage/export model preserves Human Readable First.
- Location semantics remain out of original metadata and in future View/Alias.

## Verification Run

- `rg` for stale PWA / old DATA_MODEL references.
- `git diff --check`.
- Manual diff review of README, DATA_MODEL, WORKFLOW, EVENT_ENGINE, ADR index, ADR-006, CHANGELOG.
