입력 데이터를 분석하고 HTML 슬라이드 프레젠테이션(PDF 저장 포함)을 생성한다. 아래 워크플로우를 따른다.

---

## 워크플로우

### 0. 입력 확인

`input/request.yaml` 파일을 읽는다.

파일이 없으면 아래 형식을 안내하고 중단한다:

```yaml
type: presentation          # 고정값
title: "문서 제목"
subtitle: "부제목"          # optional
template: report            # report | proposal | briefing | tutorial | review
slide_count: 12             # optional — 미지정 시 내용 기반 자동 결정
confluence: false           # true면 confluence-ready.md 추가 생성
instructions: |             # optional — 강조할 내용, 구조 지침 등
  특별한 요구사항을 자유롭게 작성
```

### A. 출력 경로 결정

오늘 날짜와 title을 조합하여 출력 디렉토리를 결정한다.

규칙:
- 형식: `output/YYYY-MM-DD_제목`
- title에서 파일명 사용 불가 문자(`/ \ : * ? " < > |`)는 제거
- 공백은 `_`로 대체
- 예: `output/2026-05-06_분기_성과보고`

이후 단계에서 `{OUT}`은 이 경로를 가리킨다.

### B. 입력 파일 읽기

`input/` 에서 `_archive/`와 `request.yaml`을 제외한 모든 파일을 찾는다:

```bash
find input/ -not -path 'input/_archive/*' -not -name 'request.yaml' -type f
```

