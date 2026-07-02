# ADR-007: Storage is Export

- Status: Accepted (CEO Decision #007)
- Date: 2026-07-02
- Related: PRD §9 Long-term Design Goals, ADR-001, [DATA_MODEL.md §10](../DATA_MODEL.md#10-storage-layout--export-v1)

## Decision

Duri의 저장 구조 자체를 Export v1로 취급한다.

사용자는 Duri 애플리케이션이 없어도 파일 탐색기와 표준 도구만으로 원본 데이터를
확인할 수 있어야 한다.

원본 보존 형식:

- Markdown
- JSON
- 원본 사진 파일

DB와 검색 인덱스는 검색과 성능을 위한 파생 인덱스일 뿐이며, 원본 저장 구조에서
재생성 가능해야 한다.

## Context

Duri는 두 사람의 삶을 장기간 보존하는 Personal Life System이다. Export를 별도
기능으로만 두면, 미래에 앱이나 DB가 깨졌을 때 실제 데이터 접근이 구현 상태에
종속된다. Human Readable First는 Export가 나중에 실행하는 작업이 아니라, 저장
구조 자체의 성질이어야 한다.

## Alternatives Considered

1. **DB를 canonical source로 두고 Export 기능을 별도 구현** — 쿼리와 구현은
   단순할 수 있지만, 앱이 동작하지 않으면 Export도 실패할 수 있다.
2. **압축 아카이브를 주기적으로 생성** — 백업 파일은 깔끔하지만, 최신 원본과
   아카이브 사이의 동기화/무결성 문제가 생긴다.
3. **사진만 파일로 저장하고 메시지는 DB에만 저장** — 구현은 쉽지만, 대화 기록의
   장기 보존성이 DB 스키마와 앱 코드에 종속된다.

## Reason

- 저장 구조가 곧 Export이면 데이터 생존이 특정 앱 코드나 DB 엔진에 묶이지 않는다.
- Markdown/JSON/원본 사진 파일은 사람이 직접 열어 확인할 수 있다.
- 검색 인덱스와 DB는 언제든 버리고 다시 만들 수 있는 파생물로 단순화된다.

## Consequences

- (+) 앱 없이도 데이터 확인과 백업/이전이 가능하다.
- (+) DB 교체와 검색 인덱스 재생성이 쉬워진다.
- (+) ADR-001 Human Readable First를 저장 계층에서 직접 만족한다.
- (−) 파일/디렉토리 쓰기 무결성, 동시성, 마이그레이션 규칙을 신중히 설계해야 한다.
- (−) 구체적인 파일명 규칙, 월 분할 기준, 단일 `metadata.json` 쓰기 전략은
  구현 전 별도 RFC가 필요하다.

## Non-Decision

이 ADR은 저장 구조가 Export라는 불변식을 정한다. 다음은 아직 확정하지 않는다.

- 정확한 파일명 규칙
- 월별/일별 분할 기준
- `metadata.json` 쓰기 잠금/무결성 전략
- 백업 스케줄과 저장 위치
- DB 엔진 또는 검색 엔진
