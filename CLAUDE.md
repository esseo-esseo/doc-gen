# 프로젝트: Doc-Gen Harness

## 기술 스택
- Python 3.10+ (표준 라이브러리만 사용, 외부 의존성 없음)
- Claude Code CLI (콘텐츠 분석 및 slides.json 생성)
- 순수 HTML/CSS/JS (렌더링 결과물, 외부 CDN 없음)

## 아키텍처 규칙
- CRITICAL: 모든 렌더링은 `scripts/render_html.py`를 통해서만 수행한다. 슬라이드 스타일을 직접 인라인으로 수정하지 않는다.
- CRITICAL: 입력 데이터는 `input/`에, 사용 완료된 자료는 `input/_archive/`에, 생성 결과물은 `output/YYYY-MM-DD_제목/`에 저장한다.
- CRITICAL: 새 산출물(slides.json `meta.author`, title 슬라이드 `author`, Confluence 작성자 등)을 만들 때 작성자/발표자 필드는 **작업 시작 시 사용자에게 한 번 물어본 뒤** 받은 값을 사용한다. 인자나 대화 맥락에 이미 명시되어 있으면 묻지 말고 그 값을 그대로 쓴다. 임의의 기본값을 채우지 않는다.
- 슬라이드 구조(slides.json)와 렌더링을 분리한다. Claude는 구조를 생성하고, 스크립트가 HTML로 변환한다.
- 디자인 시스템(CSS/JS)은 `render_html.py` 한 곳에서만 관리한다.

## 템플릿 라이브러리 (PPT 작성 시 우선 활용)
- `template/` 폴더는 다크/라이트 두 디자인 시스템을 통합한 슬라이드 템플릿 카탈로그.
- `template/README.md`의 **"템플릿 매칭 표"** 를 먼저 읽고, 만들 슬라이드의 콘텐츠 의도에 가장 적합한 `slides/NN_*.html`을 선택해 마크업을 복사·재활용한다.
- 공통 CSS는 `template/_shared/styles.css`, 공통 JS는 `template/_shared/deck.js`. 새 결과물은 이를 외부 참조하거나 `<style>` 블록에 그대로 복사해 self-contained로 만든다.
- 이미지가 필요한 자리는 `<div class="img-ph ratio-43/169/916/11">` 형태로 placeholder만 잡는다 (실제 이미지를 임의로 생성하지 않는다).
- 새 슬라이드 패턴이 정말 필요할 때만 `template/slides/`에 새 파일을 추가하고 README 매칭 표를 같이 갱신한다.

## 개발 프로세스
- 새 슬라이드 타입 추가 시 `render_html.py`의 `render_slide_html()` 함수와 CSS에 등록한다.
- 커밋 메시지는 conventional commits 형식을 따른다 (feat:, fix:, docs:, refactor:)

## 명령어
```bash
python3 scripts/render_html.py output/YYYY-MM-DD_제목/slides.json   # HTML 렌더링
python3 -m pytest scripts/ -q                                         # 테스트 실행
```
