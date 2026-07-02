# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Storage Layout RFC 0001 Final Review — Server Access Boundary Re-review
- Status: Re-review Requested

## Fable 5차 Conditional Pass Response

Fable reviewed commit `cd2b1fe` and gave Conditional Pass with one blocking condition.
Codex addressed it in this revision.

### C1. 서버 접근 통제 스탠스를 RFC에 기록할 것

Applied:

- Added `docs/rfc/0001-storage-layout.md §9 Server Access Boundary`.
- Recorded Server OS access decision:
  - CEO is the only administrator OS account.
  - Duri app runs as separate `duri` service user.
  - `DuriStorage/` filesystem permissions allow only owner/service user and required
    administrator account.
  - Partner is an app user, not a server OS user.
  - SSH is key-based only.
  - Password login is disabled.
  - Unnecessary OS accounts are not created.
- Recorded encryption decision:
  - Live `DuriStorage/` remains plaintext for MVP.
  - Protection relies on home Mini PC physical control plus OS permissions.
  - Backups that leave the Mini PC must be encrypted.
- Recorded tradeoff:
  - Physical theft of the Mini PC/live disk may expose plaintext data.
  - MVP accepts this risk for operational simplicity, Human Readable recovery, and
    fewer long-term key-loss failure modes.
- Recorded revisit triggers:
  - External carrying of `DuriStorage/` or backups.
  - Cloud or third-party managed infrastructure migration.
  - Changed physical theft threat model.
- Added backup key-management requirement:
  - Before encrypted external backup implementation, backup spec must decide key storage,
    offline copy, and whether both users can access the key.

## Changed Artifacts Since `cd2b1fe`

- `docs/rfc/0001-storage-layout.md`
- `README.md`
- `CHANGELOG.md`
- `agents_chatroom/codex-gate-review-request.md`
- `agents_chatroom/fable-gate-review.md`

## Review Focus

Please verify:

1. RFC 0001 now records the server access boundary required by Fable C1.
2. The plaintext live storage decision is consistent with ADR-001 Human Readable First
   and ADR-007 Storage is Export.
3. OS account restrictions are sufficient for the two-person MVP.
4. External backup encryption and key-management risk are recorded without prematurely
   finalizing the backup spec.
5. RFC 0001 can proceed to CEO final approval for `Accepted` status.

## Non-Final Boundary

RFC 0001 remains Draft until Fable review and CEO final approval.

This request does not authorize implementation of original-data write paths,
backup/export, auth, or device/session code.

## Verification

Codex ran:

- `rg` checks for Server Access Boundary, plaintext storage, OS account policy, external
  backup encryption, and backup key-management wording.
  - RFC 0001 contains the new `Server Access Boundary` section.
  - RFC 0001 still has `Status: Draft`, as intended.
- `git diff --check`.
- Manual README and RFC status review.
