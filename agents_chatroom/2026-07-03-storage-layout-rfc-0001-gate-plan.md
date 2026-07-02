# Storage Layout RFC 0001 Gate Plan

- Date: 2026-07-03
- Author: Codex (Architect)
- Reviewer: Fable (Gate Keeper)
- Scope: Storage Layout RFC 0001 Final Review
- Status: Ready for Fable Review

## Goal

Prepare Storage Layout RFC 0001 for Fable review before any implementation touches
original-data write paths, backup/export, auth, or device/session code.

## CEO Decisions Incorporated

1. MVP keeps month-level `metadata.json`.
2. Day-level partitioning is Future Work if file size or performance becomes a problem.
3. `DuriStorage/` must live on persistent server-local storage or a mounted persistent
   volume.
4. `DuriStorage/` must not live on ephemeral filesystem.
5. Original photos, Message text, and metadata are preservation targets above DB/search.
6. DB/search indexes are rebuildable caches.
7. Writes use temp file, validation, atomic rename, fsync best effort, and separate backup.

## Proposed Review Sequence

1. Fable reviews RFC 0001 against ADR-001, ADR-007, ADR-008, DATA_MODEL v0.4, and README.
2. Codex addresses any Fable conditions.
3. CEO approves or rejects RFC 0001 finalization.
4. Only after approval, RFC 0001 may become `Accepted`.

## Explicit Non-Goals For This Gate

- Do not implement original-data write code.
- Do not implement backup/export code.
- Do not implement auth/device/session code.
- Do not mark RFC 0001 Accepted before Fable pass and CEO final approval.
