# Changelog

Duri 문서(PRD 및 주요 결정)의 변경 이력을 기록한다.

포맷은 [Keep a Changelog](https://keepachangelog.com/)를 따른다.

---

## Read-only SQLite Timeline Index — 2026-07-03

Rebuildable Timeline/Search index improvement.

### Added

- `duri_api.timeline_index` full-log read helpers
- Indexed Timeline filtering by period and log type
- Indexed search that matches filesystem-backed search results after rebuild

### Guardrails

- SQLite remains a derived cache/index, not source of truth
- No original-data write endpoint added
- No auth HTTP endpoint added
- No upload persistence added

### Verification

- Timeline index tests: `2 passed`
- Storage Writer Gate spec: `16 passed`

---

## Read-only Timeline/Search Filters — 2026-07-03

Read-only Timeline/Search usability improvement.

### Added

- `period` and `type` filters for `GET /timeline`
- `period` and `type` filters for `GET /search`
- Frontend filter controls for period and log type
- Backend tests for combined query/period/type filtering

### Guardrails

- No original-data write path added
- No auth HTTP endpoint added
- No upload persistence added

### Verification

- Timeline/Search backend tests: `5 passed`
- Frontend tests: `8 passed`
- Backend/frontend lint and typecheck passed

---

## Frontend Timeline/Search Shell — 2026-07-03

Gate 불필요 read-only UI integration 반영.

### Added

- Frontend Timeline/Search client shell
- Typed Timeline/Search API client helpers
- Access-token handoff point via local browser storage for future auth flow
- API helper tests for authenticated read requests and display formatting

### Changed

- Initial scaffold UI를 read-only Timeline 중심 화면으로 정리
- Styling을 조용한 내부 도구 레이아웃으로 조정

### Guardrails

- No registration/login HTTP auth endpoint added
- No photo upload persistence added
- No original-data write path added

### Verification

- Frontend tests: `8 passed`
- Frontend lint/typecheck/build passed

---

## Read-only Timeline/Search Connection — 2026-07-03

Step 3 Gate 종료 후 진행 가능한 비-Gate 범위 반영.

### Added

- `duri_api.timeline` read-only query module
- Authenticated `GET /timeline` response backed by `DuriStorage/metadata.json`
- Authenticated `GET /search?q=...` response backed by `DuriStorage/metadata.json`
- Timeline/Search API tests

### Guardrails

- No original-data write path added
- No registration/login HTTP auth endpoint added
- No photo upload persistence added
- No backup/export implementation added

### Verification

- Timeline/Search tests: `3 passed`
- Backend tests: `34 passed`
- Gate spec: `29 passed`

---

## Auth/Session Gate Closed — 2026-07-03

Fable 11차 Re-Review Pass와 Step 3 Auth/Session Gate 종료 반영.

### Changed

- README를 Storage/Auth service Gate 종료 상태로 갱신
- 적대적 보안 점검 시점을 첫 배포 직전으로 이동
- HTTP 인증 엔드포인트와 photo upload persistence는 별도 Gate review 대상으로 명시

### Carryover

- Timeline/Search read-only 연결은 진행 가능
- 등록/로그인/갱신/폐기 HTTP auth endpoints는 Gate 대상
- Photo upload persistence는 Gate 대상
- 10차 심사의 보안 관찰 6건은 배포 직전 적대적 점검 시작 체크리스트

---

## Auth/Session C1 Re-review Request — 2026-07-03

Fable 10차 심사 Conditional Pass 조건 반영.

### Added

- Gate Acceptance Spec v1.2 반영
- B2-4 테스트: 서명 키만 교체해도 기존 refresh token 갱신은 성공하고, 구
  access token은 거부되는지 검증

### Changed

- JWT 서명 키(`jwt_secret`)와 저장 해시 키(`hash_secret`)를 분리
- invite code, refresh token, device fingerprint 해시에 용도별 HMAC domain 적용
- Gate review 요청 문서를 C1 재심사 요청으로 갱신

### Verification

- B2-4 red 확인: 서명 키 교체 후 기존 refresh token 조회 실패
- B2-4 green 전환
- Backend gate spec: `29 passed`
- Backend tests: `31 passed`

---

## Auth/Session Gate Review Request — 2026-07-03

Fable Gate Acceptance Spec v1.1의 Step 3 Auth/Session(B1~B4) 반영.

### Added

- `apps/api/src/duri_api/auth.py` 내부 AuthService 추가
- `apps/api/tests/gate_spec/test_auth_session.py` 추가
- Timeline, photo, search, Timeline WebSocket 데이터 표면 인증 가드 추가

### Tested Behaviors

- 유효한 초대 코드로 사용자 등록
- 초대 코드 1회 소모
- 정확히 2명까지만 등록
- slot 유일성
- 초대 코드/refresh token 원문 비저장
- auth 운영 데이터의 `DuriStorage/` 비저장
- 인증 없는 데이터 endpoint/WebSocket 요청 거부
- 만료 access token 거부
- refresh session으로 access token 갱신
- 기기별 refresh session 폐기
- 한 기기 폐기가 같은 사용자의 다른 기기에 영향을 주지 않음

### Gate

- Storage Writer Step 2는 Fable 9차 심사에서 통과.
- Auth/Session Step 3은 Gate review 요청 상태이며, 통과 전까지 제품 동작으로
  확정하지 않는다.

### Verification

- B1~B4 red 확인: `ModuleNotFoundError: No module named 'duri_api.auth'`
- Backend gate spec: `28 passed`
- Backend tests: `30 passed`
- Full CI: `bash scripts/ci.sh` passed

---

## Storage Writer C1/C2 Re-review Request — 2026-07-03

Fable 8차 심사 Conditional Pass 조건 반영.

### Added

- Gate Acceptance Spec v1.1 반영
- A2-4 테스트: rename 전 temp media size/sha256 검증
- A5-4 테스트: mixed timezone 입력의 app timezone 정규화와 실제 시각순 정렬

### Changed

- `created_at`과 `ingested_at`을 저장 시점에 앱 타임존으로 정규화
- 사진 temp 파일을 rename하기 전에 업로드 원본 바이트와 size/sha256 비교
- Gate review 요청 문서를 C1/C2 재심사 요청으로 갱신

### Verification

- A2-4/A5-4 red 확인 후 green 전환
- Backend gate spec: `16 passed`
- Backend tests: `18 passed`

---

## Storage Writer Gate Review Request — 2026-07-03

Fable Gate Acceptance Spec v1의 Step 2 Storage Writer(A1~A5) 반영.

### Added

- `agents_chatroom/fable-gate-acceptance-spec.md` 기록
- `apps/api/src/duri_api/storage.py` 내부 Storage Writer 모듈 추가
- `apps/api/tests/gate_spec/test_storage_writer.py` 추가
- `pytest` marker `gate_spec` 등록

### Tested Behaviors

- 원본 사진 바이트와 MediaRef 크기/해시 일치
- temp file + atomic rename 기반 사진/metadata write
- `messages.md` 재생성 실패가 canonical data를 손상하지 않음
- `messages.md` 삭제 후 metadata에서 재생성 가능
- SQLite timeline index를 `DuriStorage/`에서 재구축 가능
- participants display-name map 포함
- orphan media 재수록 및 기존 metadata 보존
- 같은 월 파티션 동시 쓰기 직렬화
- `created_at` 기준 월 파티션 규칙과 EXIF `captured_at` 비우선 규칙

### Gate

- Storage Writer는 Gate 대상 구현이다.
- Fable review 요청 상태이며, 통과 전까지 제품 동작으로 확정하지 않는다.

---

## Initial Tech Stack Scaffold — 2026-07-03

CEO Decision: Initial Tech Stack 반영.

### Added

- `apps/web` Next.js + TypeScript scaffold
- `apps/api` FastAPI scaffold
- FastAPI `/health` endpoint
- FastAPI `/ws/probe` WebSocket proof-of-connection endpoint
- Frontend/backend lint, typecheck, and test setup
- CI를 Next build, npm test, pytest, ruff, mypy까지 확장

### Changed

- README Current Architecture와 Development 섹션에 approved stack 및 실행 명령 추가
- Implementation Plan Step 1을 CEO-approved stack 기준으로 갱신

### Guardrails

- Original storage writes, auth/device sessions, photo upload persistence, and metadata
  write path remain blocked until Fable Gate Acceptance Spec exists.
- `npm audit` reports a moderate PostCSS advisory through Next.js 16.2.10. The suggested
  `npm audit fix --force` would downgrade Next.js across major versions, so this remains
  an upstream dependency risk to revisit when Next publishes a compatible patched release.

---

## Implementation Plan v0.1 — 2026-07-03

구현 착수 순서와 Gate 경계를 문서화.

### Added

- `docs/IMPLEMENTATION_PLAN.md` 추가
- 원본 쓰기/백업/Auth 구현 전 Fable Gate Acceptance Spec이 필요한 영역 명시
- 앱 스택 추천안 기록: TypeScript / Next.js / npm / SQLite cache + filesystem
  `DuriStorage/`

### Changed

- README Next Gate와 Documents에 Implementation Plan 링크 추가
- README 구현 Gate 이월 확인 항목에 앱 스택 선택 추가

---

## CI Baseline — 2026-07-03

구현 단계 Gate 구조와 "CI 구성 1순위" 원칙 반영.

### Added

- GitHub Actions CI 추가: 모든 push/PR에서 `scripts/ci.sh` 실행
- Markdown 로컬 링크 검사 스크립트 추가
- `.omx/` 로컬 에이전트 런타임 상태를 ignore 처리

### Changed

- README Next Gate에 CI 기준선과 Gate Acceptance Spec 테스트 연결 방식을 명시
- `00-gatekeeping-principles.md`의 구현 단계 TDD Gate 구조를 반영

---

## Storage Layout RFC 0001 Accepted — 2026-07-03

Fable 6차 Re-Review Pass와 CEO 최종 승인 반영.

### Changed

- RFC 0001 Status를 `Accepted`로 전환
- README를 Design Gates Complete / Implementation Gate 기준으로 갱신
- RFC index에서 RFC 0001 상태를 `Accepted`로 갱신

### Implementation Gate Carryover

- N1: orphan media 복구 규칙
- N2: 월 파티션 단위 쓰기 직렬화
- N3: 백업 스펙(주기, 복원 테스트, 보관 위치, 암호화 키 관리)
- 서버 하드닝 실적용 확인(계정, SSH, 권한)

---

## Storage Layout RFC 0001 C1 Re-review Request — 2026-07-03

Fable 5차 Conditional Pass 조건(C1)과 CEO Decision: Server Access Control 반영.

### Changed

- RFC 0001에 `Server Access Boundary` 절 추가
- Live `DuriStorage/`는 MVP에서 평문 유지, OS 계정 권한과 Mini PC 물리 통제로 보호
- OS 계정 정책 명시: CEO 관리자 계정 1개, 별도 `duri` service user, partner는 OS 계정 없음
- SSH key-only, password login 비활성화, 불필요 OS 계정 금지 명시
- 외부 백업본은 암호화하도록 명시
- 백업 암호화 키 보관 방식은 백업 스펙 Gate의 필수 결정 항목으로 추가

### Gate

- Storage Layout RFC 0001은 아직 Draft
- Fable Storage Layout RFC 0001 C1 Re-review 요청

---

## Storage Layout RFC 0001 Gate Review Request — 2026-07-03

CEO Decision for Storage Layout RFC 0001 반영.

### Changed

- MVP 저장 단위를 월 단위 `metadata.json`으로 확정
- 일 단위 파티션은 파일 크기/성능 문제가 생길 경우 Future Work로 이동
- `DuriStorage/`는 ephemeral filesystem이 아니라 서버 로컬 또는 마운트된 영구
  디스크/볼륨에 저장하도록 명시
- 원본 사진/Message/metadata가 DB보다 우선하는 보존 대상임을 명시
- `metadata.json.tmp` 작성, 검증 후 rename, fsync best effort, 별도 백업 요구사항 추가
- README와 Gate Review 요청을 Storage Layout RFC 0001 Final Review 기준으로 갱신

### Gate

- Storage Layout RFC 0001은 아직 Draft
- Fable Storage Layout RFC 0001 Final Review 요청

---

## PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 — 2026-07-03

Fable 4차 Re-Review Pass와 CEO 최종 승인 반영.

### Changed

- PRD v0.2.5 Draft 해제
- DATA_MODEL v0.4 Draft 해제
- WORKFLOW v0.4 Draft 해제
- ADR-008을 `Accepted`로 전환
- README를 Storage Layout RFC 0001 Draft 유지 및 다음 Gate 기준으로 갱신

### Remaining Gate

- Storage Layout RFC 0001은 Draft 유지
- 구현 착수 전 월/일 파티션과 배포 서버 파일시스템 내구성 보장 수준 확정 필요

---

## Gate Re-review Request Update — 2026-07-03

Fable 3차 Conditional Pass 조건(C1, C2) 반영.

### Added

- **ADR-008 Proposed** — Preservation-first MVP: VaultFolder Curation is Future Work

### Changed

- ADR-002 Decision 3을 원문 복원 후 ADR-008로 supersede 표시
- Auth 운영 데이터와 추억 표시 정체성을 분리
- `metadata.json`에 `participants: { actor_id -> display_name }` 맵을 포함하도록 DATA_MODEL/RFC 정합화
- `messages.md`가 `metadata.json.participants`에서 발화자 이름을 렌더링하도록 명시
- `codex-gate-review-request.md`를 C1/C2 대응 완료 재심사 요청으로 갱신

---

## PRD v0.2.5 Draft / DATA_MODEL v0.4 Draft — 2026-07-03

CEO Decision: VaultFolder is Future Work 반영.

### Changed

- MVP 범위에서 Manual VaultFolder Curation 제거
- README Core Concept를 `Timeline -> View/Index`와 Future Work(`VaultFolder`, `AI View`)로 재정리
- PRD §4.4를 "Search Now, Vault Later"로 변경
- DATA_MODEL에서 `VaultFolder`를 Future Work 엔터티로 이동
- WORKFLOW에서 MVP 사용자 흐름을 채팅/사진/Timeline/Search로 단순화
- Storage Layout RFC에서 `vault/folders/` 구조와 VaultFolder Export 질문 제거
- ADR-002와 EVENT_ENGINE의 "Timeline + Vault" 표현을 "Timeline 보존 + Search" 기준으로 정정

### Gate

- PRD 의미 변경, DATA_MODEL 범위 변경, Storage RFC 변경이므로 Fable Gate Review 요청 대상

---

## RFC 0001 Draft Update — 2026-07-03

CEO clarification 반영.

### Changed

- Export 최상위 폴더 이름을 `DuriArchive/`에서 `DuriStorage/`로 변경
- Auth/User/Device 운영 정보는 Export에서 전면 제외하도록 정리
- VaultFolder Export 질문을 앱 내부 큐레이션과 외부 내보내기 패키지 기준으로 재작성

---

## RFC 0001 Draft — 2026-07-02

Storage Layout RFC 초안 작성.

### Added

- `docs/rfc/0001-storage-layout.md` — `DuriStorage/` 루트, Timeline 월별 원본,
  VaultFolder 큐레이션 Export, Message canonical source, `metadata.json`
  쓰기 무결성 전략 초안
- README Phase 3 상태 갱신

---

## PRD v0.2.4 — 2026-07-02

CEO Decisions for DATA_MODEL과 PRD 표현 정합성 반영. Fable Gate Review와
CEO 최종 승인을 거쳐 확정.

### Changed

- Core User Experience에서 일정 공유를 Future Work로 명시
- Future Work에 추가 Log Type(Schedule, Place, Gift, Note, Voice 등)을 명시

---

## DATA_MODEL v0.3 — 2026-07-02

CEO Decisions for DATA_MODEL 반영. Fable Gate Review와 CEO 최종 승인을 거쳐 확정.

### Added

- **DATA_MODEL v0.3** — MVP Log Type을 `Message`, `Photo`로 제한
- Authentication 엔터티 추가: `User`, `InviteCode`, `Device`, `Session`
- Export-as-storage 원칙 명시 — Markdown / JSON / 원본 사진 파일이 원본 보존 구조
- Search/DB는 원본이 아니라 재생성 가능한 인덱스임을 명시
- **ADR-006 Accepted** — Location Metadata는 사진 EXIF의 GPS 좌표만 원본으로 저장
- **ADR-007 Accepted** — 저장 구조 자체를 Export v1로 취급

### Changed

- Metadata 원칙을 "추출만 하고 해석하지 않는다"로 명확화
- VaultFolder 원본 큐레이션과 Metadata 기반 탐색 View/Index를 분리
- `WORKFLOW.md`의 PWA 성공 조건 표현을 Responsive Web URL 접근으로 수정
- `EVENT_ENGINE.md`의 DATA_MODEL 참조를 v0.3 섹션 구조에 맞게 수정

### Deferred

- Schedule / Place / Gift / Note / Voice Log Type
- AI/NLP 기반 사람·장소·날짜 추출
- GPS -> 장소명 변환
- Location Alias
- AI 자동 분류 / Event Engine

---

## PRD v0.2.3 — 2026-07-02

Phase 1 Gate 반영 (CEO Decision #004, #005). v0.2.2에 대한 Patch.

### Added

- **Delivery Strategy (§7)** — MVP는 반응형 Web Application으로 https://duri.bubblelab.dev 에서 제공. PWA는 선택 가능한 배포 방식 (CEO Decision #004, ADR-004)
- **Security Requirements (§8)** — Self-hosted JWT + Invite Code 인증을 MVP 필수 요구사항으로 포함 (CEO Decision #005, ADR-005)
- MVP 기능에 Authentication (Invite Code), Device Registration 추가
- ADR-001 ~ ADR-005 생성 (`docs/adr/`)
- CHANGELOG.md 도입 — 이후 PRD 본문은 안정 유지, 변경은 이 파일에 기록

### Changed

- **MVP Goal (§6)** — 반응형 Web Application 제공을 명시, PWA는 성공 조건이 아님
- **Ownership (§10)** — 개인 서버 원칙 유지, 공개 접근 시에도 인증을 통해 두 사용자만 접근 가능해야 함을 명시
- **Non Goals (§11)** — Native App, PWA 설치 경험은 MVP 성공 조건이 아님을 추가
- §7 이후 섹션 번호 재정렬 (Delivery Strategy, Security Requirements 신설로 +2)

### Removed

- MVP 기능에서 **PWA** 제외 — 선택 가능한 Delivery Method로 재분류 (ADR-004)

---

## PRD v0.2.2 — 2026-07-02

Timeline First 재정의.

### Added

- First Principle에 «데이터를 오래 보존하고, 필요할 때 똑똑하게 읽는다» 추가
- MVP Goal에 Future Work 목록 추가 (Event Engine, AI 자동 분류 등)
- `docs/DATA_MODEL.md` — Log / Timeline / Vault / View 데이터 모델 (v0.2)
- `docs/EVENT_ENGINE.md` — Event Engine 설계를 Future Work로 보존
- `docs/WORKFLOW.md` — 제품/엔지니어링 워크플로우
- `docs/adr/`, `docs/rfc/` — ADR/RFC 프로세스 도입

### Changed

- **§4.3** — "Logs become Events" → **Timeline First**: MVP에서 Event를 생성하지 않고 Log를 시간순 Timeline으로 저장
- **§4.4** — Vault를 폴더 중심 인터페이스로 재정의
- **§4.5** — "AI grows with Memory" → **AI as Reader**: AI는 원본을 생성/수정하지 않고 View만 생성
- MVP 검증 문장 변경 — «채팅만 했는데 추억이 자동으로 정리된다» → «채팅만 했는데 추억을 잃지 않는다»
- Success Criteria, Guiding Sentence를 보존 중심으로 재정의

### Removed

- MVP 기능에서 **Event 자동 생성** 제외 — Event Engine은 Future Work (ADR-002)

---

## PRD v0.2.1 — 2026-07-02

- PRD 최초 리포지토리 반영 (`docs/PRD.md`)
