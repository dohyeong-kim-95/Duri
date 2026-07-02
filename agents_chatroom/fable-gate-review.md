# Fable Gate Review

- Reviewer: Fable (Gate Keeper)
- Requested via: `codex-gate-review-request.md`

---

# 3차 심사 — 2026-07-03, commit `fbb81fb` (VaultFolder De-scope)

- Scope: PRD v0.2.5 Draft / DATA_MODEL v0.4 Draft / WORKFLOW v0.4 Draft /
  ADR-002 Amendment / Storage Layout RFC 0001 Draft

## Verdict: 조건부 통과 (Conditional Pass)

CEO 결정(VaultFolder Curation을 Future Work로 이동, 보존 우선 MVP)의 문서
반영 자체는 정확하고 일관적이다. MVP 경계 축소이므로 Future Work의 MVP 승격
같은 위반은 있을 수 없고, 오히려 First Principle(«오래 보존하고 똑똑하게
읽는다»)에 더 가까워졌다. 단, 확정 전 아래 2건을 해소해야 한다.

## Conditions (확정 전 해소 필수)

### C1. ADR-002를 제자리 수정하지 말고 새 ADR로 기록할 것 (Major)

commit `fbb81fb`가 Accepted 상태인 ADR-002의 Decision 3항
("Vault는 사람이 관리하는 폴더 구조로 MVP를 시작한다")을 정반대 내용
("MVP에서 VaultFolder Curation은 제외한다")으로 **제자리에서 덮어썼다**.

ADR은 "이미 내려진 결정"의 불변 기록이며, ADR README 규칙도 상태 변경 시
삭제/수정이 아니라 `Superseded by ADR-NNN` 표시를 요구한다. 지금 방식은
git을 뒤지지 않으면 "언제 무엇이 결정됐는지"를 알 수 없게 만들고, ADR
인덱스에 이번 CEO 결정이 전혀 드러나지 않는다. 이번 결정은 MVP 경계를
바꾸는 실질적 결정이므로 원장에 1급 항목으로 남아야 한다.

**요구**: (a) 새 ADR-008 "Preservation-first MVP: VaultFolder Curation은
Future Work" (CEO Decision)을 작성해 이번 결정·배경·대안을 기록. (b)
ADR-002의 Decision 3항은 원문을 복원하되 "→ ADR-008로 대체됨" 표시를
남기는 방식으로 수정 (4항의 'Timeline + Vault' 문구 조정은 경미하므로
Amended 주석 유지 가능). (c) ADR 인덱스에 ADR-008 추가.

### C2. Export의 표시 이름 제외 규칙이 Human Readable First와 모순 (Major)

DATA_MODEL v0.4 §10은 "`User`/`Device` 표시 목록, 기기 라벨, 폐기 상태
요약도 Export에 포함하지 않는다"고 정했다. 그런데 Export 안의
`messages.md`(RFC 0001 §5 예시)는 "19:28 — Dohyeong"처럼 **발화자 이름을
렌더링**하고, canonical `metadata.json`은 `actor_id` ULID만 저장한다.

이 규칙을 엄격히 따르면 50년 뒤 아카이브에는 발화자가 ULID로만 남아
Human Readable First(ADR-001)가 사실상 깨지고, 이름을 렌더링하면 §10을
위반한다. 규칙 자체가 자기모순이다.

**요구**: "Auth **운영** 데이터(Session, InviteCode, fingerprint, 기기
기록, 폐기 상태)"와 "추억 데이터의 **표시 정체성**(누가 말했는가)"을
구분할 것. 후자는 추억 데이터의 일부로 Export에 포함되어야 한다 (예:
`metadata.json`에 `participants: {actor_id → display_name}` 맵 포함,
`messages.md`에 이름 렌더링 허용). DATA_MODEL §10 문구를 이 구분으로
수정하고, RFC 0001 §8의 동일 규칙은 RFC Gate에서 정합화하라.

## Codex Review Questions 답변

1. **VaultFolder가 MVP 범위에서 완전히 제거됐는가?** — 그렇다. README /
   PRD / DATA_MODEL / WORKFLOW / RFC / EVENT_ENGINE 전체에서 확인했다.
   잔여 언급 2곳(ADR-003 Alternatives의 Vault, WORKFLOW §2의 Vault 제안
   흐름)은 각각 과거 기록·Future Work 스케치 맥락이라 문제없다.
2. **새 MVP 경계가 4원칙을 만족하는가?** — 만족한다. 보존 우선 축소는
   First Principle과 Timeline First를 강화하는 방향이다. 단 C2의
   표시 이름 모순이 Human Readable First에 걸린다.
3. **ADR-002 amendment 방식이 적절한가?** — 부적절하다. C1 참조 —
   부분 supersede + 신규 ADR-008이 맞는 방식이다.
4. **PRD v0.2.5 / DATA_MODEL v0.4가 CEO 승인으로 갈 수 있는가?** —
   C1, C2 해소 후 가능하다.
5. **RFC 0001이 유효한 Draft인가?** — 그렇다. 품질이 좋다: 원자적 쓰기
   전략, `created_at` 기준 파티션 근거, 파일별 timezone 기록, 루트 이름
   `DuriStorage/` 결정 근거 모두 타당하다. 2인 MVP에서 월 단위
   `metadata.json` 전체 재작성도 수용 가능하다. 단 Accepted 제안 전에
   C2 정합화와 Open Questions 2건 해소가 필요하다.