파일 유형별 처리:
- `.md`, `.txt`, `.csv`: Read 도구로 전문 읽기
- `.pdf`: Read 도구 (대용량은 `pages` 파라미터로 범위 분할)
- 이미지 (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`): Read 도구로 시각 분석 — 이미지 내용, 차트·그래프의 수치, 포함된 텍스트를 모두 추출

파일이 없으면 `request.yaml`의 `instructions`만으로 진행한다.

### C. 내용 분석

읽은 자료를 바탕으로 다음을 도출한다:

1. **핵심 메시지** — 이 발표가 전달할 핵심 1가지
2. **주요 포인트** — 청중이 기억해야 할 3~7가지
3. **논리 흐름** — 도입 → 본론 → 결론
4. **이미지 배치** — 이미지 파일이 있으면 어느 슬라이드에 넣을지 결정 (image 타입 슬라이드의 `"image"` 필드에 `"input/파일명"` 경로 사용)

`request.yaml`의 `instructions`를 최우선으로 반영한다.

### D. 슬라이드 구조 설계

`template`별 권장 구성:

| template | 권장 흐름 |
|----------|-----------|
| **report** | title → (section) → bullets → two_column or table → bullets → closing |
| **proposal** | title → section(문제정의) → bullets(현황) → two_column(Before/After) → bullets(제안) → bullets(기대효과) → closing |
| **briefing** | title → bullets(요약) → bullets × N → closing |
| **tutorial** | title → section × N → bullets → image → closing |
| **review** | title → bullets(요약) → two_column(잘된점/개선점) → table → closing |

### E. slides.json 생성

`{OUT}/slides.json`에 저장한다. `{OUT}` 디렉토리가 없으면 생성한다.

```json
{
  "meta": {
    "title": "문서 제목",
    "author": "웰체크팀 서은상",
    "date": "YYYY-MM-DD"
  },
  "slides": []
}
```

**슬라이드 타입별 스키마:**

```json
// 표지
{ "type": "title", "title": "제목", "subtitle": "부제목", "date": "2026-05-06" }

// 섹션 구분 (어두운 배경)
{ "type": "section", "title": "섹션명", "subtitle": "설명" }

// 불릿 리스트
{ "type": "bullets", "title": "슬라이드 제목", "items": ["항목1", "항목2"] }

// 중첩 불릿
{ "type": "bullets", "title": "제목",
  "items": [{ "heading": "소제목", "sub": ["하위항목1", "하위항목2"] }] }

// 흐름 카드 (단계/프로세스 — 카드가 → 화살표로 연결)
{ "type": "flow", "title": "제목",
  "items": [
    { "heading": "단계1", "icon": "🔷", "text": "설명", "color": "blue" },
    { "heading": "단계2", "icon": "✅", "text": "설명", "color": "green" },
    { "heading": "단계3", "icon": "⚠️", "text": "설명", "color": "yellow" }
  ]}
// color 값: blue | green | yellow | purple | red | cyan

// 2열 비교 (기본: items 불릿)
{ "type": "two_column", "title": "제목",
  "left":  { "heading": "왼쪽 제목", "items": ["항목"] },
  "right": { "heading": "오른쪽 제목", "items": ["항목"] } }

// 2열 비교 (확장: rows 테이블 + icon + color + note)
{ "type": "two_column", "title": "제목",
  "left":  { "heading": "AS-IS", "icon": "📄", "color": "blue",
             "rows": [["항목", "값1"], ["항목2", "값2"]], "note": "비고" },
  "right": { "heading": "TO-BE", "icon": "🧠", "color": "purple",
             "rows": [["항목", "값1"], ["항목2", "값2"]], "note": "비고" } }
// color 값: blue | purple | green | yellow
// rows가 있으면 테이블 형식, items가 있으면 불릿 형식

// 핵심 메시지 강조 (callout)
{ "type": "callout", "title": "핵심 메시지 문장", "label": "POINT" }

// 이미지
{ "type": "image", "title": "제목", "image": "input/파일명.png", "caption": "캡션" }

// 인용
{ "type": "quote", "text": "인용 텍스트", "attribution": "출처" }

// 데이터 테이블
{ "type": "table", "title": "제목",
  "headers": ["열1", "열2", "열3"],
  "rows": [["A", "B", "C"], ["D", "E", "F"]] }

// 마지막 슬라이드
{ "type": "closing", "title": "감사합니다", "subtitle": "문의 정보" }
```

**모든 슬라이드에 사용 가능한 선택 필드:**

```json
// 슬라이드 상단 알림 바
"banner": { "text": "경고 또는 안내 메시지", "level": "warning" }
// level 값: warning | error | info

// 슬라이드 우상단 소형 레이블
"label": "DRAFT"

// 슬라이드 하단 요약 바
"summary": "이 슬라이드의 핵심 한 줄 요약"
```

**template별 flow/callout 활용 가이드:**

| template | 추천 활용 |
|----------|-----------|
| **proposal** | flow로 제안 프로세스, callout으로 핵심 기대효과 강조 |
| **report** | flow로 분석 단계, callout으로 결론 메시지 |
| **tutorial** | flow로 설치/실행 순서 |
| **review** | callout으로 핵심 개선 방향 |

**작성 원칙:**
- 슬라이드당 핵심 1가지만
- 불릿 항목당 15단어 이내
- 총 슬라이드: `slide_count` 준수, 미지정 시 8~15장
- 읽은 이미지 파일이 있으면 `image` 타입으로 반드시 포함
- flow는 3~5개 항목이 최적 (2개 이하면 two_column, 6개 이상이면 bullets 권장)

### F. HTML 렌더링

```bash
python3 scripts/render_html.py {OUT}/slides.json --output-dir {OUT}
```

실패 시:
- 오류 메시지를 읽고 `slides.json`의 해당 슬라이드를 수정한 뒤 재실행
- Python 버전 문제라면 `python3 --version` 확인 (3.10+ 필요)

성공 시 `{OUT}/index.html`이 생성된다.

### G. Confluence 문서 생성 (request.yaml에 `confluence: true`인 경우)

`{OUT}/confluence-ready.md`를 생성한다.

형식 규칙:
- `# H1`: 문서 제목
- `## H2`: 섹션 구분
- `### H3`: 슬라이드 내용 제목
- `- 항목`: 불릿 리스트
- GFM 테이블: 데이터 테이블
- `> **핵심:** 내용`: 강조 블록
- `---`: 섹션 구분선
- 이미지: `![캡션](파일경로)` (Confluence에서 첨부파일로 교체 필요 — 파일명 주석 추가)

slides.json 내용을 Confluence 에디터에 바로 붙여넣을 수 있도록 충분히 상세하게 변환한다.

### H. 입력 파일 아카이브

생성이 완료된 뒤 `input/` 루트의 파일과 폴더를 아카이브로 이동한다.

아카이브 디렉토리: `input/_archive/{OUT_NAME}` (`{OUT_NAME}`은 `{OUT}`의 마지막 경로 요소, 예: `2026-05-06_분기_성과보고`)

```bash
mkdir -p "input/_archive/{OUT_NAME}"
# input/ 루트의 파일 이동 (_archive 제외)
find input/ -maxdepth 1 -type f -exec mv {} "input/_archive/{OUT_NAME}/" \;
# input/ 루트의 서브디렉토리 이동 (_archive 제외)
find input/ -maxdepth 1 -mindepth 1 -type d -not -name '_archive' -exec mv {} "input/_archive/{OUT_NAME}/" \;
```

`input/_archive/` 폴더 자체는 이동하지 않는다.

### I. 완료 보고

```
✓ 프레젠테이션: {OUT}/index.html
✓ 슬라이드 구조: {OUT}/slides.json
✓ Confluence: {OUT}/confluence-ready.md  (생성된 경우)
✓ 아카이브: input/_archive/{OUT_NAME}/

슬라이드 구성: N장
  - title (1)
  - section (2)
  - bullets (6)
  - ...

열기: open "{OUT}/index.html"
```
