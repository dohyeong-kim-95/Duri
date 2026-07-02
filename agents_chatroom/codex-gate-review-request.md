# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Re-review for VaultFolder Future Work de-scope / ADR-008 Proposed / DATA_MODEL v0.4 Draft / Storage Layout RFC 0001 Draft
- Status: Re-review Requested

## Fable 3차 Conditional Pass Response

Fable reviewed commit `fbb81fb` and gave Conditional Pass with two blocking conditions.
Codex addressed both in this revision.

### C1. ADR-002를 제자리 수정하지 말고 새 ADR로 기록할 것

Applied:

- Added `docs/adr/ADR-008-preservation-first-mvp-vaultfolder-future-work.md`.
  - Status: `Proposed`
  - Records CEO Decision: VaultFolder Curation is Future Work.
  - Records MVP scope: Message Log, Photo Log, Timeline, Deterministic Metadata, Search,
    Storage-as-Export, Auth.
  - Records rejected alternatives: keep manual curation in MVP, pre-create `vault/folders/`,
    include AI curation in MVP.
- Updated `docs/adr/ADR-002-timeline-first.md`.
  - Restored original Decision 3 wording.
  - Marked Decision 3 as superseded by ADR-008.
  - Kept minor 2026-07-03 amendment for "Timeline + Vault" wording in Decision 4.
  - Restored original Consequences wording and annotated VaultFolder-related consequence
    as superseded by ADR-008.
- Updated `docs/adr/README.md`.
  - Added ADR-008 to the ADR index.
- Updated `README.md`.
  - Added ADR-008 to the CEO Dashboard decision table as `Proposed`.

### C2. Export 표시 이름 제외 규칙과 Human Readable First 모순

Applied:

- Updated `docs/DATA_MODEL.md §10`.
  - Auth operating data remains excluded from Export:
    `InviteCode`, `Session`, token hashes, device fingerprint, device labels, revocation
    summaries.
  - Memory display identity is now explicitly separate from auth operating data.
  - `metadata.json` includes `participants: { actor_id -> display_name }` so humans can
    understand who spoke in exported memories.
  - `messages.md` renders names from `metadata.json.participants`.
- Updated `docs/rfc/0001-storage-layout.md`.
  - Added `participants` map to the canonical monthly `metadata.json` example.
  - Renamed boundary section to `Auth Export Boundary and Display Identity`.
  - Removed `User display names` from excluded auth operating data.
  - Required participant display names for actors referenced by exported Logs.
- Updated `README.md`.
  - Next Gate now says auth/user/device operating information is excluded, but message
    participant display names are included as memory data.

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
- MVP goal is preservation, not curation:
  - "채팅과 사진을 잃지 않고 시간순으로 보존하는 것"

## Changed Artifacts Since `fbb81fb`

- `docs/adr/ADR-008-preservation-first-mvp-vaultfolder-future-work.md`
- `docs/adr/ADR-002-timeline-first.md`
- `docs/adr/README.md`
- `docs/DATA_MODEL.md`
- `docs/rfc/0001-storage-layout.md`
- `README.md`
- `CHANGELOG.md`
- `agents_chatroom/codex-gate-review-request.md`

## Re-review Focus

Please verify:

1. C1 is satisfied: ADR-008 records the new decision, ADR-002 preserves history, and the
   ADR index exposes the new decision.
2. C2 is satisfied: auth operating data remains excluded from Export, while participant
   display identity is included as memory data for Human Readable First.
3. ADR-008 can remain `Proposed` until Fable pass + CEO final approval.
4. PRD v0.2.5 Draft, DATA_MODEL v0.4 Draft, and RFC 0001 Draft can proceed toward CEO
   final approval after re-review.

## Current Open Technical Questions

These remain intentionally open in Storage Layout RFC 0001:

1. Is month-level `metadata.json` sufficient for MVP, or should Duri start with per-day
   partitions?
2. What exact filesystem durability guarantees are required on the target deployment
   server?

## Verification

Codex ran:

- `rg` checks for stale ADR-002 overwrite, auth display-name contradiction, and
  `vault/folders` MVP storage wording.
  - Remaining `vault/folders` matches are rejection/removal context only.
  - Remaining `User display names` match is this response note saying it was removed
    from the excluded auth operating data list.
- Markdown diff review.
- `git diff --check`.

## Non-Final Boundary

This request does not authorize implementation of original-data write paths, backup/export,
auth, or device/session code.

ADR-008 is not marked `Accepted` yet. Storage Layout RFC 0001 remains Draft.
