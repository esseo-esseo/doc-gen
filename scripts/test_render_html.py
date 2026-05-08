"""render_html.py 테스트 — dark theme."""

import json, sys, tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import render_html as rh

MINIMAL = {
    "meta": {"title": "테스트 발표", "date": "2026-05-07"},
    "slides": [
        {"type": "title",   "title": "표지 제목",  "subtitle": "부제목"},
        {"type": "bullets", "title": "주요 내용",  "items": ["항목1", "항목2"]},
        {"type": "closing", "title": "감사합니다"},
    ],
}

ALL_TYPES = {
    "meta": {"title": "All Types"},
    "slides": [
        {"type": "title",      "title": "Title",    "label": "LABEL", "subtitle": "Sub"},
        {"type": "section",    "title": "Section",  "subtitle": "설명"},
        {"type": "bullets",    "title": "Bullets",  "items": ["a", {"heading": "B", "sub": ["b1"]}]},
        {"type": "flow",       "title": "Flow",
         "items": [{"heading": "S1", "icon": "🔷", "text": "텍스트", "color": "blue"},
                   {"heading": "S2", "icon": "✅", "text": "텍스트", "color": "green"},
                   {"heading": "S3", "icon": "⚠️", "text": "텍스트", "color": "yellow"}]},
        {"type": "two_column", "title": "Compare",
         "left":  {"heading": "Left",  "icon": "📄", "color": "blue",
                   "rows": [["범위", "팀 전체"], ["GIT", "커밋됨"]], "note": "예시"},
         "right": {"heading": "Right", "icon": "🧠", "color": "purple",
                   "rows": [["범위", "개인"],   ["GIT", "로컬"]],    "note": "예시2"}},
        {"type": "image",      "title": "Image",    "image": "nonexistent.png", "caption": "캡션"},
        {"type": "quote",      "text": "인용문",     "attribution": "출처"},
        {"type": "table",      "title": "Table",
         "headers": ["A","B"], "rows": [["1","2"],["3","4"]]},
        {"type": "callout",    "title": "핵심 메시지", "label": "CALLOUT"},
        {"type": "closing",    "title": "끝"},
    ],
}

# ── render() ──

