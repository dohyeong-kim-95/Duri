# Duri PRD v0.2.5

> «Live together. Log automatically. Remember forever.»

> 변경 이력은 [CHANGELOG.md](../CHANGELOG.md)에서 관리한다.

---

## 1. Mission

Duri는 우리 둘이 함께 살아가는 모든 순간을 자동으로 기록하고, 구조화하며, 평생 간직할 수 있도록 돕는 **Personal Life System**이다.

우리는 메신저를 만드는 것이 아니다.

우리는 우리의 삶을 가장 자연스럽게 기록하고, 잃지 않도록 보존하는 시스템을 만든다.

---

## 2. Vision

사람은 추억을 잃어버리는 것이 아니다.

정리하지 못하거나 다시 찾지 못해서 잃어버린다고 느낀다.

Duri는

- 대화
- 사진
- 일정
- 장소
- 메모
- 선물
- 데이트

등 일상에서 발생하는 모든 기록을 시간순으로 보존하고, 미래에 다양한 방식으로 다시 활용할 수 있도록 충분한 메타데이터를 함께 저장한다.

사용자는 기록을 관리하지 않는다.

사용자는 살아간다.

기록과 보존은 Duri가 담당한다.

---

## 3. First Principle

> «사용자는 기록하지 않는다. 사용자는 살아간다. Duri는 삶을 기록한다.»

그리고

> «Duri는 데이터를 똑똑하게 저장하지 않는다. 데이터를 오래 보존하고, 필요할 때 똑똑하게 읽는다.»

원본 데이터는 가능한 한 단순하고 안정적으로 저장하며, AI는 원본을 변경하지 않고 다양한 관점의 View를 생성하는 역할만 수행한다.

---

## 4. Product Philosophy

### 4.1 Chat is the Input

채팅은 목적이 아니다.

채팅은 가장 자연스러운 입력 인터페이스다.

두 사람이 가장 자주 사용하는 행동이므로 기록은 이곳에서 시작된다.

### 4.2 Everything is a Log

모든 정보는 Log이다.

예)

- Message
- Photo
- Schedule
- Place
- Gift
- Note
- Voice

새로운 기능은 새로운 Log Type을 추가하는 방식으로 확장한다.

### 4.3 Timeline First

MVP에서 Duri는 Event를 생성하지 않는다.

모든 Log는 시간순 Timeline으로 저장되며, 미래의 Event Engine과 AI가 충분히 활용할 수 있도록 Metadata를 함께 축적한다.

MVP Metadata는 원본 데이터에서 기계적으로 **추출** 가능한 값만 저장하며,
사람 이름, 장소명, 여행/데이트 분류, AI 요약, AI 태깅처럼 의미를 **해석**하는
작업은 Future Work다.

Event 생성은 Future Work이다. ([ADR-002](adr/ADR-002-timeline-first.md), [EVENT_ENGINE.md](EVENT_ENGINE.md) 참고)

### 4.4 Search Now, Vault Later

MVP에서 VaultFolder Curation은 제외한다.

MVP의 탐색 경험은 Timeline, Deterministic Metadata, Search로 제공한다.

Metadata 기반 탐색 조건과 검색 결과는 원본이 아니라 재생성 가능한 View/Index다.

VaultFolder는 사용자가 직접 추억 폴더를 만들거나 AI가 큐레이션 제안을 돕는
Future Work다. 도입되더라도 원본 Log와 Timeline을 수정하지 않고, `log_id`
참조 또는 재생성 가능한 View로 다룬다.

### 4.5 AI as Reader

AI는 원본 데이터를 생성하거나 수정하지 않는다.

AI의 역할은

- 검색
- 회상
- 요약
- 분류
- 다양한 View 생성

이다.

AI가 생성하는 모든 결과는 원본 데이터로부터 언제든 다시 생성 가능해야 한다. ([ADR-003](adr/ADR-003-ai-generates-views-not-data.md) 참고)

---

## 5. Core User Experience

사용자는

- 채팅한다.
- 사진을 보낸다.
- *(Future Work)* 일정을 공유한다.
- 평소처럼 살아간다.

↓

Duri는

- Log 저장
- Timeline 생성
- Metadata 생성
- 자동 백업

을 수행한다.

↓

나중에 사용자는

기간, 메시지에 직접 등장한 단어, 사진 Metadata 같은 기준으로 추억을 다시
탐색할 수 있다.

VaultFolder, 장소 Alias, AI 요약/추천/분류는 Future Work다.

