# Fable Gate Acceptance Spec v1.2

- Date: 2026-07-03 (v1.1 — A2-4, A5-4 추가 / v1.2 — B2-4 추가)
- Author: Fable (Gate Keeper)
- Audience: Codex (Architect)
- Scope: IMPLEMENTATION_PLAN Step 2 (Storage Writer), Step 3 (Auth/Session)
- Status: Active — 이 목록의 테스트가 존재하고 CI에서 통과해야 해당 Gate를 통과한다

> 규칙은 [00-gatekeeping-principles.md](./00-gatekeeping-principles.md)의
> "구현 단계 Gate 구조"를 따른다. 테스트를 먼저 작성해 실패를 확인한 뒤
> 구현한다. 이 목록의 테스트를 약화·삭제·skip하는 변경은 Fable review 없이
> 진행할 수 없다. 테스트 이름은 아래 행위 문장을 그대로 옮긴다.

---

## A. Storage Writer (Step 2) — 근거: RFC 0001 §4~§7, §10 / DATA_MODEL §10

### A1. 원본 무손실

- [ ] A1-1. 업로드된 사진의 바이트는 `photos/`에 저장된 파일과 정확히 동일하다 (sha256 일치).
- [ ] A1-2. 사진 저장 후 `metadata.json`의 MediaRef는 실제 파일의 크기·해시와 일치한다.
- [ ] A1-3. 어떤 재수록·재계산 경로도 저장된 payload(메시지 본문, 사진 바이트)를 변경하지 않는다.

### A2. 원자성 / 장애 내성

- [ ] A2-1. 사진 쓰기가 원자적 rename 이전에 실패하면 `photos/`에 불완전한 파일이 남지 않는다.
- [ ] A2-2. `metadata.json` 갱신 도중 프로세스가 중단되어도 이전 `metadata.json`은 온전한 JSON으로 남는다 (temp 파일 + rename 검증).
- [ ] A2-3. `messages.md` 재생성이 실패해도 `metadata.json`과 `photos/`는 영향받지 않는다.
- [ ] A2-4. 원자적 rename 직전의 temp 파일 내용이 업로드된 원본 바이트와 다르면(손상 시뮬레이션) 쓰기가 실패하고 `photos/`에 파일이 남지 않는다 — RFC 0001 §10 2단계("hash/size 검증 후 rename") 준수. *(v1.1 추가)*

### A3. 재생성 가능성 (canonical 경계)

- [ ] A3-1. `messages.md`를 삭제한 뒤 `metadata.json`에서 동일한 내용으로 재생성할 수 있다.
- [ ] A3-2. DB와 검색 인덱스를 삭제한 뒤 `DuriStorage/`만으로 전부 재구축할 수 있고, 재구축 결과로 동일한 Timeline 조회가 가능하다.
- [ ] A3-3. `metadata.json`에는 참여자 표시 이름 맵(`participants`)이 포함되어, 파일만 읽어도 발화자를 알 수 있다.

### A4. Orphan 미디어 보호

- [ ] A4-1. `photos/`에 있으나 `metadata.json`에 없는 파일은 복구 스캔에서 삭제되지 않고 재수록된다.
- [ ] A4-2. 복구 스캔은 기존 `metadata.json` 항목을 변경하지 않는다.

### A5. 동시성 / 파티션 규칙

- [ ] A5-1. 같은 월 파티션에 대한 동시 쓰기 요청 2건이 모두 유실 없이 `metadata.json`에 반영된다 (직렬화 검증).
- [ ] A5-2. Log는 `created_at`(앱 타임존)의 월 파티션에 저장된다 — 월 경계(말일 23:59 / 익월 00:00) 케이스 포함.
- [ ] A5-3. EXIF `captured_at`이 `created_at`과 다른 달이어도 파티션은 `created_at`을 따른다.
- [ ] A5-4. 서로 다른 타임존 표기(예: UTC와 +09:00)로 도착한 Log들이 **실제 시각 순서대로** Timeline에 정렬되고, `metadata.json`의 `created_at`과 `messages.md`의 시각 표기는 앱 타임존으로 일관된다. *(v1.1 추가 — 8차 심사에서 결함 실증됨)*

## B. Auth / Session (Step 3) — 근거: ADR-005 / DATA_MODEL §9 / RFC 0001 §8~§9

### B1. 2인 제한

- [ ] B1-1. 유효한 초대 코드로 사용자 등록에 성공한다.
- [ ] B1-2. 이미 사용된 초대 코드로는 등록할 수 없다 (1회 소모).
- [ ] B1-3. 두 슬롯이 모두 등록된 상태에서는 어떤 경로로도 세 번째 사용자를 만들 수 없다.
- [ ] B1-4. 같은 슬롯에 두 명이 등록될 수 없다 (slot 유일성).

### B2. 비밀 비저장

- [ ] B2-1. 초대 코드 원문은 DB·로그·`DuriStorage/` 어디에도 저장되지 않는다 (해시만 존재).
- [ ] B2-2. Refresh token 원문도 동일하다.
- [ ] B2-3. `DuriStorage/` 트리 안에 auth 운영 데이터(해시 포함)가 존재하지 않는다.
- [ ] B2-4. 토큰 서명 키를 교체해도 저장된 해시(초대 코드·refresh token·fingerprint)는 유효하게 유지된다 — 같은 DB에서 서명 키만 다른 서비스 인스턴스로 기존 refresh token 갱신이 성공하고, 구 access token은 거부된다 (서명 키와 해시 키의 도메인 분리). *(v1.2 추가 — 10차 심사)*

### B3. 접근 통제

- [ ] B3-1. 인증 없는 요청은 모든 데이터 엔드포인트(Timeline, 사진, 검색, WebSocket)에서 거부된다.
- [ ] B3-2. 만료된 access token은 거부된다.
- [ ] B3-3. 유효한 refresh session으로 access token을 갱신할 수 있다.

