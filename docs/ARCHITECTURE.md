# 아키텍처

## 디렉토리 구조
```
doc-gen/
├── .claude/commands/
│   ├── doc-gen.md        # /doc-gen 스킬 정의
│   └── harness.md        # /harness 스킬 (코드 개발용, 기존 유지)
├── docs/                 # 프로젝트 문서
├── input/
│   ├── _archive/         # 이전 생성에 사용된 자료 (자동 이동됨)
│   │   └── YYYY-MM-DD_제목/  # 아카이브 폴더 (생성 시마다 자동 생성)
│   ├── request.yaml      # 현재 생성 요청 스펙 (필수)
│   └── [소스 파일들]      # .md, .txt, .pdf, 이미지 등
├── output/
│   └── YYYY-MM-DD_제목/  # 생성 결과물 폴더 (생성 시마다 자동 생성)
│       ├── slides.json        # 슬라이드 구조 (중간 산출물)
│       ├── index.html         # 최종 HTML 프레젠테이션
│       └── confluence-ready.md  # Confluence 붙여넣기 문서 (선택)
├── scripts/
│   ├── render_html.py    # slides.json → HTML 렌더러
│   ├── test_render_html.py  # 렌더러 테스트
│   ├── execute.py        # 코드 개발 하네스 (기존 유지)
│   └── session_start.py  # 세션 훅 (기존 유지)
└── phases/               # 코드 개발 하네스 데이터 (기존 유지)
```

## 패턴: 구조-렌더링 분리
Claude가 `slides.json`(슬라이드 구조 + 내용)을 생성하고, `render_html.py`가 HTML로 변환한다.
두 단계를 분리하면 디자인 변경이 렌더러에만 영향을 미치고, 구조 문제는 JSON을 직접 수정해 재렌더링할 수 있다.

## 데이터 흐름
```
input/ (소스 파일 + request.yaml)
    ↓  /doc-gen 스킬
Claude: 모든 입력 파일 읽기 + 내용 분석
    ↓
Claude: output/YYYY-MM-DD_제목/slides.json 생성
    ↓
render_html.py: output/YYYY-MM-DD_제목/index.html 생성
    ↓ (선택)
Claude: output/YYYY-MM-DD_제목/confluence-ready.md 생성
    ↓
input/ 파일 → input/_archive/YYYY-MM-DD_제목/ 이동
```

## 상태 관리
상태 없음. 매 실행마다 `input/`을 읽고 `output/YYYY-MM-DD_제목/`에 새로 생성한다.
이전 결과물은 `output/` 하위에 날짜+제목 폴더로 영구 보관된다.
