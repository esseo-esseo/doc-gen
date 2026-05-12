# 슬라이드 템플릿 카탈로그

`/Users/01-n3360/Downloads/20260312_presentation.html` (다크 테마)와
`/Users/01-n3360/Downloads/20260316_웰체크 약사 서비스 차별화 전략.html` (라이트 테마)
두 원본 디자인을 통합한 재사용 가능한 슬라이드 템플릿 모음.

## 디렉토리 구조

```
template/
├── README.md                ← 이 파일 (사용 가이드 + 템플릿 매칭 표)
├── _shared/
│   ├── styles.css           ← 통합 CSS (라이트 기본 + body.dark)
│   ├── deck.js              ← 공통 JS (nav · theme toggle · PDF save)
│   └── wrapper.html         ← top-actions·nav 마크업 스니펫 (참고용)
└── slides/                  ← 17개 슬라이드 템플릿 (self-contained HTML)
    ├── 01_title.html
    ├── 02_index_grid.html
    ├── ...
    └── 17_image_hero_closing.html
```

## 사용 방법

### A. 단일 슬라이드 미리보기
각 `slides/NN_*.html`을 브라우저로 직접 열면 해당 슬라이드 하나만 표시.
우측 상단의 ☾/☀ 버튼으로 라이트↔다크 전환, ⬇ 버튼으로 PDF 저장.

### B. 새 PPT 결과물 만들 때
1. `output/YYYY-MM-DD_제목/index.html` 새 파일 생성
2. `<link rel="stylesheet" href="../../template/_shared/styles.css">` 로 CSS 참조
   (또는 styles.css 내용을 그대로 `<style>` 블록에 복사 — self-contained 원할 때)
3. 각 슬라이드는 아래 매칭 표에서 적합한 템플릿을 골라 `<div class="slide">` 마크업을 복사
4. 더미 텍스트를 실제 콘텐츠로 교체
5. 우측 상단 액션 버튼·하단 nav는 마지막 슬라이드 뒤에 한 번만 추가

---

## 템플릿 매칭 표 — 콘텐츠 유형 → 적합 템플릿

| 콘텐츠 유형 / 의도 | 권장 템플릿 | 핵심 특징 |
|---|---|---|
| **표지·인트로** (제목, 부제, 메타데이터) | `01_title` | badge + accent-bar + 그라데이션 텍스트 + 메타 3개 |
| **목차 (8개 항목)** — 분석 보고서 풀 스코프 | `02_index_grid` | 2×4 카드 그리드, 각 항목에 아이콘+제목+한 줄 설명 |
| **목차 (4~5개 항목)** — 가벼운 요약·킥오프 | `03_index_vertical` | 세로 정렬 + 가운데 정렬 카드, 더 임팩트 있음 |
| **섹션 개요** — 정의 + 주요 수치 3개 + 운영 주체 표 | `04_section_metrics` | hlbox 정의 + 3 stat cards + 4-row 표 |
| **A vs B 비교** — 두 모델·옵션 비교 후 결정 | `05_comparison_table` | 좌측 라벨 컬럼 + 2개 옵션 컬럼 + 결론 hlbox |
| **세부 유형 분류** — 비교 표 + 보조 수치 카드 | `06_detail_table` | 비교 표 + 하단 3 stat cards |
| **3단계 프로세스** — 단순 흐름 + 사전 준비/포인트 | `07_flow_3step` | 3-step flow + 2 보조 카드 (사전 준비 · 운영 포인트) |
| **3단계 프로세스 — 단가/지표 강조** | `08_flow_fee_pills` | 각 step 내 단가 배지(fee-pill) 강조, 큰 폰트 |
| **수익·비용 시뮬레이션** — 좌 표 / 우 시뮬레이션 | `09_two_column_box` | 좌측 blue 박스 (단가 구조) / 우측 amber 박스 (시뮬레이션 결과) |
| **허들·문제 4개** — 평면 나열 | `10_risk_cards_grid` | 2×2 risk cards, 모두 동등한 비중 |
| **위협 vs 기회** — 좌 risk / 우 opportunity | `11_risk_opp_columns` | 좌측 빨강 risk × N / 우측 초록 opportunity × N + 시사점 bar |
| **4개 강조 메시지** — 핵심 주장·이유 | `12_card_grid_4up` | 2×2 큰 blue 카드 + 하단 핵심 공식 메시지 |
| **3개 기능 + 화면 이미지** | `13_feature_image_3up` | 3-up amber feature 카드, 각 카드에 이미지 placeholder 1개 |
| **2개 큰 기능 + 이미지 페어** | `14_feature_image_2up` | 2-up green feature 카드, 각 카드에 이미지 placeholder 2개 |
| **3-Phase 로드맵·마일스톤** | `15_milestone_timeline` | 가로 그라데이션 트랙 + 3 Phase 원형 번호 + 단계별 설명 |
| **데이터 흐름·아키텍처** | `16_data_architecture` | 3단계 점선 컨테이너 SVG (수집·표준화·외부 연결) + 화살표 마커 |
| **마무리·Closing** — 키 이미지 + 핵심 메시지 | `17_image_hero_closing` | 좌측 큰 이미지 placeholder + 우측 hlbox + gold card + 한 줄 메시지 bar |

