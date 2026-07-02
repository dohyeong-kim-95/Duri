# Fable Gate Review

- Reviewer: Fable (Gate Keeper)
- Requested via: `codex-gate-review-request.md`

---

# 11차 심사 (Re-Review) — 2026-07-03, commit `e6c5d2b` (Step 3 C1 해소)

- Scope: 10차 심사 C1 (서명 키/해시 키 도메인 분리) 해소 확인

## Verdict: 통과 (Pass) — Step 3 Auth/Session Gate 종료

- **C1 해소** ✓ — `AuthService`가 `jwt_secret`과 별도의 `hash_secret`을
  요구하고, 동일 값 설정을 생성자에서 거부한다 (Fable이 직접 확인).
  저장 해시는 용도별 도메인 접두어(`duri-auth:{purpose}:v1`)로 분리됐고
  버전 태그까지 포함해 미래 해시 마이그레이션 여지도 남겼다 — 요구보다
  한 단계 좋은 구현이다.
- **B2-4 테스트** ✓ — 같은 DB에서 서명 키만 교체한 인스턴스로 구 access
  token 거부 + 기존 refresh token 갱신 성공 + 새 토큰으로 실제 엔드포인트
  200 응답까지 검증. red 상태 기록 확인. 기존 테스트 약화 없음.
- Fable 환경 전체 31건 통과. Spec B 13개 항목(B1-1~B4-2) 전부 종료.
- 부수: Codex가 구식 계획 노트 2건(`2026-07-02-data-model-v03-gate-note.md`,
  `2026-07-03-storage-layout-rfc-0001-gate-plan.md`)을 삭제 — 자신의 작업
  노트이고 git 이력에 보존되므로 허용. Fable 심사 기록은 본 파일에 온전하다.

## Step 3 Gate 종료 판정 및 적대적 점검 시점

Spec A(16) + B(13) = 29개 Gate 테스트 전부 존재·통과. 서비스 계층의
Storage/Auth Gate가 모두 닫혔다.

**적대적 보안 점검 시점 판단**: 예정된 1회성 점검은 등록/로그인/갱신/폐기
**HTTP 엔드포인트**와 업로드 경로가 구현된 뒤, **첫 배포 직전**에 수행하는
것이 옳다. 현재는 공격 표면(HTTP)이 아직 없어서 지금 점검하면 실제 공격
벡터(rate limiting, 토큰 전달 방식, CORS 등)를 검증할 수 없다. 10차 심사의
이월 관찰 6건이 그 점검의 시작 체크리스트다.

---

# 10차 심사 — 2026-07-03, commit `597849c` (Step 3: Auth/Session)

- Scope: Gate 대상 ⑤ — `auth.py` + `main.py` 보호 엔드포인트 + Spec B 테스트 12건

## Verdict: 조건부 통과 (Conditional Pass)

TDD 절차 준수, Spec B 12개 항목이 1:1로 존재하며 테스트가 정직하다
(SQLite raw 바이트 스캔으로 원문 부재 검증, 실 ASGI 전송으로 401 검증,
2기기 시나리오로 폐기 격리 검증). Fable 환경에서 전체 30건 통과 재확인.

**Fable 즉석 스팟체크 (전부 방어 성공)**: ① 다른 키로 서명한 토큰 위조
거부, ② 페이로드 변조(user_id 바꿔치기) 거부, ③ **기기 폐기 시 만료 전
access token도 즉시 무효** — 요청마다 세션 상태를 DB에서 확인하는 설계
덕분에 일반적인 JWT 구성보다 강하다. 좋은 설계다.

**HTTP 표면 확인**: 등록/세션 발급/폐기는 아직 엔드포인트로 노출되지 않음
(서비스 계층만 구현). 데이터 엔드포인트 4종은 auth_service 부재 시에도
401을 반환하는 deny-by-default. 원본 쓰기·업로드가 Step 3에 섞이지 않음 확인.

## Condition (Step 3 Gate 통과 전 해소 필수)

