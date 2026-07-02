# 0001. Storage Layout RFC

- Status: Draft
- Date: 2026-07-02
- Related: PRD v0.2.4, DATA_MODEL v0.3, ADR-001, ADR-007

## Summary

Duri의 Export v1 저장 구조를 `DuriArchive/` 아래에 두고, Timeline 월별 원본
묶음과 VaultFolder 사용자 큐레이션을 분리한다.

이 RFC는 구현 전 논의 초안이다. Accepted 전까지 파일명 규칙, 디렉토리 규칙,
쓰기 무결성 전략은 확정되지 않는다.

## Motivation

ADR-007은 "저장 구조 자체가 Export"라고 결정했다. 따라서 구현 전에 다음을
정해야 한다.

- `Vault/`라는 루트 이름과 `VaultFolder` 엔터티의 용어 충돌 해소
- Message/Photo 원본의 canonical 위치
- VaultFolder 큐레이션을 Export에서 사람이 읽을 수 있게 표현하는 방식
- 파일명 규칙과 월/일 분할 기준
- `metadata.json` 쓰기 무결성 전략

이 RFC는 원본 데이터를 오래 보존하면서도, 앱이 없어도 파일 탐색기와 표준 도구로
읽을 수 있는 저장 구조를 제안한다.

## Proposal

### 1. Root Name

Export 루트는 `Vault/`가 아니라 `DuriArchive/`로 한다.

이유:

- `VaultFolder`는 사용자가 직접 만든 큐레이션 엔터티다.
- Export 전체 루트를 `Vault/`라고 부르면 Timeline 원본 아카이브와 사용자
  VaultFolder가 섞여 보인다.
- `DuriArchive/`는 앱 전체 원본 보관소라는 의미가 더 명확하다.

### 2. Top-Level Layout

```text
DuriArchive/
  timeline/
    2026/
      2026-07/
        metadata.json
        messages.md
        photos/
          2026-07-12T19-30-22_01J...jpg
  vault/
    folders/
      01J.../
        folder.json
        index.md
  indexes/
    README.md
  system/
    README.md
```

Directory roles:

- `timeline/`: canonical Log archive. `metadata.json` and original photos live here.
- `vault/folders/`: user-created VaultFolder curation. It references Log IDs, not duplicate media.
- `indexes/`: rebuildable search/timeline helper files. These are not canonical.
- `system/`: operational notes for humans. Auth secrets and token/session hashes are not exported.

### 3. Timeline Partition Rule

Timeline partitions use `Log.created_at` in local application timezone.

Example:

```text
timeline/2026/2026-07/
```

Reason:

- `Log.created_at` is the Timeline ordering key.
- Photo EXIF `captured_at` can differ from upload/Log time and can be missing.
- Partitioning by one canonical Log field avoids a photo moving between folders if EXIF handling changes.

Photo metadata still stores `captured_at` and raw EXIF GPS when available.

### 4. Canonical Monthly Metadata

`metadata.json` is the canonical structured source for all Logs in a month partition.

Shape:

```json
{
  "schema_version": 1,
  "period": "2026-07",
  "timezone": "Asia/Seoul",
  "logs": [
    {
      "id": "01J...",
      "type": "Message",
      "created_at": "2026-07-12T19:28:00+09:00",
      "ingested_at": "2026-07-12T19:28:01+09:00",
      "actor_id": "01J_USER...",
      "source": "chat",
      "payload": {
        "message_id": "01J_MSG...",
        "text": "오늘 저녁 뭐 먹을까?",
        "thread_id": "default"
      },
      "metadata": {}
    }
  ]
}
```

Rules:

- Message `text` is canonical in `metadata.json`.
- `messages.md` is generated from `metadata.json`.
- Original photos live under `photos/`, and `metadata.json` stores their `MediaRef`.
- DB/search indexes must be rebuildable from `metadata.json` and original media files.

### 5. Human-Readable Message View

`messages.md` is a regenerated human-readable view, not canonical source.

Example:

```markdown
# 2026-07 Messages

## 2026-07-12

19:28 — Dohyeong
: 오늘 저녁 뭐 먹을까?
```

Rules:

- If `messages.md` and `metadata.json` conflict, `metadata.json` wins.
- `messages.md` can be deleted and regenerated.

### 6. Photo File Naming

