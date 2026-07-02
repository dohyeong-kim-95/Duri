# Changelog

Duri 문서(PRD 및 주요 결정)의 변경 이력을 기록한다.

포맷은 [Keep a Changelog](https://keepachangelog.com/)를 따른다.

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
