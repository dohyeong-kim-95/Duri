# Changelog

Duri 문서(PRD 및 주요 결정)의 변경 이력을 기록한다.

포맷은 [Keep a Changelog](https://keepachangelog.com/)를 따른다.

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