### C1. 서명 키와 해시 키의 도메인 미분리 (Major — 지금이 마지막 싼 수정 시점)

`_hash_secret`이 **JWT 서명 키(`jwt_secret`)를 그대로** 초대 코드·refresh
token·기기 fingerprint의 HMAC 해시 키로 재사용한다. 문제는 키 회전 시나리오:
토큰 유출이 의심되어 서명 키를 교체하는 순간, 저장된 **모든 해시가 무효**가
되어 두 사용자의 refresh session 전체와 미사용 초대 코드가 소리 없이 죽는다.
비밀번호가 없는 시스템이라 재로그인 경로도 없으므로 서버 관리자가 수동
복구해야 한다. 해시는 DB에 저장되는 데이터라서, 배포 후 고치려면 전원
재등록이 필요하다 — 실데이터가 없는 지금이 마지막 싼 수정 시점이다.

**요구**: 서명 키와 해시 키를 분리하라 (별도 secret 또는 도메인 접두어
파생 키 — 예: `HMAC(secret, "hash:invite:" + value)` 방식으로 용도별 분리).
Spec **B2-4** (v1.2 추가)의 테스트로 증명하라: 같은 DB에 서명 키만 교체한
인스턴스에서 기존 refresh token 갱신이 성공하고 구 access token은 거부된다.

## 적대적 점검(예정)으로 이월하는 관찰 사항

Step 3 통과 후 수행할 1회성 보안 점검에서 다룰 항목으로 기록만 해둔다:

- 공개 URL 전제인데 rate limiting/lockout 없음 (초대 코드·토큰 온라인 추측)
- WS 인증 토큰이 query string으로 전달 — 프록시/로그 잔류 가능성
- Refresh token rotation 미적용 (탈취 시 180일 유효)
- 중복 fingerprint/중복 초대 코드 등록 시 IntegrityError → 500 (미처리 예외)
- 키 회전 후 기존 사용자의 재인증 경로 부재 (운영 절차 필요)
- **향후 등록/갱신/폐기 HTTP 엔드포인트 추가는 별도 Gate 대상** — 서비스
  계층이 통과해도 HTTP 노출 시점에 다시 심사한다.

---

# 9차 심사 (Re-Review) — 2026-07-03, commit `9fda760` (Step 2 조건 해소)

- Scope: 8차 심사 C1/C2 해소 확인 (Spec v1.1 — A2-4, A5-4)

## Verdict: 통과 (Pass) — Step 2 Storage Writer Gate 종료

- **C1 (타임존 정규화)** ✓ — `_base_log`가 `created_at`/`ingested_at`을
  앱 타임존으로 정규화해 저장한다. A5-4 테스트가 8차의 실증 시나리오
  그대로(KST 먼저, 1초 뒤 UTC 표기)를 검증하고, 정규화된 문자열까지 정확히
  단언한다. **Fable이 8차에서 사용한 재현 스크립트를 재실행해 결함 소멸을
  직접 확인했다** (실제 순서 정렬 + 전체 +09:00 표기).
- **C2 (rename 전 해시 검증)** ✓ — `_verify_file_matches_bytes`가 rename
  직전에 크기+sha256을 원본 바이트와 비교하고 불일치 시 거부한다. A2-4
  테스트가 hook으로 temp 파일을 실제로 손상시켜 거부·무잔류(photos/,
  metadata.json 모두)를 검증한다. hook 실행 → 검증 → rename 순서라 손상
  주입이 검증보다 앞서는 것도 올바르다.
- TDD 절차 준수 (A2-4/A5-4 red 상태 기록 후 수정), 기존 Spec 테스트 약화
  없음 (diff로 확인 — 추가만 있음). 전체 18건 Fable 환경 통과.
- Spec v1.1 파일은 Fable 원문 그대로 커밋됨 (변조 없음 확인).

## Step 2 Gate 종료 판정

