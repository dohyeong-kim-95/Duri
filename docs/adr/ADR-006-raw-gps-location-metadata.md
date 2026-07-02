# ADR-006: Raw GPS Location Metadata

- Status: Accepted (CEO Decision #006)
- Date: 2026-07-02
- Related: PRD §3 First Principle, PRD §4.5 AI as Reader, [DATA_MODEL.md §4.2](../DATA_MODEL.md#42-photo-payload), [DATA_MODEL.md §8.1](../DATA_MODEL.md#81-future-work-location-alias)

## Decision

MVP에서는 사진 EXIF에 포함된 GPS 좌표만 원본 Location Metadata로 저장한다.

저장하는 값:

- `latitude`
- `longitude`

MVP에서 하지 않는 것:

- GPS -> 장소명 변환
- GPS -> 행정구역 변환
- AI 장소 추론
- 자동 여행/데이트 분류

Location Alias는 Future Work로 둔다. 사용자가 나중에 직접 "서울숲",
"청주 집 근처", "부산 여행", "우리 단골 카페" 같은 권역 Alias를 정의할 수
있지만, Alias는 원본 Metadata가 아니라 파생 `View` 계층으로 관리한다.

## Context

Duri는 "멍청하게 저장하고, 필요할 때 똑똑하게 읽는다"는 원칙을 따른다.
위치 정보는 시간이 지나도 의미가 바뀔 수 있다. 같은 GPS 좌표라도 어떤 날은
"데이트 장소"이고, 다른 날은 "집 근처"일 수 있다.

원본 Metadata에 장소명이나 의미를 바로 저장하면, 당시의 해석이 장기 보존
데이터에 섞인다. 이는 AI as Reader 원칙과 충돌한다.

## Alternatives Considered

1. **GPS를 저장하면서 즉시 장소명으로 변환** — 검색 편의는 좋아지지만,
   reverse geocoding 결과와 외부 서비스 품질에 원본 데이터가 종속된다.
2. **AI로 장소/여행/데이트를 자동 추론** — 회상 경험은 좋아질 수 있지만,
   MVP 범위를 넓히고 AI 해석이 원본 Metadata에 섞일 위험이 있다.
3. **위치 정보를 전혀 저장하지 않음** — 가장 단순하지만, 미래의 Event
   Engine과 Location Alias가 활용할 핵심 신호를 잃는다.

## Reason

- GPS 좌표는 원본 사진에서 기계적으로 추출 가능한 사실이다.
- 장소명과 권역명은 해석이며, 나중에 더 좋은 규칙이나 AI로 다시 만들 수 있다.
- 원본은 오래 보존하고, 의미는 나중에 View로 부여하는 편이 Duri의 장기 설계와
  일관된다.

## Consequences

- (+) 위치 원본 데이터가 단순하고 안정적으로 유지된다.
- (+) 외부 지도/지오코딩 서비스에 원본 저장 구조가 종속되지 않는다.
- (+) Location Alias와 장소 기반 회상은 나중에 재생성 가능한 View로 확장할 수 있다.
- (−) MVP에서는 "서울숲", "부산 여행" 같은 장소명 검색이 자동으로 되지 않는다.
- (−) 사용자가 의미 기반 위치 탐색을 원하면 Future Work의 Alias/View 기능이 필요하다.
