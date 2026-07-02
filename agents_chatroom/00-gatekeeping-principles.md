# Gatekeeping Principles

- Date: 2026-07-02
- Author: Fable (Gate Keeper)
- Approved by: CEO
- Audience: Codex (Architect)
- Status: Active — 이 문서는 상시 유효한 협업 원칙이다 (dated note 아님)

---

## 역할

| 역할 | 담당 | 권한 |
|------|------|------|
| CEO (사람) | 최종 의사결정 | 모든 결정의 최종 승인. "CEO Decision #NNN"으로 기록 |
| Codex (Architect) | 설계·산출물 작성 | PRD/ADR/RFC/데이터 모델/코드의 제안과 작성 |
| Fable (Gate Keeper) | 심사·검증 | Gate 대상의 통과/반려 심사 후 CEO에게 보고. 직접 설계·구현하지 않음 |

## Gate의 기준

**"되돌리기 어려운 결정인가."** Duri의 핵심 가치는 원본의 영구 보존이므로,
한번 정하면 미래 데이터 전체를 구속하는 것만 Gate를 거친다. 원본으로부터
재생성 가능한 것(View, UI, 문서 정리)은 Architect가 자율로 진행한다.

## Fable 심사 필수 (Gate 대상) — 확정 전에 반드시 review 요청

1. **Phase Gate 판정** — 각 Phase 완료 선언. Fable이 완료 기준 충족 여부를 심사해 CEO에게 통과/반려 보고.
2. **PRD 본문의 의미 변경** — First Principle, MVP 범위, Non Goals, Security Requirements 등. 의미가 바뀌면 한 줄이라도 심사 대상 (오탈자 수정 제외).
3. **RFC → ADR 확정** — RFC 초안 작성·논의는 자율. 단 `Accepted` 확정과 ADR 등록 직전에 심사 (기존 ADR과의 충돌, First Principle 통과 여부).
4. **데이터 모델·스토리지 포맷·Export 포맷 확정** — 스키마, 파일/디렉토리 규칙, 마이그레이션 등 저장된 데이터를 구속하는 모든 결정.
5. **원본 데이터·보안을 만지는 코드** — Log 쓰기/수정/삭제 경로, 백업, 인증/기기 관리(ADR-005 영역)의 구현.

## Codex 자율 진행 — 수정 전 inform만 하면 됨

- 문서 오탈자·링크·섹션 번호 정합성, CHANGELOG 기록, README Dashboard 갱신
- RFC **초안** 작성 및 수정 (Draft 상태인 동안)
- 읽기 전용 코드: View 생성, 검색, UI, Timeline 조회
- 테스트, 개발 환경 설정, 리팩터링 (원본 쓰기 경로를 건드리지 않는 한)

## Gate review 절차

1. Codex는 Gate 대상 작업을 마치면 이 폴더의 **`codex-gate-review-request.md`**를
   갱신해 review를 요청한다 (CEO 확정 채널, 2026-07-02).
   변경 파일 목록, 적용한 CEO Decision, 검증 방법, 중점 확인 요청 사항을 포함한다.
2. Fable은 PRD First Principle, ADR-001~ 정합성, 문서 간 일관성, Non Goals
   위반 여부를 기준으로 심사하고, 결과(통과/조건부 통과/반려 + 지적 사항)를
   **`fable-gate-review.md`**에 남기고 CEO에게 보고한다.
3. 반려 시 Codex가 수정 후 재요청한다. 최종 확정(merge, ADR Accepted 등)은
   CEO 승인 후에만 진행한다.

## 구현 단계 Gate 구조: TDD as Executable Gate (CEO 승인, 2026-07-03)

구현 단계부터 Gate 통과 조건은 가능한 한 **실행 가능한 테스트**로 표현한다.

### 역할 분담

- **Fable**: 구현 착수 전, Gate 대상 ⑤ 영역의 불변식을 **Gate Acceptance
  Spec**(행위 수준의 필수 테스트 목록)으로 작성한다. 코드가 아니라
  "이런 테스트가 존재하고 통과해야 한다"는 명세다.
- **Codex**: TDD로 구현한다 — Spec의 테스트를 먼저 작성하고 실패를 확인한
  뒤 구현한다. Spec 외의 단위 테스트는 자율 범위다.
- **CI**: 모든 커밋에서 전체 테스트를 자동 실행한다. CI 구성 자체가 구현
  1순위 작업이다. Gate review 요청 시 녹색 CI가 전제 조건이다.

### 규칙

1. Fable의 Gate 조건은 "~를 증명하는 테스트를 추가/강화하라" 형태로
   발행될 수 있으며, 해당 테스트의 **존재 + 통과**가 통과 조건이 된다.
2. Coverage는 퍼센트 지표가 아니라 **필수 행위 목록의 충족**으로 판정한다.
3. Gate Acceptance Spec에 속한 테스트의 약화·삭제·skip은 그 자체가 Gate
   대상이다 — Fable review 없이 진행할 수 없다.
4. 테스트 이름은 행위 문장으로 쓴다 (예: "세 번째 초대 코드 등록 시도는
   거부된다"). CEO가 테스트 목록과 통과 여부만 보고 시스템이 보증하는
   바를 읽을 수 있어야 한다 — 이것이 CEO의 코드 리딩을 대체한다.
5. Fable의 코드 심사는 전체 코드가 아니라 ① 테스트가 Spec을 실제로
   검증하는지, ② 필수 테스트의 약화 여부, ③ 위험 경로(원본 쓰기·인증)
   diff에 집중한다.

### 보안 점검

인증/접근 통제 구현이 완료되면, Fable이 공격 시나리오 체크리스트 기반의
**1회성 적대적 점검**을 수행한다 (상설 절차 아님, CEO 결정 2026-07-03).

## 심사 기준 (Fable이 적용하는 체크리스트)

- First Principle: «사용자는 기록하지 않는다» / «오래 보존하고 똑똑하게 읽는다» (PRD §3)
- Human Readable First (ADR-001)
- Timeline First — Event는 Future Work (ADR-002)
- AI as Reader — AI는 View만 생성, 원본 불변 (ADR-003)
- Responsive Web First (ADR-004), Self-hosted Auth (ADR-005)
- Non Goals (PRD §11) 위반 없음 — Future Work가 MVP 요구사항으로 슬며시 승격되지 않았는지
- 문서 간 상호 참조 정합성 (PRD ↔ DATA_MODEL ↔ WORKFLOW ↔ ADR ↔ README ↔ CHANGELOG)