---

## 6. MVP Goal

MVP의 목적은 메신저를 만드는 것이 아니다.

다음 경험을 검증하는 것이다.

> «"채팅만 했는데 추억을 잃지 않는다."»

MVP는 **반응형 Web Application**으로 제공한다.

PWA는 선택 가능한 배포 방식이며 MVP의 성공 조건이 아니다.

**MVP 기능**

- 1:1 채팅
- 사진 전송
- 원본 사진 저장
- Timeline 저장
- Deterministic Metadata 자동 생성
- 검색
- Storage-as-Export / 자동 백업
- Authentication (Invite Code)
- Device Registration

**Future Work**

- Event Engine
- VaultFolder Curation
- AI 자동 분류
- 여행/데이트 자동 생성
- AI Memory
- 다양한 View 자동 생성
- 추가 Log Type (Schedule, Place, Gift, Note, Voice 등)

---

## 7. Delivery Strategy

*(CEO Decision #004, [ADR-004](adr/ADR-004-responsive-web-first.md))*

MVP는

**https://duri.bubblelab.dev**

를 통해 제공한다.

Responsive Web을 기본 플랫폼으로 하며,

PWA는 선택 가능한 설치 방식(Delivery Method)으로 취급한다.

- 앱처럼 사용할 수 있도록 UI를 설계한다.
- PWA 설치를 성공 조건으로 삼지 않는다.
- 사용자가 URL 하나만 기억하면 사용할 수 있는 경험을 우선한다.

---

## 8. Security Requirements

*(CEO Decision #005, [ADR-005](adr/ADR-005-invite-code-two-person-auth.md))*

MVP는 공개 URL에서 제공되므로 **Authentication은 MVP 필수 요구사항이다.**

인증 방식은 **Self-hosted JWT + Invite Code**를 사용하며, 외부 Authentication Provider(Supabase Auth, Firebase Auth 등)는 사용하지 않는다.

- 등록 가능한 사용자는 정확히 2명으로 제한한다.
- Invite Code는 소모형(One-time)이다.
- 최초 로그인 이후 기기를 기억하여 반복 로그인을 최소화한다.
- 서버는 등록된 기기를 관리할 수 있어야 한다.
- 기기 분실 시 특정 기기의 인증을 무효화할 수 있어야 한다.
- 모든 데이터 접근은 인증 이후에만 가능하다.

---

## 9. Long-term Design Goals

- 원본 데이터는 사람이 직접 읽을 수 있어야 한다.
- 언제든 Export 가능해야 한다.
- AI 모델이 바뀌어도 데이터는 그대로 활용 가능해야 한다.
- 특정 서비스에 종속되지 않아야 한다.
- 사진 원본은 절대 손실되지 않아야 한다.
- AI가 생성한 결과는 언제든 원본으로부터 다시 생성 가능해야 한다.

---

## 10. Ownership

모든 데이터는 우리 둘의 것이다.

기본 저장 위치는 개인 서버(Mini PC)를 원칙으로 하며,

공개 접근 시에도 인증을 통해 두 사용자만 접근 가능해야 한다.

원본 데이터는 장기 보존을 최우선으로 하며, 자동 백업을 지원한다.

---

## 11. Non Goals

Duri는 다음을 목표로 하지 않는다.

- 카카오톡보다 많은 기능
- 범용 메신저
- SNS
- 공개 커뮤니티
- 수익화
- 서비스 확장

또한 MVP에서 AI 기반 자동 분류나 Event 생성 정확도를 목표로 하지 않는다.

MVP에서

- Native App
- PWA 설치 경험

은 성공 조건이 아니다.

---

## 12. Success Criteria

이 프로젝트의 성공은 사용자 수가 아니다.

다음 질문에 "예"라고 답할 수 있으면 성공이다.

- 자연스럽게 Duri에서 대화하게 되는가?
- 사진을 보내면 따로 정리하지 않아도 되는가?
- 원하는 추억을 몇 초 안에 다시 찾을 수 있는가?
- 원본 데이터를 잃지 않고 장기 보존할 수 있는가?
- 미래의 AI가 현재 저장된 데이터를 그대로 활용할 수 있는가?

---

## 13. Guiding Sentence

> «우리는 추억을 자동으로 분류하는 시스템을 만드는 것이 아니다. 우리는 추억을 잃지 않도록 기록하고, 미래의 어떤 기술로도 다시 이해할 수 있는 형태로 보존하는 시스템을 만든다.»
