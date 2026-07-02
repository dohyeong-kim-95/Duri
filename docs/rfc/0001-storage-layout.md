# 0001. Storage Layout RFC

- Status: Draft
- Date: 2026-07-02
- Updated: 2026-07-03
- Related: PRD v0.2.5 Draft, DATA_MODEL v0.4 Draft, ADR-001, ADR-007, ADR-008

## Summary

Duri의 Export v1 저장 구조를 `DuriStorage/` 아래에 두고, Timeline 월별 원본
묶음과 재생성 가능한 Index/View를 분리한다.

이 RFC는 구현 전 논의 초안이다. Accepted 전까지 파일명 규칙, 디렉토리 규칙,
쓰기 무결성 전략은 확정되지 않는다.

## Motivation

ADR-007은 "저장 구조 자체가 Export"라고 결정했다. 따라서 구현 전에 다음을
정해야 한다.

- Export 루트 이름 확정
- Message/Photo 원본의 canonical 위치
- 파일명 규칙과 월/일 분할 기준
- `metadata.json` 쓰기 무결성 전략

이 RFC는 원본 데이터를 오래 보존하면서도, 앱이 없어도 파일 탐색기와 표준 도구로
읽을 수 있는 저장 구조를 제안한다.

## Proposal

### 1. Root Name

Export 루트는 `Vault/`가 아니라 `DuriStorage/`로 한다.

이유:

- MVP에서 VaultFolder Curation은 Future Work다.
- Export 전체 루트를 `Vault/`라고 부르면 MVP 저장소가 큐레이션 폴더처럼 보인다.
- `DuriStorage/`는 사용자가 파일 탐색기로 열었을 때 "Duri의 원본 저장소"라는
  의미가 명확하다.

### 2. Top-Level Layout

```text
DuriStorage/
  timeline/
    2026/
      2026-07/
        metadata.json
        messages.md
        photos/
          2026-07-12T19-30-22_01J...jpg
  indexes/
    README.md
  system/
    README.md
```

Directory roles:

- `timeline/`: canonical Log archive. `metadata.json` and original photos live here.
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
  "participants": {
    "01J_USER_1": {
      "display_name": "Dohyeong"
    },
    "01J_USER_2": {
      "display_name": "Partner"
    }
  },
  "logs": [
    {
      "id": "01J...",
      "type": "Message",
      "created_at": "2026-07-12T19:28:00+09:00",
      "ingested_at": "2026-07-12T19:28:01+09:00",
      "actor_id": "01J_USER_1",
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
- `participants` stores display identity needed to read memory data. It is not an auth
  session or device export.
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

### 7. Metadata Exploration Views

Metadata-based search results are stored outside canonical Timeline data.

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

### 8. Auth Export Boundary and Display Identity

Auth operating data is excluded from `DuriStorage/`.

Excluded:

- InviteCode hashes
- Refresh Session hashes
- Access tokens
- Device fingerprint hashes
- Device labels
- Revocation status summaries

Required memory display data:

- Participant display names for actors referenced by exported Logs

Rule:

- Export authorization happens before export creation.
- `DuriStorage/` does not contain login/session/device audit data.
- Participant display names are memory display identity, not auth operating data.
- `messages.md` may render participant names from `metadata.json.participants`.
- It is enough that the export action is allowed only for one of the two registered users.

### 9. Write Integrity Strategy

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

- Makes the MVP storage root look like a curated Vault product surface.
- Conflicts with the CEO decision that VaultFolder Curation is Future Work.

### B. Include VaultFolder Curation in MVP Storage

Pros:

- Would make manual memory folders easy to browse in a file explorer.

Cons:

- Expands MVP from preservation/search into curation.
- Forces storage/export decisions for a feature that is not needed to prove the MVP.
- Creates duplicate-media and consistency questions too early.

Rejected for MVP by CEO Decision: VaultFolder is Future Work.

### C. Store Every Log as a Separate JSON File

Pros:

- Atomic writes are simpler.
- Git-style diffs are cleaner.

Cons:

- Month-level human browsing is noisier.
- Requires an additional index file for month views.

This may become attractive later, but the MVP proposal keeps a monthly `metadata.json`
because DATA_MODEL v0.4 Draft already names it as canonical.

## Open Questions

1. Is month-level `metadata.json` sufficient for MVP, or should we start with per-day partitions?
2. What exact filesystem durability guarantees are required on the target deployment server?

## Gate Notes

This RFC is Draft. It may be edited freely until it is proposed for acceptance.

Before implementation touches original-data write paths, backup/export, auth, or
device/session code, this RFC or a successor must pass Fable Gate Review and CEO approval.
