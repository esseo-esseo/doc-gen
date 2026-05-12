---
description: 대화 맥락이나 인자로 받은 주제로 HTML 슬라이드 프레젠테이션을 빠르게 생성한다 (input 폴더 분석·Confluence 변환은 안 함, 가볍게)
argument-hint: [주제] (생략 가능 — 생략 시 사용자에게 묻는다)
---

대화에서 받은 주제를 바탕으로 자체완결 HTML 프레젠테이션을 생성한다. `doc-gen` 스킬보다 가볍고, input 폴더 자료 수집·아카이빙·Confluence 변환을 하지 않는다.

---

## 0. 인자 / 의도 파악

`$ARGUMENTS`에 주제가 들어왔으면 그것을 출발점으로 삼는다. 비어있으면 사용자에게 한 번만 다음을 묻는다 (AskUserQuestion):

1. 주제 / 핵심 메시지
2. 발표 길이 (slide_count) — 기본 10
3. 톤 (보고 / 제안 / 튜토리얼 / 회고)

이미 충분한 맥락이 대화에 있으면 묻지 말고 바로 진행.

**작성자(author) 확보** — 인자(`author:`)나 대화 맥락에 작성자가 명시되어 있지 않으면 **이 단계에서 함께 묻는다** ("표지에 들어갈 작성자명을 알려주세요"). 임의의 기본값을 채우지 않는다.

선택 정보 (자유롭게 인자 안에 적혀있으면 추출):
- `title:` — 표지 제목 (없으면 주제로부터 자동 생성)
- `subtitle:` — 부제
- `author:` — 발표자 (인자·맥락에 없으면 0단계에서 사용자에게 묻는다)
- `slide_count:` — 정수 (기본 10)
- `template:` — `report | proposal | metric | tutorial | review`
- `output:` — 출력 디렉토리명 (기본: `output/YYYY-MM-DD_제목`)

## 1. 출력 경로 결정

오늘 날짜와 title을 조합:
- 형식: `output/YYYY-MM-DD_제목`
- title의 파일명 불가 문자(`/ \ : * ? " < > |`) 제거, 공백은 `_`로 대체
- 예: `output/2026-05-08_5월_KPI_리뷰`

이후 단계에서 `{OUT}` 은 이 경로를 가리킨다.

## 2. 콘텐츠 분석 (대화 맥락만 사용)

주제·맥락에서 다음을 도출:

1. **핵심 메시지** — 발표가 전달할 단 한 가지
2. **주요 포인트** — 청중이 기억해야 할 3~7가지
3. **데이터/숫자** — 있으면 `metric` 슬라이드로 빅 넘버 강조
4. **비교/대조** — 있으면 `two_column rows`
5. **프로세스/단계** — 있으면 `flow` (3-5단계)
6. **인용·핵심 슬로건** — 있으면 `callout` 또는 `quote`

input 폴더는 읽지 않는다. 대화 맥락 + 사용자 인자만 사용.

## 3. 슬라이드 구조 설계

`template`별 권장 흐름:

| template | 권장 흐름 |
|---|---|
| `report` | title → agenda → section → bullets → metric → two_column → callout → closing |
| `proposal` | title → section(문제) → bullets(현황) → flow(개선안) → two_column(AS-IS/TO-BE) → metric(기대효과) → callout → closing |
| `metric` | title → metric(hero) → metric(grid 4-up) → bullets(인사이트) → callout → closing |
| `tutorial` | title → agenda → section × N → flow(단계) → bullets → callout → closing |
| `review` | title → agenda → metric(성과 KPI) → two_column(잘된점/개선점) → table → callout → closing |

### v2 신규 타입 (적극 활용)

- **agenda** — 5장 이상 PT면 두 번째 슬라이드로 자동 삽입. 슬라이드 길잡이
- **metric** — KPI·달성율·증감 표현. 1개면 hero 모드, 2-4개면 그리드. 본문에 숫자가 묻히지 않게 메인으로 강조

### 작성 원칙

- 슬라이드당 핵심 1가지
- 불릿 항목당 15단어 이내
- 한글 measure는 35-45자/줄 (시스템이 자동 처리)
- 총 슬라이드: `slide_count` 준수, 미지정 시 8-12장
- bullets/flow/agenda 각각 5-8개 이하 — 초과 시 stderr 경고가 나오므로 분할

## 4. slides.json 작성

`{OUT}/slides.json` 에 저장한다. 디렉토리가 없으면 만든다.

```json
{
  "meta": {
    "title": "발표 제목",
    "author": "<사용자에게 받은 작성자명>",
    "date": "YYYY-MM-DD"
  },
  "slides": []
}
```

### 슬라이드 타입 스키마 (v2 — 12종)

