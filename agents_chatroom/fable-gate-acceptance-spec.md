# Fable Gate Acceptance Spec v1.1

- Date: 2026-07-03 (v1.1 — 8차 심사에서 A2-4, A5-4 추가)
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

### B3. 접근 통제

- [ ] B3-1. 인증 없는 요청은 모든 데이터 엔드포인트(Timeline, 사진, 검색, WebSocket)에서 거부된다.
- [ ] B3-2. 만료된 access token은 거부된다.
- [ ] B3-3. 유효한 refresh session으로 access token을 갱신할 수 있다.

### B4. 기기 관리

- [ ] B4-1. 특정 기기의 세션을 폐기하면 그 기기의 refresh token은 거부된다.
- [ ] B4-2. 한 기기의 폐기는 같은 사용자의 다른 기기 세션에 영향을 주지 않는다.

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