Spec A 영역 16개 항목(A1-1~A5-4) 전부 테스트 존재 + 통과. Storage Writer는
Gate 통과. **Codex는 Step 3 (Auth/Session, Spec B 영역)으로 진행 가능** —
Spec B가 이미 발행되어 있으므로 추가 승인 없이 B1-1부터 TDD로 착수하면
된다. 이월 항목: N1(다중 프로세스 직렬화)은 배포/e2e Gate에서 확인.

---

# 8차 심사 — 2026-07-03, commit `aff3c1f` (Step 2: Storage Writer)

- Scope: Gate 대상 ⑤ 첫 코드 심사 — `storage.py` + gate_spec 테스트 14건

## Verdict: 조건부 통과 (Conditional Pass)

TDD 절차 준수(red 상태 기록 후 구현), Spec A1~A5의 14개 테스트가 1:1로
존재하며 전부 정직하게 작성됐다 (hook 기반 장애 주입, 실제 스레드 동시성
검증). Fable 환경에서 전체 16건 통과 재확인. Auth/공개 엔드포인트가
Step 2에 섞여 들어오지 않았음도 확인 (storage.py는 내부 모듈만 노출).
단, 정독 중 결함 1건을 실증했고 RFC 불일치 1건을 확인했다.

## Conditions (Step 2 Gate 통과 전 해소 필수)

### C1. 타임존 혼합 시 Timeline 정렬 붕괴 (Major — 결함 실증됨)

`_base_log`가 `created_at`을 받은 그대로 저장하고, `_sorted_logs`가 이
문자열을 사전순 정렬한다. 서로 다른 offset 표기가 섞이면 정렬이 깨진다.

**실증**: KST 19:28:00에 온 메시지와 1초 뒤(UTC 표기 10:28:01+00:00)에 온
메시지를 저장하면 — 늦게 온 메시지가 Timeline에서 먼저 정렬되고,
`messages.md`에는 "10:28"(UTC)로 표기된다. 향후 업로드 엔드포인트가
서버 UTC 시각을 쓰는 순간 실사용에서 재현된다. Timeline 순서는 이 제품의
핵심 불변식이다.

**요구**: `created_at`/`ingested_at`을 저장 시점에 앱 타임존으로 정규화할
것 (canonical 파일의 시각 표기 일관성은 Human Readable First에도 부합).
Spec **A5-4** (v1.1 추가)의 테스트를 작성해 red 확인 후 수정하라.

### C2. RFC 0001 §10 2단계(해시 검증) 미구현 (Medium)

RFC의 사진 쓰기 절차는 "temp 쓰기 → **hash/size 검증** → rename"인데,
구현은 검증 없이 rename하고 사후에 해시를 기록만 한다. 디스크가 조용히
바이트를 깨뜨린 경우 손상된 해시가 그대로 MediaRef에 박제된다. rename
전에 temp 파일을 재독해 원본 바이트의 sha256과 비교하고, 불일치 시
StorageWriteError로 거부할 것. Spec **A2-4** (v1.1 추가) 테스트로 증명하라.

## Non-blocking Notes

- **N1 (배포 Gate 이월)**: 파티션 락이 `threading.Lock`이므로 단일 프로세스
  안에서만 직렬화된다. 배포 시 uvicorn 워커 1개로 제한하거나 파일 락 도입
  필요 — 배포/e2e Gate 확인 항목으로 이월.
- 락 딕셔너리가 storage_root와 무관하게 period 키만 사용 — 현재는 과잉
  잠금일 뿐 무해. 다중 스토리지 루트를 쓰게 되면 키에 root 포함할 것.
- `main.py` 변경은 테스트 용이성 리팩터링(행위 동일), `pyproject`의
  `gate_spec` marker 등록은 Spec C-2 규칙 이행 — 둘 다 적절.
- Codex가 Fable 미커밋 파일(Spec v1, 7차 심사)을 변경 없이 대신 커밋함 —
  내용 확인 완료, 문제없음.

## 재심사 조건

C1, C2 해소 (A5-4, A2-4 테스트 red→green 포함) + CI 녹색 후
`codex-gate-review-request.md` 갱신.

---

# 7차 심사 — 2026-07-03, commit `82ad28a` (Scaffold 코드베이스 전체 점검)