---

## 디자인 시스템 요약

### 컬러 토큰
| 토큰 | 라이트 (기본) | 다크 (body.dark) |
|---|---|---|
| **Accent Blue** | `#2563eb` | `#4f8ef7` |
| **Accent Purple** | `#7c3aed` | `#7c3aed` |
| **Body Text** | `#1e293b` | `#e2e8f0` |
| **Muted Text** | `#475569` / `#64748b` | `#cbd5e1` / `#94a3b8` |
| **Card Bg** | `#f8fafc` | `rgba(255,255,255,.04)` |
| **Surface** | `#ffffff` | `#0a0f1e` |
| **Success** | `#059669` (green) | `#6ee7b7` |
| **Warning** | `#d97706` (gold) | `#fcd34d` |
| **Danger** | `#b91c1c` | `#fca5a5` |

### 핵심 컴포넌트 클래스
- `.s-title` — 표지 슬라이드 (그라데이션 배경)
- `.badge` — 그라데이션 캡슐 라벨
- `.title-grad` — 그라데이션 텍스트 (메인 타이틀)
- `.sh` — 슬라이드 헤더 (`.num` + h2 + `.desc`)
- `.cards.c2` / `.c3` / `.c4` / `.c5` — N분할 카드 그리드
- `.card` + `.blue` / `.gold` / `.green` / `.purple` / `.rose` / `.slate` — 컬러 카드
- `.tbl` — 표 (헤더 강조 + hover 효과)
- `.li` — 아이콘+제목+설명의 리스트 아이템
- `.flow` + `.fstep` + `.farr` — 흐름도 단계
- `.fee-pill` — 흐름 단계 내 단가/지표 배지
- `.hlbox` — 강조 박스 (그라데이션 배경)
- `.stats` + `.stat` — 가로 수치 카드 row
- `.bp.bp-b/-g/-r/-y/-p` — 인라인 라벨 (badge pill)
- `.two` — 2-컬럼 grid
- `.col-box.blue` / `.amber` / `.green` / `.purple` — 색상 박스 컨테이너
- `.sec-pill` + `.bar` + `.lbl` — 박스 안 작은 섹션 헤더
- `.ri` (Risk) / `.oi` (Opportunity) — 위협·기회 아이템
- `.feature` + `.green` / `.purple` — 기능 카드 (이미지 포함)
- `.img-ph` + `.ratio-43/169/11/916/hero` — 이미지 placeholder (대시 보더, 비율 자동)
- `.milestone` + `.ms-track` + `.ms-grid` + `.ms-col.p1/p2/p3` — 로드맵 타임라인
- `.step-num` — 그라데이션 원형 번호
- `pre.code` + `.kw/.str/.cm` — 다크 코드 블록

### 공통 동작 (`_shared/deck.js`)
- 16:9 비율 자동 잠금 (브라우저 리사이즈 시 deck 크기 재계산)
- `.sh` 이후 콘텐츠를 `.slide-body`로 자동 wrap → 긴 콘텐츠 스크롤 가능
- 좌/우 화살표 키, 점 클릭, nav 버튼으로 슬라이드 이동
- `toggleTheme()` — body에 `.dark` 클래스 토글
- `savePDF()` — `window.print()` 호출 + 인쇄 직전 모든 슬라이드 펼침

### 인쇄·PDF
- `@page` 1280×720, 모든 색상 강제 인쇄 (`-webkit-print-color-adjust: exact`)
- 인쇄 시 `#nav`, `#top-actions` 자동 숨김
- 각 슬라이드는 별도 페이지로 분리 (`page-break-after: always`)

---

## 작성자 필드 규칙
**작성자 필드는 PPT/문서 생성 작업 시작 시 사용자에게 한 번 묻고 받은 값을 사용한다.**
인자나 대화 맥락에 이미 명시되어 있으면 묻지 말고 그 값을 그대로 쓴다. 임의의 기본값(예: 팀명·이름)을 채우지 않는다. 템플릿 파일에 남아있는 작성자 placeholder는 어디까지나 예시이며 실제 결과물에서는 사용자 응답으로 교체한다.

## 새 슬라이드 패턴이 필요할 때
1. 두 원본 HTML(`/Users/01-n3360/Downloads/20260312_presentation.html`, `20260316_웰체크…`)에서 유사한 마크업 검색
2. 없다면 기존 컴포넌트(`.card`, `.hlbox`, `.two`, `.flow`)를 조합
3. 정말 새 컴포넌트가 필요하면 `_shared/styles.css`에 새 클래스 정의 + 다크 모드 오버라이드 + README 매칭 표에 항목 추가
4. `slides/NN_*.html`로 새 템플릿 파일 저장
