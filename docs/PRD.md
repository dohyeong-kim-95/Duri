# Duri PRD v0.2.3

> «Live together. Log automatically. Remember forever.»

> 변경 이력은 [CHANGELOG.md](../CHANGELOG.md)에서 관리한다.

---

## 1. Mission

Duri는 우리 둘이 함께 살아가는 모든 순간을 자동으로 기록하고, 구조화하며, 평생 간직할 수 있도록 돕는 **Personal Life System**이다.

우리는 메신저를 만드는 것이 아니다.

우리는 우리의 삶을 가장 자연스럽게 기록하는 시스템을 만든다.

---

## 2. Vision

사람은 추억을 잃어버리는 것이 아니다.

정리하지 못해서 다시 찾지 못한다.

Duri는

- 대화
- 사진
- 일정
- 장소
- 메모
- 선물
- 데이트

등 일상에서 발생하는 모든 기록을 자동으로 연결하고 구조화한다.

사용자는 기록을 관리하지 않는다.

사용자는 살아간다.

기록과 정리는 Duri가 담당한다.

---

## 3. First Principle

> «사용자는 기록하지 않는다. 사용자는 살아간다. Duri는 삶을 기록한다.»

이 원칙은 모든 기능 설계의 기준이 된다.

새로운 기능은 반드시 아래 질문을 통과해야 한다.

> «이 기능이 우리의 삶을 더 자연스럽게 기록하고, 더 쉽게 다시 꺼내볼 수 있게 만드는가?»

---

## 4. Product Philosophy

### 4.1 Chat is the Input

채팅은 목적이 아니다.

채팅은 가장 자연스러운 입력 인터페이스다.

두 사람이 가장 자주 사용하는 행동이므로, 기록은 이곳에서 시작된다.

### 4.2 Everything is a Log

Duri에서 모든 정보는 Log이다.

예를 들어

- Message
- Photo
- Schedule
- Place
- Gift
- Note
- Voice
- AI Conversation

모두 동일한 Log 개념으로 저장된다.

새로운 기능은 새로운 Log Type일 뿐이다.

### 4.3 Logs become Events

Log는 시간, 장소, 맥락 등을 기반으로 자동 연결되어 Event를 형성한다.

예)

- 사진 여러 장
- 채팅
- 위치 정보
- 일정

↓

**"2026-07-12 서울숲 데이트"**

사용자는 Event를 만들지 않는다.

Duri가 생성한다.

> Event 자동 생성(Event Engine)은 장기 방향이며, MVP 범위에는 포함하지 않는다.
> ([ADR-002](adr/ADR-002-timeline-first.md) 참고)

### 4.4 Events become Timeline

Event는 시간 순으로 연결되어 하나의 Timeline을 만든다.

Timeline은 두 사람이 함께 살아온 이야기이다.

### 4.5 Timeline becomes Vault

Timeline은 시간이 지나면서 의미 단위로 구조화된다.

예)

- 여행
- 데이트
- 기념일
- 맛집
- 영화
- 선물

Vault는 폴더가 아니라, 하나의 Event를 여러 관점에서 다시 볼 수 있는 구조화된 지식 공간이다.

### 4.6 AI grows with Memory

AI는 단순히 검색하지 않는다.

축적된 Vault를 이해하고

- 회상
- 추천
- 연결
- 요약

을 수행한다.

AI의 품질은 시간이 지날수록 향상된다.

---

## 5. Core User Experience

사용자는

- 채팅한다.
- 사진을 보낸다.
- 데이트를 한다.
- 일정을 공유한다.

평소처럼 살아간다.

↓

Duri는

- Log 생성
- Event 생성
- Timeline 생성
- Vault 갱신

을 자동 수행한다.

↓

몇 년 후에도

**"우리 처음 제주도 갔던 날"**

이라고 검색하면

관련된 모든 기록을 하나의 추억으로 다시 보여준다.

---

## 6. MVP Goal

MVP의 목적은 메신저를 만드는 것이 아니다.

다음 경험을 검증하는 것이다.

> «"채팅만 했는데 추억이 자동으로 정리된다."»

MVP는 **반응형 Web Application**으로 제공한다.

PWA는 선택 가능한 배포 방식이며 MVP의 성공 조건이 아니다.

**MVP 기능**

- 1:1 채팅
- 사진 전송
- 원본 사진 저장
- 자동 백업
- Timeline 저장
- Metadata 자동 생성
- 검색
- Authentication (Invite Code)
- Device Registration

---

## 7. Delivery Strategy

*(CEO Decision #004)*

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

*(CEO Decision #005)*

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

Duri는 수십 년 동안 사용할 시스템을 목표로 한다.

이를 위해

- 데이터는 사람이 이해할 수 있는 형태로 저장한다.
- 언제든 Export 가능해야 한다.
- AI가 변경되어도 데이터는 그대로 활용 가능해야 한다.
- 특정 서비스나 기술에 종속되지 않는다.
- 사진 원본은 절대 손실되지 않는다.

---

## 10. Human Readable First

앱보다 데이터가 오래 살아야 한다.

최악의 경우 Duri가 동작하지 않아도,

사용자는 폴더를 열어

- 사진
- 메시지
- 메타데이터
- 요약

를 직접 확인할 수 있어야 한다.

데이터는 Duri만을 위한 것이 아니라, 우리의 삶을 위한 자산이다.

---

## 11. Ownership

모든 데이터는 우리 둘의 것이다.

기본 저장 위치는 개인 서버(Mini PC)를 원칙으로 하며,

공개 접근 시에도 인증을 통해 두 사용자만 접근 가능해야 한다.

자동 백업을 통해 장기 보존을 지원하며, 언제든 다른 저장소나 새로운 시스템으로 이전할 수 있어야 한다.

---

## 12. Non Goals

Duri는 다음을 목표로 하지 않는다.

- 카카오톡보다 많은 기능
- 범용 메신저
- SNS
- 공개 커뮤니티
- 수익화
- 서비스 확장

MVP에서

- Native App
- PWA 설치 경험

은 성공 조건이 아니다.

Duri는 오직 우리 둘만을 위한 프로젝트다.

---

## 13. Success Criteria

이 프로젝트의 성공은 사용자 수가 아니다.

다음 질문에 "예"라고 답할 수 있으면 성공이다.

- 자연스럽게 Duri에서 대화하게 되는가?
- 사진을 보내면 따로 정리하지 않아도 되는가?
- 원하는 추억을 몇 초 안에 다시 찾을 수 있는가?
- 시간이 지날수록 기록의 가치가 커지는가?
- 10년 뒤에도 이 데이터를 그대로 활용할 수 있는가?

---

## 14. Guiding Sentence

> «우리는 추억을 저장하는 것이 아니라, 함께 살아가는 시간을 이해하고 기억하는 시스템을 만든다.»