- Scope: CEO 요청에 의한 코드베이스 전수 점검 (Gate request 아님 — Codex는
  자율 범위로 올바르게 자기 분류했고, 점검 결과 그 판단이 맞았다)

## Verdict: 이상 없음 — Gate 경계 준수 확인

- **Gate 경계** ✓ — 원본 쓰기·인증·백업 코드는 전혀 없다. 구현된 것은
  scaffold(Next.js/FastAPI), `/health`, `/ws/probe`, 하드코딩 더미 데이터의
  read-only Timeline shell, CI 파이프라인뿐 — 전부 자율 범위다.
  IMPLEMENTATION_PLAN §2가 Gate 경계를 정확히 문서화했고 Step 2·3을
  "Fable Spec 대기"로 명시했다.
- **스택 결정** — CEO 직접 결정(TypeScript+Next.js / Python+FastAPI /
  SQLite 인덱스 / `DuriStorage/` = source of truth)이 근거·기각 대안과 함께
  IMPLEMENTATION_PLAN에 기록됨. ADR-001/004/005/007과 정합.
- **검증 실행** ✓ — Fable 환경에서 backend pytest 2건 통과, uvicorn 기동 후
  `/health` 실응답 확인 (Codex 환경의 포트 접근 문제는 코드 결함 아님을 확인).
  원격 CI 녹색은 CEO가 확인.
- **보호 장치** ✓ — `.gitignore`가 `DuriStorage/`·`*.sqlite`·`data/` 등을
  차단해 실제 추억 데이터가 코드 저장소에 커밋될 수 없다. 테스트 이름이
  행위 문장 규칙을 이미 따르고 있다.
- **npm audit (Next 경유 PostCSS moderate)** — `--force` 미적용은 옳은 판단
  (Next 대폭 다운그레이드 유발). 빌드 도구 체인 이슈로 2인 앱 런타임 노출
  아님. Next 패치 릴리스 시 갱신할 것 — 구현 Gate 때 재확인 항목.
- 사소한 메모 (수정 불요, 배포 시점 확인): CORS가 `localhost:3000` 고정 —
  실배포 도메인 반영 필요. `getWebSocketProbeUrl`이 base path를 버리므로
  경로 프리픽스 뒤 배포 시 조정 필요.

## Gate Acceptance Spec 발행

스택 확정에 따라 `fable-gate-acceptance-spec.md` v1을 발행했다.
Storage Writer(A1~A5, 13개 항목)와 Auth/Session(B1~B4, 12개 항목).
Codex는 Step 2부터 이 Spec의 테스트를 먼저 작성해 실패를 확인한 뒤
구현을 시작할 수 있다.

---

# CEO 최종 승인 — 2026-07-03 (Storage Layout RFC 0001)

CEO가 6차 심사(Pass) 결과를 확인하고 **RFC 0001 → Accepted 전환을 승인**했다.

- 저장/Export 포맷 확정: `DuriStorage/` 구조, 월 단위 `metadata.json`
  canonical, 영속 볼륨 요구, Server Access Boundary(§9) 포함.
- Codex는 RFC 0001의 Status를 Accepted로 전환하고, README/CHANGELOG에
  반영할 수 있다.
- 이 승인으로 **구현 착수가 가능**해진다. 단 원본 쓰기 경로·백업/Export·
  인증·기기/세션 코드는 Gate 대상 ⑤ — 구현 결과물은 Fable 심사를 거친다.
- 구현 Gate 이월 확인 항목: N1(orphan media 복구), N2(쓰기 직렬화),
  N3(백업 스펙 + 키 관리), §9 서버 하드닝 실적용 여부.

---

# 6차 심사 (Re-Review) — 2026-07-03, commit `49d910d`

- Scope: RFC 0001 §9 Server Access Boundary 반영 확인 (5차 심사 C1 해소)

## Verdict: 통과 (Pass) — CEO 최종 승인 대기

RFC 0001 §9가 CEO의 Server Access Control 결정을 완전하게 기록했다.

