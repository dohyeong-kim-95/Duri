# Request for Comments (RFC)

RFC는 Duri의 설계/구조 중 **아직 확정되지 않은 것**을 제안하고 논의하기
위한 문서다. 데이터 모델 변경, 새로운 Log Type 추가, Event Engine 규칙
변경처럼 영향 범위가 넓은 제안은 코드를 작성하기 전에 RFC로 먼저 정리한다.

합의된 RFC는 [docs/adr](../adr/README.md)에 짧은 ADR로 요약되어 남는다.
RFC 자체는 논의 과정의 기록으로 보존한다(합의 후에도 삭제하지 않음).

## 프로세스

1. **Draft**: 제안자가 아래 템플릿으로 RFC 파일을 작성한다.
2. **Discussion**: 논의를 통해 제안을 수정하거나 대안을 검토한다.
3. **Resolution**: `Accepted` / `Rejected` / `Withdrawn` 중 하나로 상태를 확정한다.
   `Accepted`된 내용은 결과를 요약해 ADR로 옮긴다.

## 파일 규칙

- 파일명: `NNNN-short-title.md` (예: `0001-log-type-voice.md`)
- 번호는 순차 증가하며 재사용하지 않는다.

## 템플릿

```markdown
# NNNN. <제안 제목>

- Status: Draft | Accepted | Rejected | Withdrawn
- Date: YYYY-MM-DD

## Summary

한두 문장으로 요약.

## Motivation

왜 필요한가. PRD의 어떤 원칙/목표와 연결되는가.

## Proposal

구체적인 제안 내용.

## Alternatives Considered

검토했지만 채택하지 않은 대안과 그 이유.

## Open Questions

아직 결정되지 않은 부분.
```

## Index

| No. | Title | Status | Date |
|-----|-------|--------|------|
| [0001](./0001-storage-layout.md) | Storage Layout | Draft | 2026-07-02 |
