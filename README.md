# Duri

> «Live together. Log automatically. Remember forever.»

Duri는 우리 둘이 함께 살아가는 모든 순간을 자동으로 기록하고, 구조화하며,
평생 간직할 수 있도록 돕는 **Personal Life System**이다.

메신저를 만드는 것이 목적이 아니다. 채팅, 사진, 일정, 장소, 메모, 선물,
데이트 같은 일상의 기록을 잃지 않도록 시간순으로 보존하고, 미래에 어떤
방식으로든 다시 활용할 수 있는 형태로 남기는 시스템을 만드는 것이 목적이다.

자세한 배경과 원칙은 [docs/PRD.md](docs/PRD.md)를 참고한다.

---

## CEO Dashboard

### Current Phase

**Phase 4 — 구현 착수 가능** (Design Gates Complete)

### Current MVP

- Responsive Web
- 1:1 Chat (`Message` Log)
- Photo Sharing (`Photo` Log)
- Timeline
- Deterministic Metadata (AI 해석 없음)
- Metadata-based Timeline Exploration
- Search
- Export-as-storage / Automatic Backup
- Authentication (Self-hosted JWT + Invite Code)
- Device Registration / Revocation

### Deployment

https://duri.bubblelab.dev

### Current Decisions

| # | Decision | Record |
|---|----------|--------|
| ADR-001 | Human Readable First | [docs/adr/ADR-001](docs/adr/ADR-001-human-readable-first.md) |
| ADR-002 | Timeline First (Event Engine은 Future Work) | [docs/adr/ADR-002](docs/adr/ADR-002-timeline-first.md) |
| ADR-003 | AI generates Views, not Data | [docs/adr/ADR-003](docs/adr/ADR-003-ai-generates-views-not-data.md) |
| ADR-004 | Responsive Web First (CEO Decision #004) | [docs/adr/ADR-004](docs/adr/ADR-004-responsive-web-first.md) |
| ADR-005 | Invite-code based two-person authentication (CEO Decision #005) | [docs/adr/ADR-005](docs/adr/ADR-005-invite-code-two-person-auth.md) |
| ADR-006 | Raw GPS Location Metadata (CEO Decision #006) | [docs/adr/ADR-006](docs/adr/ADR-006-raw-gps-location-metadata.md) |
| ADR-007 | Storage is Export (CEO Decision #007) | [docs/adr/ADR-007](docs/adr/ADR-007-storage-is-export.md) |
| ADR-008 | Preservation-first MVP: VaultFolder is Future Work | [docs/adr/ADR-008](docs/adr/ADR-008-preservation-first-mvp-vaultfolder-future-work.md) |

### Current Architecture

Design Gates Complete — Storage/Auth Service Gates Closed

`DATA_MODEL.md` v0.4는 다음 CEO 결정을 반영한다.

1. MVP Log Type은 `Message`, `Photo`만 지원한다.
2. Metadata는 추출만 하고 해석하지 않는다. AI/NLP 분류는 Future Work다.
3. MVP에서 VaultFolder Curation은 제외한다. Metadata 기반 탐색 결과는 재생성 가능한 View/Index다.
4. 저장 구조 자체가 Export다. DB는 검색/성능용 인덱스다.
5. Authentication은 Self-hosted JWT + Invite Code + 기기별 Refresh Session으로 설계한다.
6. 위치 Metadata는 사진 EXIF의 GPS 좌표만 원본으로 저장한다. 장소명/Alias는 Future Work의 View다.
7. 초기 구현 스택은 TypeScript + Next.js frontend, Python + FastAPI backend,
   FastAPI WebSocket, SQLite index/cache, filesystem `DuriStorage/` source of truth다.

기록 방식: 1, 2, 5는 `DATA_MODEL.md` v0.4 승인 범위에 묶고, 3은 ADR-008,
4는 ADR-007, 6은 ADR-006으로 기록한다.

### Next Gate

Implementation Gate

Accepted storage RFC: [docs/rfc/0001-storage-layout.md](docs/rfc/0001-storage-layout.md)

Implementation plan: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)

설계 Gate는 닫혔다. 구현 착수는 가능하다.

CI 기준선: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)이 모든 push/PR에서
공백 검사와 Markdown 로컬 링크 검사를 실행한다. Fable Gate Acceptance Spec이
도착하면 해당 테스트를 이 CI에 추가한 뒤 Gate review를 요청한다.

Storage Writer Step 2는 Fable Gate Acceptance Spec v1.1 A1~A5를 테스트로
먼저 작성해 실패를 확인한 뒤 구현했고, 9차 심사에서 Gate 통과가 확인됐다.

Auth/Session Step 3은 Fable Gate Acceptance Spec v1.2 B1~B4를 테스트로
먼저 작성해 실패를 확인한 뒤 구현했다. 10차 심사 C1(서명 키/해시 키
도메인 분리)을 반영했고, 11차 심사에서 Gate 통과가 확인됐다.

다만 등록/로그인/갱신/폐기 HTTP 인증 엔드포인트와 photo upload persistence는
아직 구현하지 않았다. 이 둘은 별도 Gate review 대상이다.

예정된 1회성 적대적 보안 점검은 지금이 아니라, HTTP 인증 엔드포인트와
업로드 경로가 구현된 뒤 첫 배포 직전에 수행한다.

구현 Gate 이월 확인 항목:

- N1: orphan media 복구 규칙
- N2: 월 파티션 단위 쓰기 직렬화
- N3: 백업 스펙(주기, 복원 테스트, 보관 위치, 암호화 키 관리)
- 서버 하드닝 실적용 확인(계정, SSH, 권한)
- 배포 직전 적대적 보안 점검(10차 심사 이월 관찰 6건 기준)

Gate 통과:

- Storage Writer internal module
- Fable Gate Acceptance Spec A1~A5 pytest suite (`gate_spec`)
- temp file + atomic rename write path
- rename 전 temp media size/sha256 verification
- app timezone canonical timestamp normalization
- `messages.md` regeneration
- orphan media recovery
- SQLite timeline index rebuild from `DuriStorage/`
- Auth/Session internal module
- Fable Gate Acceptance Spec B1~B4 pytest suite (`gate_spec`)
- two-person invite-code registration limit
- one-time invite consumption
- no plaintext invite code / refresh token storage
- separated signing key and hash key domains
- auth operating data kept outside `DuriStorage/`
- protected Timeline, photo, search, and Timeline WebSocket access
- access token expiry rejection
- refresh session access token renewal
- per-device session revocation

Gate 불필요 read-only 구현 완료:

- `GET /timeline` reads Timeline logs from `DuriStorage/metadata.json`
- `GET /timeline/summary` returns read-only period/type counts for exploration
- `GET /search?q=...` filters Timeline logs from `DuriStorage/metadata.json`
- Timeline/Search support read-only period and log type filters
- SQLite Timeline index can be rebuilt and queried from `DuriStorage/`
- Frontend Timeline/Search shell calls the read-only APIs when a future auth token exists

다음 Gate review 필요:

- registration/login/refresh/revocation HTTP auth endpoints
- photo upload persistence
- backup/export implementation

이미 완료된 자율 범위:

- frontend/backend scaffold
- dependency installation
- lint/typecheck/test setup
- basic CI
- empty healthcheck endpoint
- WebSocket proof-of-connection test

아직 구현 금지:

- public message write endpoint
- photo upload persistence
- public photo upload endpoint
- backup/export implementation

---

## Core Concept

```
Chat / Photo (MVP) / Schedule / Place / Note ... (Future Work)
        │  (사용자는 그냥 살아간다)
        ▼
      Log            모든 기록의 최소 단위 (원본, Metadata 자동 축적)
        ▼
   Timeline          Log가 시간 순으로 그대로 이어진 기록 (MVP는 Event 없이 바로 여기로)
        └── View/Index      Metadata 기반 탐색 결과

Future Work
  ├── VaultFolder     사용자가 직접 담거나 AI가 제안하는 큐레이션
  └── AI View         원본을 읽어 만드는 요약/추천/분류
```

Duri는 **Timeline First**를 따른다. MVP에서는 Event를 자동 생성하지
않으며([PRD §4.3](docs/PRD.md#43-timeline-first)), Event 자동 클러스터링은
Timeline 보존 경험이 검증된 이후의 Future Work다.

## Documents

- [docs/PRD.md](docs/PRD.md) — 제품 정의 (v0.2.5)
- [CHANGELOG.md](CHANGELOG.md) — PRD/주요 결정 변경 이력
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — Log / Timeline / Search / View 데이터 모델 (v0.4)
- [docs/WORKFLOW.md](docs/WORKFLOW.md) — 사용자 행동부터 Search까지 이어지는 전체 워크플로우
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — 구현 착수 순서와 Gate 경계
- [docs/EVENT_ENGINE.md](docs/EVENT_ENGINE.md) — (Future Work) Log가 Event로 자동 연결되는 규칙과 파이프라인 스케치
- [docs/adr](docs/adr) — Architecture Decision Records
- [docs/rfc](docs/rfc) — Request for Comments

## Development

```bash
npm run dev:web
.venv/bin/uvicorn duri_api.main:app --app-dir apps/api/src --reload
```

```bash
bash scripts/ci.sh
```

## Ownership

모든 데이터와 코드는 우리 둘만을 위한 것이다. 공개 서비스나 수익화를
목표로 하지 않는다. 공개 URL로 배포되더라도 인증을 통해 두 사용자만
접근할 수 있다. 자세한 내용은 [docs/PRD.md](docs/PRD.md#10-ownership),
[docs/PRD.md](docs/PRD.md#11-non-goals) 참고.

---

## Phase 1 Gate Completion Criteria

- [x] PRD.md에 Decision #004, #005가 반영되어 있다. (PRD v0.2.3 §7, §8)
- [x] ADR-001 ~ ADR-005가 리포지토리에 기록되어 있다.
- [x] README가 CEO Dashboard 역할을 수행한다.

## Phase 2 Gate Completion Criteria

- [x] CEO Decisions for DATA_MODEL.md 수령
- [x] DATA_MODEL.md v0.3에 Auth / Device / Session 모델 반영
- [x] ADR-006 Accepted
- [x] ADR-007 Accepted
- [x] Claude Code Fable DATA_MODEL Review 통과
- [x] CEO final approval

## VaultFolder De-scope Gate Completion Criteria

- [x] Storage Layout RFC Draft 작성
- [x] CEO Decision: VaultFolder is Future Work 수령
- [x] ADR-008 작성
- [x] Fable VaultFolder De-scope / Storage Layout Review 통과
- [x] CEO final approval
- [x] PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 Draft 해제
- [x] ADR-008 Accepted

## Storage Layout RFC 0001 Gate Completion Criteria

- [x] Storage Layout RFC 0001 Draft 작성
- [x] 월 단위 `metadata.json` 유지 확정
- [x] 영구 디스크/볼륨 기준 파일 저장 보장 확정
- [x] Server Access Boundary 반영
- [x] Fable Storage Layout RFC 0001 Final Review 통과
- [x] CEO final approval
- [x] Storage Layout RFC 0001 Accepted
