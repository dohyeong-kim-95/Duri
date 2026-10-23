# Fable Review Request — Code Review Fixes (H1~H5, M1~M9, L1~L8)

- Date: 2026-10-23
- Requested by: Claude Code (코드 리뷰 수정 작업)
- Reviewer: Fable (Gate Keeper)
- Branches: `claude/fix-high-findings` → `claude/fix-rest` (main에는 아직 머지하지 않음)
- Status: **Open** — Fable review 요청

Gate ④(스토리지 포맷)와 ⑤(원본 쓰기 경로·인증 코드)에 닿는 변경이라 확정 전에 심사를 요청한다.
포맷 결정 자체([RFC 0002](../docs/rfc/0002-duristorage-canonical-format.md))는 CEO 몫이라 이 요청에 없다.

## 1. Gate Spec 테스트 변경 — A2-3

- 변경: `messages.md` 재생성이 실패하면 예외(`StorageWriteError`)를 기대하던 단언을 없앴다.
  이제 쓰기는 성공으로 반환돼야 한다. `metadata.json`, 사진 바이트, sha256 단언은 그대로다.
- 근거: RFC 0001 §10("7단계가 실패해도 정본은 유효하다"). 예외를 올리면 호출자가 재시도하고
  중복 Log가 생겼다(리뷰 H1).
- 요청: Spec 문장 해석 변경으로 받아들일지 판단해 달라. 새 R-* 테스트 14건(파라미터 포함 16개 실행)은
  [Spec R 절](./fable-gate-acceptance-spec.md)에 **Pending**으로 올렸다.

## 2. 원본 쓰기 경로 변경 (`apps/api/src/duri_api/storage.py`)

| 항목 | 변경 |
|---|---|
| H1 | 같은 `log_id`·같은 내용은 기존 Log 반환. 내용이 다르면 `StorageWriteError`. 사진은 type·actor만 비교(재인코딩 허용). recovery Log는 actor 비교 제외 |
| H1 | `metadata.json` 확정 뒤 `messages.md`의 렌더링·쓰기 예외는 모두 경고만 남김(append, orphan 복구 모두) |
| H3 | 사진은 temp → 검증 → `os.link`로 게시. `FileExistsError`면 이름을 다시 고름(같은 sha256 재사용 / `_2`…). temp 이름에 pid+난수 |
| H4 | orphan 파일명 시각은 파티션 `timezone`으로 해석하고 그 offset으로 저장. id가 겹쳐도 시각은 유지 |
| H5 | `schema_version`이 정수 `1`이 아니면 쓰기 거부(reader는 건너뜀) |
| M2 | naive datetime은 `ValueError`로 거부 |
| M3 | 파티션 안 정렬을 실제 시각 기준으로. 파티션 `timezone`과 writer 타임존이 다르면 새 Log 거부 |
| M4 | 파티션마다 `threading.Lock` + `fcntl.flock("<partition>/.write.lock")`. `metadata.json` temp 이름에 pid+난수 |
| L3 | `messages.md`도 temp + `os.replace` |
| L4 | `period`는 `YYYY-MM`만 허용(경로에 들어가기 전 검증) |

파생물: 인덱스 재구축 temp 이름 유일화, 옛 `-wal`/`-shm`/`-journal` 삭제(H2). 검색 텍스트를 값만으로(M6).
운영: 복구 CLI `python -m duri_api.recover`(M5).

## 3. 인증 코드 변경 (`auth.py`, `main.py`)

- M7: 폐기된 기기는 같은 fingerprint로 재등록하면 그 행을 다시 활성화한다. 폐기 전 세션은 계속 무효다.
  활성 기기와 fingerprint가 겹치면 `AuthError`.
- M8: Timeline WebSocket은 메시지마다 세션 상태를 다시 확인하고, 폐기되면 1008로 닫는다.
- M9: `create_app_from_env` 추가(시크릿 32바이트 미만이면 시작 거부). 기본 `app`은 그대로 deny-by-default.
- L6: refresh 때 `devices.last_seen_at` 갱신. refresh token 회전·TTL은 바꾸지 않았다(배포 전 적대적 점검 항목).

## 4. 스토리지 레이아웃에 새로 생기는 파일

- `<partition>/.write.lock` (M4, 빈 파일). 숨김 파일이고 정본이 아니다. Export에 포함돼도 무해하지만
  RFC 0001 §2 레이아웃에는 없는 파일이라 확인을 요청한다.

## 검증

`pytest`(73 passed), `ruff check`, `ruff format --check`, `mypy --strict`, 프론트 lint/typecheck/test/build,
Markdown 링크 검사 모두 통과.