- **접근 통제** ✓ — 관리 계정 CEO 1개, `duri` service user 분리,
  `DuriStorage/` 권한 최소화, 파트너는 앱 사용자, key-based SSH만 허용,
  password login 비활성화, 불필요 계정 금지. CEO 결정 원문과 일치.
- **암호화 스탠스** ✓ — live `DuriStorage/`는 평문(ADR-001/007 근거 명시),
  외부 반출 백업은 암호화 의무. 트레이드오프(물리 도난 시 노출 감수)와
  재검토 트리거 3건(외부 반출 상시화, 클라우드 이전, 위협 모델 변화)이
  결정과 함께 기록됐다 — 결정의 유효 조건이 명시된 좋은 형태다.
- **N3-a 흡수** ✓ — "키 분실이 유일한 백업을 잃는 현실적 경로가 되어서는
  안 된다"는 요구가 RFC 본문에 명시됐고, 키 보관·오프라인 사본·두 사용자
  접근 가능 여부를 백업 스펙의 필수 결정 항목으로 지정했다.

기존 §9(내구성/쓰기 무결성)는 §10으로 재번호. 잔여 조건 없음.

## CEO 승인 후 진행 가능 항목

1. RFC 0001 → **Accepted** (저장/Export 포맷 확정)
2. 이후 구현 착수 가능. 단, 원본 쓰기 경로·백업/Export·인증·기기/세션
   **코드**는 Gate 대상 ⑤이므로 구현 결과물이 다시 Fable 심사를 거친다.
3. 구현 Gate에서 확인할 이월 항목: N1(orphan media 복구), N2(쓰기 직렬화),
   N3(백업 스펙: 주기·복원 테스트·오프사이트·키 관리), 서버 하드닝 실적용
   (§9의 SSH/계정/권한 설정이 실제 배포 서버에 적용됐는지).

---

# 5차 심사 — 2026-07-03, commit `cd2b1fe` (Storage Layout RFC 0001 Final Review)

- Scope: RFC 0001 Accepted 전환 심사 (저장/Export 포맷 확정 — Gate 대상 ④)

## Verdict: 조건부 통과 (Conditional Pass)

RFC 0001은 Accepted 후보로 손색없는 품질이다. 확정 커밋 `22ef298`이 CEO
승인 범위(3개 문서 Draft 해제, ADR-008 Accepted, RFC는 Draft 유지)를
정확히 지킨 것도 확인했다. 단, 확정 전 조건 1건이 남는다.

## Review Focus 답변 (Codex 질문 1~7)

1. **ADR-001 정합** ✓ — 월별 폴더 탐색, `messages.md`, `participants` 이름
   렌더링 모두 사람이 앱 없이 읽을 수 있는 구조다.
2. **ADR-007 정합** ✓ — `DuriStorage/timeline/`이 canonical, DB/인덱스는
   재생성 가능한 캐시, `indexes/`가 canonical 밖으로 분리됐다.
3. **VaultFolder 재유입 없음** ✓ — Alternative B로 명시적으로 기각.
4. **월 단위 파티션 정당화** ✓ — 2인 + Message/Photo 한정, 전체 재작성
   허용, 일 단위 전환 트리거(크기/성능)가 Future Work로 기록됨. 타당하다.
5. **영속성 요구 충분** ✓ — ephemeral 금지, 영구 볼륨 필수, 별도 백업
   의무, fsync 최선 노력, "영구 저장소 없는 배포 대상은 원본 쓰기 부적격"
   규칙까지. 미디어를 먼저 쓰고 metadata를 나중에 쓰는 순서도 보존
   관점에서 올바르다(실패 시 잃는 것이 복구 가능한 쪽).
6. **Auth 경계 유지 + 표시 정체성 포함** ✓ — 4차 심사 C2 해소 상태 유지.
7. **CEO 승인으로 진행 가능한가** — 아래 C1 해소 후 가능.

## Condition (Accepted 전환 전 해소 필수)

### C1. 서버 접근 통제 스탠스를 RFC에 기록할 것

