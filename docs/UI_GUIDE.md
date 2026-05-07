# UI 디자인 가이드

> **이 파일 작성 방법**: `{...}` 형태의 placeholder를 프로젝트 실제 값으로 교체한다.
> 프론트엔드가 없는 프로젝트는 이 파일 전체를 삭제해도 된다.

## 디자인 원칙

1. {원칙 1 — 예: "매일 쓰는 도구처럼 보여야 한다. 마케팅 페이지가 아니다."}
2. {원칙 2 — 예: "정보 밀도를 높여라. 빈 공간 낭비 없음."}
3. {원칙 3 — 예: "인터랙션은 목적이 있을 때만. 장식용 애니메이션 없음."}

---

## AI 슬롭 안티패턴 — 하지 마라

| 금지 사항 | 이유 |
|-----------|------|
| `backdrop-filter: blur()` | glass morphism은 AI 템플릿의 가장 흔한 징후 |
| gradient-text (배경 그라데이션 텍스트) | AI가 만든 SaaS 랜딩의 1번 특징 |
| "Powered by AI" 배지 | 기능이 아니라 장식. 사용자에게 가치 없음 |
| `box-shadow` 글로우 애니메이션 | 네온 글로우 = AI 슬롭 |
| 보라/인디고 브랜드 색상 | "AI = 보라색" 클리셰 |
| 모든 카드에 동일한 `rounded-2xl` | 균일한 둥근 모서리는 템플릿 느낌 |
| 배경 gradient orb (`blur-3xl` 원형) | 모든 AI 랜딩 페이지에 있는 장식 |
| 의미 없는 skeleton loader 남용 | 실제 로딩이 없는 곳에 skeleton 없음 |

---

## 색상 시스템

### 배경
| 용도 | 값 |
|------|------|
| 페이지 | {예: `#0a0a0a`} |
| 카드/패널 | {예: `#141414`} |
| 호버 | {예: `#1a1a1a`} |

### 텍스트
| 용도 | 값 |
|------|------|
| 주 텍스트 | {예: `text-white`} |
| 본문 | {예: `text-neutral-300`} |
| 보조 | {예: `text-neutral-400`} |
| 비활성/placeholder | {예: `text-neutral-500`} |

### 시맨틱 색상
| 용도 | 값 |
|------|------|
| 성공/긍정 | {예: `#22c55e`} |
| 에러/부정 | {예: `#ef4444`} |
| 경고 | {예: `#f59e0b`} |
| 기본/중립 | {예: `#525252`} |
| 브랜드 포인트 | {예: `#3b82f6`} |

### 테두리
| 용도 | 값 |
|------|------|
| 기본 | {예: `border-neutral-800`} |
| 강조 | {예: `border-neutral-600`} |

---

## 컴포넌트 스타일

### 카드
```
{예: rounded-lg bg-[#141414] border border-neutral-800 p-6}
```

### 버튼
```
Primary: {예: rounded-md bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200}
Secondary: {예: rounded-md border border-neutral-700 px-4 py-2 text-sm hover:border-neutral-500}
Text: {예: text-neutral-400 hover:text-white text-sm}
Danger: {예: text-red-400 hover:text-red-300 text-sm}
```

### 입력 필드
```
{예: rounded-md bg-neutral-900 border border-neutral-800 px-3 py-2 text-sm
     focus:border-neutral-600 focus:outline-none placeholder:text-neutral-600}
```

### 뱃지/태그
```
{예: rounded-full border border-neutral-700 px-2 py-0.5 text-xs text-neutral-400}
```

---

## 레이아웃

- 최대 너비: {예: `max-w-5xl`}
- 정렬 기본값: {예: 좌측 정렬. 중앙 정렬은 랜딩 Hero에만 허용}
- 섹션 간격: {예: `space-y-8` 또는 `gap-8`}
- 카드 내부 간격: {예: `p-6`, 소형 카드는 `p-4`}
- 컴포넌트 간 간격: {예: `gap-3` ~ `gap-4`}

### 반응형 브레이크포인트
| 구간 | 처리 방식 |
|------|----------|
| 모바일 (`< 768px`) | {예: 단일 컬럼, 사이드바 숨김} |
| 태블릿 (`768px ~ 1024px`) | {예: 2컬럼, 사이드바 아이콘만} |
| 데스크톱 (`> 1024px`) | {예: 기본 레이아웃} |

---

## 타이포그래피

| 용도 | 스타일 |
|------|--------|
| 페이지 제목 | {예: `text-2xl font-semibold text-white`} |
| 섹션 제목 | {예: `text-base font-medium text-white`} |
| 카드 레이블 | {예: `text-xs font-medium text-neutral-400 uppercase tracking-wider`} |
| 본문 | {예: `text-sm text-neutral-300 leading-relaxed`} |
| 보조 설명 | {예: `text-xs text-neutral-500`} |
| 코드/모노 | {예: `font-mono text-sm text-neutral-300`} |

폰트: {예: 시스템 폰트 스택 (`font-sans`). 커스텀 폰트 없음}

---

## 애니메이션

허용:
- {예: `transition-colors duration-150` — 색상 전환}
- {예: `transition-opacity duration-200` — 페이드}

금지:
- 스크롤 트리거 애니메이션
- 로딩 완료 후 불필요한 엔트런스 애니메이션
- `transition-all` (범위 과다)

---

## 아이콘

- 라이브러리: {예: `lucide-react`}
- 기본 크기: {예: `w-4 h-4`}
- strokeWidth: {예: `1.5`}
- 아이콘을 둥근 배경 박스(컨테이너)로 감싸지 않는다

---

## 금지 패턴 요약

```
❌ 아이콘 컨테이너 박스 (p-2 rounded-lg bg-neutral-800 안에 아이콘)
❌ 카드 타이틀 왼쪽 컬러 보더 (border-l-4 border-blue-500)
❌ 모든 수치에 변화 애니메이션 (숫자가 카운트업)
❌ 상태 표시에 pulse 애니메이션 남용
❌ 빈 상태(Empty state)에 큰 일러스트
```
