# 프로젝트: Doc-Gen Harness

## 기술 스택
- Python 3.10+ (표준 라이브러리만 사용, 외부 의존성 없음)
- Claude Code CLI (콘텐츠 분석 및 slides.json 생성)
- 순수 HTML/CSS/JS (렌더링 결과물, 외부 CDN 없음)

## 아키텍처 규칙
- CRITICAL: 모든 렌더링은 `scripts/render_html.py`를 통해서만 수행한다. 슬라이드 스타일을 직접 인라인으로 수정하지 않는다.
- CRITICAL: 입력 데이터는 `input/`에, 사용 완료된 자료는 `input/_archive/`에, 생성 결과물은 `output/YYYY-MM-DD_제목/`에 저장한다.
- CRITICAL: 모든 산출물(slides.json `meta.author`, title 슬라이드 `author`, Confluence 작성자 등)의 작성자/발표자 필드는 **"웰체크팀 서은상"** 으로 고정한다. 사용자가 명시적으로 다른 값을 지정한 경우에만 예외.
- 슬라이드 구조(slides.json)와 렌더링을 분리한다. Claude는 구조를 생성하고, 스크립트가 HTML로 변환한다.
- 디자인 시스템(CSS/JS)은 `render_html.py` 한 곳에서만 관리한다.

## 개발 프로세스
- 새 슬라이드 타입 추가 시 `render_html.py`의 `render_slide_html()` 함수와 CSS에 등록한다.
- 커밋 메시지는 conventional commits 형식을 따른다 (feat:, fix:, docs:, refactor:)

## 명령어
```bash
python3 scripts/render_html.py output/YYYY-MM-DD_제목/slides.json   # HTML 렌더링
python3 -m pytest scripts/ -q                                         # 테스트 실행
```