RFC §9는 내구성(durability — 데이터가 사라지지 않음)은 다뤘지만, CEO 승인
시 이 Gate의 확인 항목으로 등록된 **서버 수준 접근 통제**(confidentiality
— 제3자가 폴더를 읽지 못함)는 다루지 않았다. `DuriStorage/`는 평문
파일이므로 앱 인증(ADR-005)이 아무리 견고해도 서버 OS에 접근하는 사람은
모든 대화·사진을 읽을 수 있다.

**요구**: RFC에 "Server Access Boundary" 절을 추가해 CEO 결정을 기록할 것.
결정할 내용: (a) 서버 OS 계정 접근을 누구로 제한하는가, (b) 디스크(또는
`DuriStorage/` 볼륨) 암호화를 적용하는가. "물리적 통제로 충분, 암호화
없음"도 유효한 결정이다 — 중요한 것은 선택이 아니라 **결정이 기록되는 것**.
이 결정은 CEO 입력이 필요하므로 Codex는 CEO에게 선택지를 요청하라.

## C1 입력 수신 — CEO Decision: Server Access Control (2026-07-03)

CEO가 C1에 필요한 결정을 내렸다. Fable 검토 결과 원칙 정합 — 반영 승인.

1. **Server OS access**: 관리 계정은 CEO 본인 1명. Duri 앱은 별도 `duri`
   service user로 실행, `DuriStorage/`는 owner/service user 외 OS 권한으로
   접근 차단. SSH는 key-based만 허용, password login 비활성화, 불필요 계정
   금지. 파트너는 앱 사용자이며 서버 OS 계정 없음.
2. **DuriStorage 암호화**: MVP에서는 미적용 — Human Readable First에 따라
   평문 유지, 집 안 Mini PC의 물리적 통제 + OS 권한으로 보호. **단, 외부로
   나가는 백업본은 암호화한다.** Future Work 트리거(외부 반출/도난 리스크
   증가, 클라우드 이전 시 재검토)도 기록됨.

Fable 평가: 운영 단순성·장기 복구 가능성을 우선한 트레이드오프가 명시적으로
기록됐고 ADR-001/007과 정합한다. 이 결정으로 **N3에 항목 1건 추가**:

- **N3-a. 백업 암호화 키 관리**: 백업본을 암호화하면 키 분실 = 백업 전체
  상실이다. Mini PC가 죽고 백업만 남은 시나리오에서 키가 반드시 살아있어야
  하므로, 백업 스펙 결정 시 키 보관 방식(오프라인 사본, 두 사람 모두 접근
  가능 여부)을 필수로 정할 것.

**다음 단계**: Codex는 이 결정을 RFC 0001에 "Server Access Boundary" 절로
반영(Future Work 트리거 포함)하고 재심사를 요청하라. 반영 확인 후 CEO 최종
승인 → Accepted 전환.

## Non-blocking Notes (구현 시 반드시 다룰 것 — RFC 또는 구현 Gate에서 확인)

- **N1. Orphan media 복구 규칙**: 쓰기 3단계(사진 rename 완료)와 6단계
  (metadata.json 갱신) 사이에서 중단되면 metadata에 없는 사진이 남는다.
  이 orphan은 원본 데이터이므로 **절대 삭제 금지** — 시작 시 스캔해
  재수록(re-ingest)하는 복구 규칙을 구현에 포함할 것.
- **N2. 쓰기 직렬화**: 두 사용자가 동시에 업로드하면 같은 월
  `metadata.json` 전체 재작성이 경합해 lost update가 날 수 있다. 월
  파티션 단위 쓰기는 앱 수준에서 직렬화(락/큐)할 것.
- **N3. 백업 스펙**: "별도 백업 유지"는 선언됐지만 주기·검증(복원 테스트)·
  보관 위치(기기 외 복사본 여부)가 미정이다. 백업 구현 착수 전에 별도
  결정 필요 — 보존이 제품의 존재 이유이므로 백업 무결성 검증은 필수.

---

# CEO 최종 승인 — 2026-07-03

