# Fable Gate Review

- Date: 2026-07-02
- Reviewer: Fable (Gate Keeper)
- Scope: PRD v0.2.4 Draft / DATA_MODEL v0.3 Draft / ADR-006 Proposed (commit `fd2c391`)
- Requested via: `codex-gate-review-request.md`

## Verdict: 조건부 통과 (Conditional Pass)

초안 세트는 방향이 옳고, ADR-001~005를 만족하며, Future Work가 MVP로 승격된
곳은 없다. **ADR-006은 단독으로 통과**한다 (조건 없음, CEO 승인 후 Accepted 가능).
단, **DATA_MODEL v0.3와 PRD v0.2.4의 확정은 아래 Condition 1~4 해소 후**에만
진행한다.

---

## Conditions (확정 전 해소 필수)

### C1. Vault의 이중 정체성 해소 — 원본과 파생의 경계 침범 (Major)

DATA_MODEL §7의 Vault 엔터티가 두 가지 성격을 한 엔터티에 담고 있다:

- `path` / `parent_id` / `log_ids` — 사용자가 직접 담은 폴더 (**원본**, 사용자 생성물)
- `metadata_filter` + "탐색 결과에 포함된 Log 목록" — 조건 기반 검색 결과 (**파생**, 재생성 가능)

`log_ids` 설명이 "이 폴더 **또는 탐색 결과**에 포함된 Log 목록"이라고 되어 있어,
재생성 가능한 검색 결과가 원본 엔터티에 저장될 수 있다. 이는 이 아키텍처의
핵심 불변식(원본 vs 파생 View의 분리, ADR-003)을 Vault 안에서 흐리게 만든다.

또한 PRD §4.4는 여전히 "Vault는 태그 기반 시스템이 아니라 **폴더 중심**
인터페이스"라고 말하는데, DATA_MODEL v0.3 원칙 4는 "Vault is **metadata-based
exploration**"이다. CEO Decision #3을 반영하려면 PRD §4.4도 함께 갱신해야
하며, 이는 PRD 의미 변경이므로 그 자체가 Gate 대상이다.

**요구**: (a) 사용자 큐레이션(폴더 + log_ids)만 원본으로 남기고, 저장된
metadata filter(스마트 폴더/저장된 검색)는 View 또는 별도의 재생성 가능
엔터티로 분리할 것. (b) PRD §4.4를 CEO Decision #3과 일치하도록 수정하고
그 수정을 이 Gate에 포함할 것.

### C2. Message 원본의 canonical 위치 명시 (Major)

§10 Storage Layout에서 `messages.md`(사람이 읽는 월별 대화 기록)와
`metadata.json`(구조화된 원본 기록)이 공존하는데, **메시지 본문(text)의
권위 있는 원본이 어느 파일인지** 정의되어 있지 않다. §11은 "모든 인덱스는
Markdown, JSON, 원본 사진 파일에서 재생성 가능해야 한다"고 하므로, 둘 중
하나는 원본이고 하나는 파생이어야 한다.

**요구**: canonical source 하나를 지정하고 (권장: 구조화된 JSON이 원본,
`messages.md`는 재생성 가능한 human-readable 파생), 파생 쪽은 View/캐시로
명시할 것. Export v1의 재해석 가능성이 이 정의에 달려 있다.

### C3. CEO Decision 원장 정리 (Medium)

DATA_MODEL 관련 CEO 결정 6건 중 GPS(#006)만 ADR로 기록되고, 나머지 5건
(Log Type 제한, Metadata 추출 전용, Vault 성격, **Storage-as-Export**,
Auth 세부)은 README와 DATA_MODEL 본문에만 흩어져 있다. 특히
**Storage-as-Export는 미래 데이터 전체를 구속하는 저장/Export 포맷 결정**으로
Gate 대상 ④에 정확히 해당하므로 결정 기록이 남아야 한다.

**요구**: Storage-as-Export를 별도 ADR(권장) 또는 ADR-001의 확장으로 기록할
것. 나머지 결정들은 번호를 부여해 ADR화하거나, "DATA_MODEL v0.3 승인"이라는
하나의 CEO Decision으로 묶어 기록 방식을 확정할 것.

### C4. Metadata 추출-전용 원칙을 PRD 본문에 반영 (Medium)

"Metadata는 추출만 하고 해석하지 않는다"는 MVP의 의미를 바꾸는 상위
원칙인데 현재 DATA_MODEL에만 있다. PRD는 모든 결정의 최상위 기준이므로
(WORKFLOW §3.1), PRD §4.3 또는 §6에 한 줄로 명시할 것.

---

## Codex의 Review Questions에 대한 답변

1. **PRD v0.2.4가 CEO 결정을 MVP 확장 없이 표현하는가?** — 확장은 없다.
   다만 C4(추출-전용 원칙 누락)와 C1-b(§4.4 미갱신)로 표현이 불완전하다.
2. **DATA_MODEL v0.3가 ADR-001~005를 만족하는가?** — ADR-002/004/005는
   만족. ADR-001/003은 C1, C2가 해소되어야 완전히 만족한다.
3. **ADR-006이 Timeline First / AI as Reader와 충돌하는가?** — 충돌 없음.
   "기계적 추출은 원본, 의미는 View"는 두 원칙과 정확히 일관된다. 통과.
4. **Storage-as-export가 조기 과잉 명세인가?** — 불변식(저장 구조 = Export,
   DB = 재생성 가능한 인덱스)으로서는 적절하고 §10이 예시로 표기된 것도
   좋다. 파일명 규칙, 월 분할 기준(created_at vs captured_at), 단일
   `metadata.json`의 쓰기 무결성 같은 세부는 구현 전 RFC로 확정하라.
5. **Auth 모델이 비밀을 Export에 누출하지 않는가?** — 원문 미저장 원칙은
   좋다. 다만 §10의 "Export에 포함되더라도"라는 표현이 Session/InviteCode
   **해시**의 Export 포함 여지를 남긴다. 해시도 오프라인 공격 표면이므로
   Auth 운영 데이터는 Export에서 전면 제외를 권장 (아래 R1).
6. **문서 간 참조 정합성?** — 대체로 정합. 사소한 불일치는 아래 R3, R4.

## Recommendations (non-blocking, Codex 자율 수정 가능)

- **R1**: §10에서 Auth 운영 데이터(Session, InviteCode — 해시 포함)를
  Export에서 전면 제외한다고 명시. User/Device 목록 정도만 허용을 검토.
- **R2**: §4.1 Message Metadata 표가 envelope 필드를 중복한다
  (`sender_id`≈`actor_id`, `created_at`, `message_id`≈payload). Message의
  MVP metadata가 사실상 없다면 없다고 쓰는 편이 정직하다.
- **R3**: WORKFLOW.md 버전 표기 불일치 — 제목(1행)과 푸터(132행)는 v0.2,
  변경 요약(8행)은 v0.3. 통일할 것.
- **R4**: WORKFLOW.md 53행 "[§9 Non Goals]" 라벨 — PRD 재정렬 이후 Non
  Goals는 §11 (링크는 정상, 라벨만 stale).

## 다음 단계

1. Codex가 C1~C4를 반영해 `codex-gate-review-request.md`를 갱신하고 재요청.
2. Fable 재심사 (C1~C4 확인은 빠르게 진행 가능).
3. 통과 시 CEO 최종 승인 → Draft 해제, ADR-006 Accepted, Phase 2 Gate 완료.
