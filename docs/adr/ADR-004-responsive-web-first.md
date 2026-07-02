# ADR-004: Responsive Web First

- Status: Accepted (CEO Decision #004)
- Date: 2026-07-02
- Related: PRD §7 Delivery Strategy, §11 Non Goals

## Decision

MVP는 **반응형 Web Application**으로 제공한다.

- 배포 주소는 **https://duri.bubblelab.dev** 를 기준으로 한다.
- PWA는 MVP의 필수 기능이 아니라 **선택 가능한 전달 방식(Delivery Method)** 으로 취급한다.
- 앱처럼 사용할 수 있도록 UI를 설계하되, PWA 설치를 성공 조건으로 삼지 않는다.

## Context

사용자는 정확히 2명이며, 그중 한 명(여자친구)은 설치·설정 과정 없이 바로 사용할 수 있어야 한다. "URL 하나만 기억하면 사용할 수 있는 경험"이 도입 장벽을 없애는 가장 확실한 방법이다.

## Alternatives Considered

1. **Native App (iOS/Android)** — 최고의 UX와 푸시 알림을 제공하지만, 스토어 심사·서명·배포 파이프라인이 2인 프로젝트에 과도하며 업데이트 마찰이 크다.
2. **PWA를 MVP 필수 조건으로 포함** — 설치형 경험을 제공하지만, iOS의 PWA 제약과 설치 유도 과정 자체가 실패 지점이 된다.
3. **데스크톱 우선 웹** — 구현은 단순하지만 주 사용 맥락(모바일에서의 채팅·사진 전송)과 맞지 않는다.

## Reason

- 배포와 업데이트가 서버 배포 한 번으로 끝난다.
- 설치 마찰이 0이다 — 브라우저와 URL만 있으면 된다.
- PWA는 웹 앱 위에 언제든 얹을 수 있으므로, 지금 배제해도 잃는 것이 없다.

## Consequences

- (+) 가장 빠른 출시 경로이며 유지보수가 단순하다.
- (+) 모든 기기(모바일/데스크톱)를 하나의 코드베이스로 커버한다.
- (−) 네이티브 푸시 알림, 백그라운드 동작 등은 제한된다(필요 시 PWA/알림은 Future Work).
- 모바일 브라우저에서 앱처럼 느껴지는 반응형 UI 설계가 필수 요구사항이 된다.
- 공개 URL로 제공되므로 인증이 필수가 된다 → ADR-005로 이어진다.
