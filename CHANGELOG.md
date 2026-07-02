# Changelog

Duri 문서(PRD 및 주요 결정)의 변경 이력을 기록한다.

포맷은 [Keep a Changelog](https://keepachangelog.com/)를 따른다.

---

## PRD v0.2.3 — 2026-07-02

Phase 1 Gate 반영 (CEO Decision #004, #005).

### Added

- **Delivery Strategy (§7)** — MVP는 반응형 Web Application으로 https://duri.bubblelab.dev 에서 제공. PWA는 선택 가능한 배포 방식 (CEO Decision #004)
- **Security Requirements (§8)** — Self-hosted JWT + Invite Code 인증을 MVP 필수 요구사항으로 포함 (CEO Decision #005)
- MVP 기능에 Authentication (Invite Code), Device Registration 추가
- ADR-001 ~ ADR-005 생성 (`docs/adr/`)
- CHANGELOG.md 도입 — 이후 PRD 본문은 안정 유지, 변경은 이 파일에 기록

### Changed

- **MVP Goal (§6)** — 반응형 Web Application 제공을 명시, PWA는 성공 조건이 아님
- **Ownership (§11)** — 개인 서버 원칙 유지, 공개 접근 시에도 인증을 통해 두 사용자만 접근 가능해야 함을 명시
- **Non Goals (§12)** — Native App, PWA 설치 경험은 MVP 성공 조건이 아님을 추가

### Removed

- MVP 기능에서 **Event 자동 생성** 제외 — Event Engine은 Future Work (ADR-002)
- MVP 기능에서 **PWA** 제외 — 선택 가능한 Delivery Method로 재분류 (ADR-004)

---

## PRD v0.2.1 — 2026-07-02

- PRD 최초 리포지토리 반영 (`docs/PRD.md`)