class TestRender:
    def test_creates_index_html(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "slides.json"
            p.write_text(json.dumps(MINIMAL), encoding="utf-8")
            rh.render(str(p), d)
            assert (Path(d) / "index.html").exists()

    def test_html_is_nonempty(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "slides.json"
            p.write_text(json.dumps(MINIMAL), encoding="utf-8")
            rh.render(str(p), d)
            assert (Path(d) / "index.html").stat().st_size > 0

    def test_creates_output_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "slides.json"
            p.write_text(json.dumps(MINIMAL), encoding="utf-8")
            out = Path(d) / "nested" / "deep"
            rh.render(str(p), str(out))
            assert (out / "index.html").exists()

    def test_returns_output_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "slides.json"
            p.write_text(json.dumps(MINIMAL), encoding="utf-8")
            result = rh.render(str(p), d)
            assert result.endswith("index.html")

# ── build_html() ──

class TestBuildHtml:
    def test_contains_title(self):
        assert "테스트 발표" in rh.build_html(MINIMAL)

    def test_contains_slide_content(self):
        html = rh.build_html(MINIMAL)
        assert "주요 내용" in html
        assert "항목1" in html

    def test_contains_navigation(self):
        html = rh.build_html(MINIMAL)
        assert "nav-prev" in html
        assert "nav-next" in html

    def test_contains_download_button(self):
        html = rh.build_html(MINIMAL)
        assert "downloadPDF" in html
        assert "PDF 저장" in html

    def test_no_dots_pagination(self):
        html = rh.build_html(MINIMAL)
        assert '<div class="dot' not in html
        assert 'class="dots"' not in html

    def test_first_slide_is_active(self):
        html = rh.build_html(MINIMAL)
        assert 'class="slide s-title active"' in html

    def test_slide_counter_shows_total(self):
        html = rh.build_html(MINIMAL)
        total_str = str(len(MINIMAL["slides"])).zfill(2)
        assert "<b>01</b>" in html
        assert total_str in html

    def test_print_css_present(self):
        assert "@media print" in rh.build_html(MINIMAL)

    def test_page_break_in_print_css(self):
        assert "page-break-after" in rh.build_html(MINIMAL)

    def test_brand_color_in_css(self):
        assert "#F5A623" in rh.build_html(MINIMAL)

    def test_all_types_render_without_error(self):
        html = rh.build_html(ALL_TYPES)
        assert "Section" in html
        assert "인용문" in html

# ── slide types ──

class TestSlideTypes:
    def test_title_has_h1(self):
        html = rh.render_slide_html({"type": "title", "title": "T"}, 0)
        assert "title-h1" in html

    def test_section_dark_class(self):
        html = rh.render_slide_html({"type": "section", "title": "S"}, 1)
        assert "s-section" in html

    def test_section_has_num(self):
        html = rh.render_slide_html({"type": "section", "title": "S"}, 3)
        assert "section-num" in html
        assert "04" in html

    def test_bullets_card_style(self):
        html = rh.render_slide_html({"type": "bullets", "title": "T", "items": ["X"]}, 0)
        assert 'class="bi"' in html
        assert "bi-dot" in html

    def test_nested_bullets(self):
        html = rh.render_slide_html({
            "type": "bullets", "title": "T",
            "items": [{"heading": "PARENT", "sub": ["CHILD"]}],
        }, 0)
        assert "PARENT" in html
        assert "CHILD" in html
        assert "bi-subs" in html

    def test_flow_type_renders(self):
        html = rh.render_slide_html({"type": "flow", "title": "F", "items": [
            {"heading": "S1", "text": "설명1", "color": "blue"},
            {"heading": "S2", "text": "설명2", "color": "green"},
        ]}, 0)
        assert "flow-card" in html
        assert "flow-arr" in html
        assert "fc-b" in html
        assert "fc-g" in html
        assert "S1" in html

    def test_flow_arrow_count(self):
        html = rh.render_slide_html({"type": "flow", "title": "F", "items": [
            {"heading": "A"}, {"heading": "B"}, {"heading": "C"}
        ]}, 0)
        assert html.count("flow-arr") == 2

    def test_two_column_headings(self):
        html = rh.render_slide_html({
            "type": "two_column", "title": "T",
            "left":  {"heading": "LEFT_H",  "items": ["x"]},
            "right": {"heading": "RIGHT_H", "items": ["y"]},
        }, 0)
        assert "LEFT_H" in html
        assert "RIGHT_H" in html

    def test_two_column_rows_format(self):
        html = rh.render_slide_html({
            "type": "two_column", "title": "T",
            "left":  {"heading": "L", "rows": [["범위", "팀 전체"]]},
            "right": {"heading": "R", "rows": [["범위", "개인"]]},
        }, 0)
        assert "panel-rows" in html
        assert "pr-k" in html
        assert "pr-v" in html
        assert "팀 전체" in html

    def test_two_column_icon(self):
        html = rh.render_slide_html({
            "type": "two_column", "title": "T",
            "left": {"heading": "L", "icon": "📄", "items": []},
            "right": {"heading": "R", "items": []},
        }, 0)
        assert "ph-icon" in html
        assert "<svg" in html

    def test_two_column_note(self):
        html = rh.render_slide_html({
            "type": "two_column", "title": "T",
            "left": {"heading": "L", "note": "예시 노트", "items": []},
            "right": {"heading": "R", "items": []},
        }, 0)
        assert "panel-note" in html
        assert "예시 노트" in html

    def test_two_column_color_blue(self):
        html = rh.render_slide_html({
            "type": "two_column", "title": "T",
            "left": {"heading": "L", "color": "blue", "items": []},
            "right": {"heading": "R", "items": []},
        }, 0)
        assert "panel-b" in html

    def test_image_placeholder_when_missing(self):
        html = rh.render_slide_html({"type": "image", "image": "no.png"}, 0)
        assert "img-ph" in html

    def test_table_headers_and_rows(self):
        html = rh.render_slide_html({
            "type": "table", "title": "T",
            "headers": ["COL_A", "COL_B"],
            "rows":    [["VAL_1", "VAL_2"]],
        }, 0)
        assert "COL_A" in html and "VAL_1" in html
        assert "<thead>" in html and "<tbody>" in html

    def test_closing_dark_class(self):
        assert "s-closing" in rh.render_slide_html({"type": "closing", "title": "Bye"}, 0)

    def test_callout_type(self):
        html = rh.render_slide_html({"type": "callout", "title": "KEY", "label": "LBL"}, 0)
        assert "callout-body" in html
        assert "KEY" in html
        assert "LBL" in html

    def test_unknown_type_fallback(self):
        html = rh.render_slide_html({"type": "unknown", "title": "FB", "items": []}, 0)
        assert "slide-h2" in html

    def test_first_slide_active(self):
        assert "active" in rh.render_slide_html({"type": "title", "title": "T"}, 0)

    def test_non_first_no_active(self):
        assert "active" not in rh.render_slide_html({"type": "title", "title": "T"}, 3)

# ── banner / label / summary ──

class TestOptionalFields:
    def test_banner_warning(self):
        html = rh.render_slide_html({
            "type": "bullets", "title": "T", "items": [],
            "banner": {"text": "경고 메시지", "level": "warning"},
        }, 0)
        assert "sbanner" in html
        assert "sb-warn" in html
        assert "경고 메시지" in html

    def test_banner_error(self):
        html = rh.render_slide_html({
            "type": "title", "title": "T",
            "banner": {"text": "오류", "level": "error"},
        }, 0)
        assert "sb-err" in html

    def test_label_rendered(self):
        html = rh.render_slide_html({"type": "title", "title": "T", "label": "MY LABEL"}, 0)
        assert "MY LABEL" in html
        assert "title-tag" in html

    def test_label_rendered_on_content_slide(self):
        html = rh.render_slide_html({"type": "bullets", "title": "T", "items": [], "label": "MY LABEL"}, 2)
        assert "MY LABEL" in html
        assert "meta-label" in html

    def test_summary_bar(self):
        html = rh.render_slide_html({
            "type": "bullets", "title": "T", "items": [],
            "summary": "핵심 요약 메시지",
        }, 0)
        assert "slide-sum" in html
        assert "핵심 요약 메시지" in html

    def test_no_banner_when_absent(self):
        html = rh.render_slide_html({"type": "title", "title": "T"}, 0)
        assert "sbanner" not in html

# ── esc() ──

class TestEsc:
    def test_lt_gt(self):    assert rh.esc("<b>") == "&lt;b&gt;"
    def test_amp(self):      assert rh.esc("a&b") == "a&amp;b"
    def test_quote(self):    assert rh.esc('"x"') == "&quot;x&quot;"
    def test_plain(self):    assert rh.esc("ok")  == "ok"
    def test_coerce(self):   assert rh.esc(99)    == "99"

# ── encode_image() ──

class TestEncodeImage:
    def test_missing_returns_empty(self):
        assert rh.encode_image("no/such.png") == ""

    def test_existing_returns_data_url(self, tmp_path):
        img = tmp_path / "t.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
        assert rh.encode_image(str(img)).startswith("data:image/png;base64,")