Photo file names use:

```text
<created_at-basic>_<log_id>.<ext>
```

Example:

```text
2026-07-12T19-30-22_01J....jpg
```

Rules:

- `created_at` is sanitized for filesystem portability.
- `log_id` prevents collisions.
- Original extension is preserved when safe; otherwise MIME type determines extension.
- Original filename is stored in `MediaRef.original_filename`.

### 7. VaultFolder Export

VaultFolder curation is exported as references, not duplicated media.

Example:

```text
vault/
  folders/
    01J_VAULT_BUSAN/
      folder.json
      index.md
```

`folder.json`:

```json
{
  "id": "01J_VAULT_BUSAN",
  "name": "부산 여행",
  "path": "여행/부산 여행",
  "parent_id": null,
  "log_ids": ["01J_LOG_1", "01J_LOG_2"],
  "cover_ref": "01J_MEDIA_1",
  "updated_at": "2026-07-12T20:00:00+09:00"
}
```

`index.md` is a human-readable generated view:

```markdown
# 부산 여행

- 2026-07-12 19:30 — Photo — `01J_LOG_1`
- 2026-07-12 19:32 — Message — `01J_LOG_2`
```

Rules:

- VaultFolder stores curated `log_ids` only.
- It does not store metadata filters or search results.
- It does not duplicate original photos.
- If a user wants a portable folder of copied photos later, that is a separate generated Export View.

### 8. Metadata Exploration Views

Metadata-based search results are stored outside canonical VaultFolder data.

Optional generated location:

```text
indexes/
  metadata-exploration/
    last-search.json
```

Rules:

- These files are disposable.
- They must be regenerable from Timeline metadata.
- They are never treated as user curation.

### 9. Auth Export Boundary

Auth operating data is excluded from `DuriArchive/`.

Excluded:

- InviteCode hashes
- Refresh Session hashes
- Access tokens
- Device fingerprint hashes

Allowed, if needed:

- Human-readable user display names
- Human-readable device labels
- Revocation status summaries without secrets

### 10. Write Integrity Strategy

MVP write strategy:

1. Write uploaded media to a temporary file in the target month partition.
2. Compute hash and verify file size.
3. Atomically rename the media file into `photos/`.
4. Build the next `metadata.json` content in memory.
5. Write `metadata.json.tmp`.
6. Flush and atomically rename `metadata.json.tmp` to `metadata.json`.
7. Regenerate `messages.md` from `metadata.json`.

If step 7 fails, the canonical archive is still valid because `messages.md` is derived.

Implementation notes:

- The exact fsync behavior is platform-specific and must be handled in implementation.
- For MVP two-person usage, whole-file rewrite is acceptable.
- If `metadata.json` becomes too large, a future RFC can split by day or use per-log files.

## Alternatives Considered

### A. Keep `Vault/` as Export Root

Pros:

- Matches earlier DATA_MODEL examples.
- Sounds user-friendly.

Cons:

- Confuses the archive root with `VaultFolder`.
- Makes Timeline-originated records look like curated Vault content.

### B. Duplicate Photos into Each VaultFolder

Pros:

- Very easy to browse a folder by file explorer.

Cons:

- Duplicates originals.
- Creates consistency problems if metadata changes.
- Makes VaultFolder look like physical storage instead of curation over Log IDs.

### C. Store Every Log as a Separate JSON File

Pros:

- Atomic writes are simpler.
- Git-style diffs are cleaner.

Cons:

- Month-level human browsing is noisier.
- Requires an additional index file for month views.

This may become attractive later, but the MVP proposal keeps a monthly `metadata.json`
because DATA_MODEL v0.3 already names it as canonical.

## Open Questions

1. Should `DuriArchive/` be the final root name, or should it be configurable?
2. Is month-level `metadata.json` sufficient for MVP, or should we start with per-day partitions?
3. Should `vault/folders/<id>/` include generated copied media bundles as an optional View, or only references?
4. What exact filesystem durability guarantees are required on the target deployment server?
5. Should device/user display summaries be exported at all, or should `DuriArchive/` contain only memory data?

## Gate Notes

This RFC is Draft. It may be edited freely until it is proposed for acceptance.

Before implementation touches original-data write paths, backup/export, auth, or
device/session code, this RFC or a successor must pass Fable Gate Review and CEO approval.
