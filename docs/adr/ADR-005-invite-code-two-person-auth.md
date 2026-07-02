# ADR-005: Invite-code based two-person authentication

- Status: Accepted (CEO Decision #005)
- Date: 2026-07-02
- Related: PRD §8 Security Requirements, §10 Ownership, ADR-004

## Decision

MVP는 공개 URL에서 제공되므로 **인증(Authentication)을 MVP 필수 요구사항으로 포함**한다.

인증 방식은 **Self-hosted JWT + Invite Code**를 사용하며, 외부 Authentication Provider(Supabase Auth, Firebase Auth 등)는 사용하지 않는다.

### Authentication Requirements

- 등록 가능한 사용자는 정확히 **2명**이다.
- 초대 코드는 **소모형(One-time)** 이어야 한다.
- 최초 인증 후 **기기를 기억**하여 반복 로그인을 최소화한다.
- 서버는 **등록된 기기를 관리**할 수 있어야 한다.
- 기기 분실 시 **특정 기기의 인증을 무효화**할 수 있어야 한다.
- **모든 데이터 접근은 인증 이후에만** 가능하다.

## Context

ADR-004에 따라 MVP는 https://duri.bubblelab.dev 라는 공개 URL로 제공된다. 이 시스템에는 두 사람의 사적인 대화와 사진이 저장되므로, 인증 없는 공개 접근은 허용될 수 없다. 동시에 Duri는 Ownership과 Vendor Lock-in 최소화를 핵심 철학으로 한다.

## Alternatives Considered

1. **외부 Auth Provider (Supabase Auth, Firebase Auth 등)** — 구현이 빠르고 검증된 보안을 제공하지만, 인증이라는 시스템의 관문을 외부 서비스에 종속시켜 Ownership·Long-term Design 원칙에 어긋난다.
2. **소셜 로그인(OAuth: Google 등)** — 사용자 편의는 높지만 마찬가지로 외부 종속이며, 2인 시스템에 과도하다.
3. **Basic Auth / IP 허용 목록** — 가장 단순하지만 기기 단위 관리·무효화가 불가능하고, 모바일 환경(유동 IP)에서 실용적이지 않다.
4. **인증 없음(비공개 URL에만 의존)** — Security by obscurity로, 사적 데이터 보호 수단이 될 수 없다.

## Reason

이 결정은 구현 단순성 때문이 아니라 Duri의 핵심 철학인

- **Ownership** — 인증 데이터와 세션까지 우리 서버가 소유한다.
- **Long-term Design** — 외부 서비스의 정책·가격·종료에 영향받지 않는다.
- **Vendor Lock-in 최소화** — 인증 계층을 통째로 이전·교체할 수 있다.

를 지키기 위한 결정이다. 사용자가 2명으로 고정되어 있어 자체 구현의 범위가 작고 통제 가능하다.

## Consequences

- (+) 인증 스택 전체가 자체 서버 안에 있어 데이터 주권이 완성된다.
- (+) 기기 등록/무효화 모델이 요구사항에 정확히 맞게 설계된다.
- (−) 토큰 발급·갱신·폐기, 초대 코드 수명 주기, 기기 관리 등 보안 구현 책임을 직접 진다.
- (−) 비밀번호 재설정, 세션 만료 등 엣지 케이스를 직접 처리해야 한다.
- DATA_MODEL.md에 User, Device, InviteCode, Session(또는 Token) 엔터티가 포함되어야 한다.