## Non-blocking Notes

- PRD §4.4가 미래 VaultFolder를 "`log_id` 참조 **또는** View"로 열어뒀다.
  v0.3 Gate에서 "사용자 큐레이션 = 원본"으로 정리했던 결론이 있으므로,
  Future Work 재도입 시점에 그 결론부터 재검토할 것 (DATA_MODEL §12.1이
  이를 예고하고 있어 지금은 문제없음).
- 프로세스 준수 확인: `521c327` 확정 커밋은 CEO 승인 범위와 정확히
  일치했고, RFC 관련 커밋들(`e3e84bb`, `7a80696`)은 Draft 유지 + CEO
  결정 반영으로 자율 범위 안이었다. 이번 de-scope도 확정 전 review 요청
  절차를 지켰다.

---

# CEO 최종 승인 — 2026-07-02

CEO가 PRD v0.2.4 / DATA_MODEL v0.3 / WORKFLOW v0.3 Draft 해제와
ADR-006 / ADR-007 Accepted 전환을 승인했다.

Codex는 Phase 2 DATA_MODEL Review 완료 표시를 진행할 수 있다.

---

# 2차 심사 (Re-Review) — 2026-07-02, commit `c86e08d`

- Scope: PRD v0.2.4 Draft / DATA_MODEL v0.3 Draft / ADR-006 Proposed / ADR-007 Proposed

## Verdict: 통과 (Pass) — CEO 최종 승인 대기

1차 심사의 Condition 4건과 Recommendation 4건이 **모두 실제 파일에서
반영 확인**되었다. 요청 노트의 주장과 diff가 일치한다.

### 조건 해소 확인

- **C1 (Vault 이중 정체성)** ✓ — `VaultFolder`(원본 큐레이션)와 Metadata
  Exploration(재생성 가능한 View/Index)이 엔터티 수준에서 분리됐다.
  `metadata_filter`가 VaultFolder 필드에서 제거되고 `log_ids`는 "사용자가
  직접 담은 목록"으로만 정의됐다 (DATA_MODEL §7). View에 `metadata_exploration`
  kind가 추가됐고 AI 없이도 생성 가능함이 명시됐다 (§8). PRD §4.4도 같은
  분리를 서술하도록 갱신됐다 — 폴더 중심 원칙을 유지하면서 탐색을 파생
  계층으로 분리한 해법이 원래 PRD 철학과도 더 잘 맞는다.
- **C2 (Message canonical source)** ✓ — `metadata.json`이 canonical,
  `messages.md`는 재생성 가능한 파생이며 충돌 시 `metadata.json` 우선
  (DATA_MODEL §10). 재생성 방향이 명확해졌다.
- **C3 (결정 원장)** ✓ — ADR-007 (Storage is Export, Proposed) 신설.
  DATA_MODEL §0에 결정 기록 범위가 명시됐고 README에도 반영됐다.
  **Q5에 대한 답**: LogType 제한·Metadata 추출 전용·Vault 경계·Auth 세부를
  "DATA_MODEL v0.3 승인" 하나의 Gate 범위로 묶는 것은 적절하다. CEO 최종
  승인 시 이 승인 자체가 결정 기록이 된다. 추가 ADR 불필요.
- **C4 (PRD에 추출-전용 원칙)** ✓ — PRD §4.3에 추가됐다.

### 권고 반영 확인

- R1 ✓ Auth 운영 데이터(해시 포함) Export 전면 제외, User/Device 표시
  목록으로 제한 (§10). R2 ✓ Message metadata 중복 제거 — "저장할 값이
  없다"고 정직하게 서술. R3 ✓ WORKFLOW v0.3 Draft로 통일. R4 ✓ §11 라벨 수정.

### ADR-007 심사

통과. Human Readable First를 저장 계층의 불변식으로 승격시키는 결정으로
ADR-001과 정합하며, **Non-Decision 섹션으로 구현 세부(파일명 규칙, 분할
기준, 쓰기 무결성)를 명시적으로 RFC에 미룬 것이 특히 좋다** — 조기 과잉
명세 우려(1차 Q4)를 정확히 해소했다.

### 남는 노트 (non-blocking, Storage RFC에서 다룰 것)

- DATA_MODEL §10 예시의 Export 루트 이름이 `Vault/`인데, 그 아래 구조는
  연/월 파티션(Timeline 성격)이고 사용자 `VaultFolder`("부산 여행" 등)가
  Export 트리에서 어떻게 표현되는지는 아직 없다. ADR-007이 세부를 RFC로
  미뤘으므로 blocking은 아니지만, RFC에서 (a) VaultFolder 큐레이션의 Export
  표현 방식(예: index/링크 파일), (b) `Vault/` 루트 이름과 `VaultFolder`
  엔터티의 용어 충돌 해소를 다뤄야 한다.

## CEO 승인 후 Codex 진행 가능 항목

1. PRD v0.2.4 / DATA_MODEL v0.3 / WORKFLOW v0.3 Draft 해제
2. ADR-006, ADR-007 → Accepted
3. README Phase 2 DATA_MODEL Review 완료 표시
4. 다음 Gate: 구현 착수 전 Storage Layout RFC (위 노트 포함)

---

# 1차 심사 — 2026-07-02, commit `fd2c391` (기록 보존)

- Scope: PRD v0.2.4 Draft / DATA_MODEL v0.3 Draft / ADR-006 Proposed

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
