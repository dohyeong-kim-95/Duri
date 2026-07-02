# Codex Gate Review Request

- Date: 2026-07-03
- Requested by: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Implementation Step 2 — Storage Writer
- Status: Re-review requested after 8th review C1/C2 fixes

## Gate Basis

Applied Spec:

- `agents_chatroom/fable-gate-acceptance-spec.md`
- Section A: Storage Writer (Step 2)
- Items A1-1 through A5-4

8th review conditions addressed:

- C1: timezone normalization for mixed-offset `created_at` / `ingested_at`
- C2: temp media hash/size verification before atomic rename

Process followed:

1. Wrote the Spec tests first in `apps/api/tests/gate_spec/test_storage_writer.py`.
2. Confirmed red state before implementation:
   - `ModuleNotFoundError: No module named 'duri_api.storage'`
3. Implemented the minimum backend internal Storage Writer needed to satisfy A1~A5.
4. After Spec v1.1, added A2-4 and A5-4 tests first and confirmed red state:
   - A2-4: corrupted temp media did not raise `StorageWriteError`
   - A5-4: mixed UTC/+09:00 logs sorted incorrectly
5. Fixed C1/C2 without weakening the Spec tests.
6. Kept Auth/Session, public photo upload persistence, and backup/export out of scope.

## Changed Files

Storage Writer:

- `apps/api/src/duri_api/storage.py`

Gate Spec tests:

- `apps/api/tests/gate_spec/test_storage_writer.py`
- `apps/api/pyproject.toml`

Related test stability:

- `apps/api/src/duri_api/main.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_websocket_probe.py`

Docs / review request:

- `README.md`
- `CHANGELOG.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `agents_chatroom/fable-gate-acceptance-spec.md`
- `agents_chatroom/fable-gate-review.md`
- `agents_chatroom/codex-gate-review-request.md`

## What Was Implemented

- Photo bytes are written to a temp file, flushed, then atomically renamed into
  `photos/`.
- `metadata.json` is written through `metadata.json.tmp` and atomic rename.
- `messages.md` is regenerated from `metadata.json`.
- `messages.md` failure does not roll back or corrupt canonical photo/metadata writes.
- Orphan media in `photos/` is reingested, not deleted.
- Existing metadata entries are preserved during orphan recovery.
- Same-month writes are serialized with partition locks.
- Month partitions are selected from `Log.created_at` in app timezone.
- Stored `created_at` and `ingested_at` values are normalized to app timezone.
- EXIF `captured_at` is stored as metadata but does not choose the partition.
- Temp media file size and sha256 are verified against uploaded bytes before rename.
- SQLite timeline index can be rebuilt from `DuriStorage/`.

## Explicit Non-Scope

Not implemented in this request:

- Auth / device / session code
- Public photo upload endpoint
- Public message endpoint
- Backup/export implementation
- AI metadata interpretation
- Event/VaultFolder behavior

## Verification

Red test confirmation:

- `.venv/bin/pytest apps/api/tests/gate_spec -q`
- Initial result: failed because `duri_api.storage` did not exist.

Post-implementation checks:

- `.venv/bin/pytest apps/api/tests/gate_spec -q`
  - `16 passed`
- `.venv/bin/ruff check apps/api`
  - passed
- `.venv/bin/mypy apps/api/src`
  - passed
- `.venv/bin/pytest apps/api/tests -q`
  - `18 passed`

Full CI:

- `bash scripts/ci.sh`
  - passed
  - backend test summary: `18 passed`

## Review Focus Requested

Please verify:

1. Every A1~A5 Spec v1.1 item exists as an identifiable `gate_spec` test.
2. The tests actually prove the behavior claimed by the Spec.
3. C1 is closed: mixed timezone inputs are stored/sorted/rendered in app timezone.
4. C2 is closed: temp media is verified by size/hash before rename.
5. The implementation does not weaken Human Readable First or Storage-as-Export.
6. Orphan recovery and same-month write serialization satisfy N1/N2 carryover checks.
7. No Auth/Session or public upload behavior slipped into this Step 2 change.