### B4. 기기 관리

- [ ] B4-1. 특정 기기의 세션을 폐기하면 그 기기의 refresh token은 거부된다.
- [ ] B4-2. 한 기기의 폐기는 같은 사용자의 다른 기기 세션에 영향을 주지 않는다.

## R. 코드 리뷰 회귀 테스트 — **Pending Fable review** *(2026-10-23 제안, 미승인)*

> 코드 리뷰(H1~H5) 수정과 함께 추가된 테스트다. `apps/api/tests/gate_spec/test_review_findings.py`에
> `gate_spec` marker로 있고 CI에서 통과하지만, **Fable이 승인하기 전까지는 Gate Spec이 아니다.**
> 요청 내용은 [fable-review-request-review-fixes.md](./fable-review-request-review-fixes.md).
> 승인되면 체크하고, 반려되면 이 절과 해당 테스트의 marker를 조정한다.

### R-H1. `messages.md` 실패 / 같은 `log_id` 재시도

- [ ] R-H1-1. `metadata.json` 확정 뒤 `messages.md` 재생성이 실패해도 쓰기는 성공으로 반환된다.
- [ ] R-H1-2. 같은 `log_id`로 같은 내용을 다시 쓰면 중복 Log를 만들지 않고 기존 Log를 반환하고, 다른 내용(type·actor·시각·본문)이면 기존 Log를 돌려주지 않고 오류로 거부한다 (메시지·사진 모두, 사진의 재인코딩 바이트 차이는 같은 내용으로 본다).
- [ ] R-H1-3. `metadata.json` 확정 뒤에는 `messages.md` 렌더링·쓰기에서 어떤 예외가 나도 쓰기와 orphan 복구는 성공으로 반환된다.

### R-H2. 인덱스 재구축

- [ ] R-H2-1. 정본에 같은 `id`가 중복돼도 인덱스 재구축은 실패하지 않고, 실패하더라도 기존 인덱스는 남는다.
- [ ] R-H2-2. 인덱스 재구축은 옛 인덱스에 남은 `-wal`/`-shm` 파일을 새 인덱스에 적용하지 않고, 임시 파일을 남기지 않는다.

### R-H3. 사진 원본 덮어쓰기 방지

- [ ] R-H3-1. 사진 파일명이 겹쳐도 기존 원본 사진은 덮어써지지 않는다 — 같은 바이트면 기존 파일을 재사용하고, 다른 바이트면 새 이름으로 저장한다.
- [ ] R-H3-2. 이미 같은 바이트의 사진 파일이 있는 경로로 다시 쓰면 파일을 새로 만들지 않고 그 파일을 참조한다 (크래시 후 재시도).
- [ ] R-H3-3. 이름 확인과 저장 사이에 다른 프로세스가 같은 사진 파일명을 먼저 만들어도 그 원본은 덮어써지지 않고, 새 사진은 다른 이름으로 저장된다.

### R-H4. Orphan 복구

- [ ] R-H4-1. 같은 바이트의 orphan 파일 두 개는 서로 다른 id로 복구되고, 복구 뒤에도 인덱스 재구축이 가능하다.
- [ ] R-H4-2. writer가 만든 파일명(`<created_at>_<log_id>.ext`)의 orphan은 원래 시각과 log_id로 복구되고, 그 외 파일만 월 시작 시각으로 복구된다.
- [ ] R-H4-3. orphan 파일명의 시각은 그 파티션 `metadata.json`의 timezone으로 해석하고, log_id가 이미 쓰이고 있어도 파일명의 시각은 유지한다.

### R-H5. 지원하지 않는 `metadata.json` 포맷 (임시 가드, [RFC 0002](../docs/rfc/0002-duristorage-canonical-format.md) 결정 전)

- [ ] R-H5-1. `schema_version`이 없는 `metadata.json`은 Timeline/Summary에서 건너뛰며, `period: "None"` 같은 잘못된 결과를 내지 않는다.
- [ ] R-H5-2. writer는 `schema_version`이 없는 기존 `metadata.json`을 덮어쓰지 않고 명확한 오류로 거부한다.
- [ ] R-H5-3. `schema_version`이 지원 버전(1)이 아니면(미래 버전 `2`, 문자열 `"1"` 등) reader는 건너뛰고 writer는 쓰기를 거부한다.

### 기존 Spec 테스트 변경 (Pending)

- A2-3 테스트: `messages.md` 실패 시 `StorageWriteError`를 기대하던 단언을 없애고 성공 반환을
  기대한다. `metadata.json`·사진 바이트·sha256 단언은 그대로다. Spec 문장은 바꾸지 않았다.
  규칙 C3에 따라 Fable review를 요청한다.

## C. 운영 규칙

1. 위 테스트는 `scripts/ci.sh`가 실행하는 스위트에 포함되어야 하며, Gate
   review 요청 시점에 원격 CI 녹색이어야 한다.
2. Spec 테스트는 식별 가능해야 한다 (예: pytest marker `gate_spec` 또는
   전용 디렉토리). Fable은 review 시 이 식별자로 존재·통과·변경 여부를 확인한다.
3. 구현 중 Spec 항목이 잘못됐거나 불충분하다고 판단되면, 테스트를 고치지
   말고 이 파일에 대한 수정을 Fable에게 요청하라.
4. Step 5(백업)의 Spec은 백업 결정(주기·복원 테스트·오프사이트·키 관리)이
   내려진 뒤 별도로 발행한다.
5. 인증 구현 완료 후 Fable의 1회성 적대적 점검이 예정되어 있다 — B 영역
   테스트 통과가 그 전제 조건이다.