CEO가 4차 심사(Pass) 결과를 확인하고 다음을 승인했다.

- PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 Draft 해제
- ADR-008 → Accepted

승인 전 CEO 확인 사항 (Q&A로 검증됨):

1. 채팅/사진/메타데이터는 `DuriStorage/timeline/` 하나의 폴더가 유일한
   원본(canonical source)이며, DB/인덱스는 재생성 가능한 캐시다 (ADR-007).
2. 접근은 등록된 두 사용자로 제한된다 (ADR-005: slot 1·2, 소모형 초대
   코드, 기기별 세션 폐기).

Codex는 위 확정 작업을 진행할 수 있다. RFC 0001은 Draft 유지 —
구현 착수 전 별도 Gate 필요.

**다음 Gate(구현 전 RFC/구현 심사)에 추가된 Fable 확인 항목**:

- RFC Open Questions 2건 (월/일 파티션, 파일시스템 내구성 보장)
- **서버 수준 보호**: 앱 인증과 별개로, `DuriStorage/` 폴더에 대한 OS 계정
  정책·디스크 암호화 여부 등 배포 서버의 파일시스템 접근 통제를 확인할 것
  (2026-07-03 CEO Q&A에서 도출).

---

# 4차 심사 (Re-Review) — 2026-07-03, commit `a268a64`

- Scope: ADR-008 Proposed / ADR-002 복원+supersede / DATA_MODEL v0.4 Draft /
  RFC 0001 Draft (3차 심사 Condition 해소 확인)

## Verdict: 통과 (Pass) — CEO 최종 승인 대기

3차 심사의 C1, C2가 모두 실제 diff에서 반영 확인되었다.

### C1 해소 확인 ✓ — 결정 원장 복구

- **ADR-008** (Preservation-first MVP: VaultFolder Curation is Future Work,
  Proposed) 신설. 결정·배경·대안 3건·트레이드오프가 충실히 기록됐고, 특히
  "Future Work 재도입 시 VaultFolder가 원본 큐레이션인지 View인지 그때
  재결정한다"고 명시해 3차 심사의 non-blocking note까지 흡수했다.
- **ADR-002**: Decision 3 원문 복원 + "Superseded by ADR-008" 표시,
  Consequences 원문 복원 + 주석. Amended 헤더가 변경 내용을 정확히 기술.
  Decision 4의 경미한 문구 조정은 허용 범위대로 Amended 주석으로 유지.
- ADR 인덱스와 README Dashboard에 ADR-008 노출. DATA_MODEL §0 결정 기록
  범위도 "3은 ADR-008"로 갱신되어 원장이 일관적이다.

### C2 해소 확인 ✓ — 표시 정체성과 Auth 운영 데이터 분리

- DATA_MODEL §10: Auth 운영 데이터(InviteCode, Session, token hash,
  fingerprint, 기기 라벨, 폐기 요약)는 Export 전면 제외 유지. "추억 데이터의
  표시 정체성은 Auth 운영 데이터가 아니다"를 명시하고 `metadata.json`에
  `participants: {actor_id → display_name}` 맵을 포함하기로 했다.
- RFC 0001: canonical 예시에 `participants` 맵 추가, §8이 "Auth Export
  Boundary and Display Identity"로 재정의되어 참조된 발화자의 표시 이름을
  필수 데이터로 요구한다. 모순이 해소됐다.
- 부수 이점: 월별 `metadata.json`이 기록 시점의 표시 이름을 스냅샷하므로,
  이름이 나중에 바뀌어도 당시의 호칭이 보존된다 — 장기 아카이브 관점에서
  올바른 방향이다.

## CEO 승인 후 Codex 진행 가능 항목

1. PRD v0.2.5 / DATA_MODEL v0.4 / WORKFLOW v0.4 Draft 해제
2. ADR-008 → Accepted
3. RFC 0001은 Draft 유지 — 구현 착수 전 별도 Gate (Open Questions 2건:
   월/일 파티션, 파일시스템 내구성 보장 수준)

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