```json
// 표지
{ "type": "title", "title": "제목", "subtitle": "부제", "label": "REPORT", "author": "<사용자에게 받은 작성자명>", "date": "2026-05-08" }

// 섹션 헤더 (좌측 오렌지 vertical bar + section 번호)
{ "type": "section", "title": "섹션명", "subtitle": "설명" }

// 목차 (v2 신규)
{ "type": "agenda", "title": "오늘의 흐름",
  "items": [
    { "heading": "현황", "sub": "Q2 핵심 지표" },
    { "heading": "이슈 분석", "sub": "구조적 문제 3가지" },
    { "heading": "제안", "sub": "3가지 개선 원칙" }
  ]}

// 빅 넘버 (v2 신규) — 단일 hero
{ "type": "metric",
  "items": [{ "value": "112%", "label": "Q2 매출 달성율", "delta": "+12%p", "caption": "목표 대비 달성" }]}

// 빅 넘버 그리드 (2-4개)
{ "type": "metric", "title": "Q2 핵심 지표",
  "items": [
    { "value": "1.35억", "label": "매출",     "delta": "+23%",   "caption": "목표 1.2억 대비 112%" },
    { "value": "847명",  "label": "신규 고객", "delta": "+158명", "caption": "재계약율 91%" },
    { "value": "1,720만","label": "운영비",   "delta": "-18%",   "caption": "자동화로 월 40h 절약" },
    { "value": "91%",    "label": "CS 만족도","delta": "-4%p",   "caption": "목표 95% 미달" }
  ]}
// delta 첫 글자 +/▲ → 녹색, -/▼ → 빨강, 그 외 → 중립

// 불릿 (간단)
{ "type": "bullets", "title": "제목", "items": ["항목1", "항목2"] }

// 불릿 (중첩 — heading + sub)
{ "type": "bullets", "title": "제목", "label": "PROBLEM",
  "items": [{ "heading": "소제목", "sub": ["하위1", "하위2"] }] }

// 흐름 (3-5단계 카드)
{ "type": "flow", "title": "제목",
  "items": [
    { "heading": "STEP 1", "icon": "🔑", "text": "설명", "color": "blue" },
    { "heading": "STEP 2", "icon": "⚙️", "text": "설명", "color": "green" },
    { "heading": "STEP 3", "icon": "✅", "text": "설명", "color": "purple" }
  ]}
// color: blue|green|yellow|purple|red|cyan — v2에서 실제 다른 hex로 렌더링됨

// 2열 비교 (rows — 라벨/값)
{ "type": "two_column", "title": "AS-IS vs TO-BE",
  "left":  { "heading": "AS-IS", "icon": "📄", "color": "blue",
             "rows": [["접수", "분산"], ["이력", "소실"]], "note": "현재 상태" },
  "right": { "heading": "TO-BE", "icon": "🚀", "color": "purple",
             "rows": [["접수", "단일 채널"], ["이력", "자동 기록"]], "note": "개선 후" } }
// color: blue|purple|green|yellow

// 2열 비교 (items — 단순 불릿)
{ "type": "two_column", "title": "제목",
  "left":  { "heading": "잘된 점", "color": "green", "items": ["..."] },
  "right": { "heading": "개선점", "color": "yellow", "items": ["..."] } }

// 데이터 테이블 (숫자 컬럼 자동 우측 정렬 + tabular-nums)
{ "type": "table", "title": "팀별 KPI",
  "headers": ["팀", "목표", "실적", "달성율"],
  "rows": [["영업", "1.2억", "1.35억", "112%"], ["마케팅", "700명", "847명", "121%"]] }

// 핵심 메시지 (callout — 좌우 horizontal rule + 강조)
{ "type": "callout", "title": "사업부는 슬랙에 입력만 — 접수·배정·이력이 모두 자동", "label": "핵심 효과" }

// 인용
{ "type": "quote", "text": "자동화 도입이 이번 분기 가장 큰 성과였다.", "attribution": "팀장 김OO" }

// 이미지 (input 폴더에 파일이 있을 때만)
{ "type": "image", "title": "제목", "image": "input/파일명.png", "caption": "캡션" }

// 마지막
{ "type": "closing", "title": "감사합니다", "subtitle": "문의: name@company.com" }
```

### 모든 슬라이드 공통 선택 필드

```json
"banner":  { "text": "안내 메시지", "level": "info" },   // level: info | warning | error | success
"label":   "DRAFT",                                       // 우상단 작은 라벨
"summary": "이 슬라이드 핵심 한 줄 요약"                  // 하단 요약 바
```

## 5. 렌더링

```bash
python3 scripts/render_html.py {OUT}/slides.json
```

stderr에 `⚠ 슬라이드 #N (타입): 항목 X개 — 권장 최대 Y개` 경고가 나오면 해당 슬라이드를 분할(예: bullets 7개 → bullets 4개 + bullets 3개)하고 재실행한다.

## 6. 완료 보고

```
✓ HTML PPT: {OUT}/index.html
✓ 슬라이드 구조: {OUT}/slides.json

총 N장 구성:
  - title (1)
  - agenda (1)
  - metric (2)
  - bullets (3)
  - ...

조작:
  ← / → / Space     슬라이드 이동
  Home / End        처음 / 끝
  ESC / O           overview 모드
  B / W             블랙아웃 / 화이트아웃
  PDF 저장 버튼      1슬라이드 = 1페이지 PDF

테마: 우상단 sun/moon 버튼 (라이트 / 다크)
공유: URL 끝에 #/3 형태로 특정 슬라이드 직접 링크 가능

열기: open "{OUT}/index.html"
```

## 다른 스킬과의 차이

- 이 스킬(`/ppt`)은 **대화 맥락만**으로 가볍게 PPT 생성
- input 폴더 자료가 있어 분석부터 해야 한다면 `/doc-gen` 사용
- 기존 PT 검토만 필요하면 `/review`
