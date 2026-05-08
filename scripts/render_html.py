#!/usr/bin/env python3
"""
render_html.py — slides.json → self-contained HTML presentation.

Slide types: title, section, bullets, flow, two_column, image, quote, table,
             closing, callout, metric, agenda

Any slide accepts optional fields:
  banner:  { text, level }  — top alert bar  (info / warning / error / success)
  label:   "CATEGORY · SUB" — small uppercase label above title
  summary: "text"           — bottom callout bar

Enhanced two_column fields:
  left/right.icon, left/right.color (blue|purple|green|yellow),
  left/right.rows [["label","value"],...], left/right.note

flow items: { heading, icon, text, color }

metric items: { value, label, delta, caption } (1-4 items per slide)
agenda items: [{ heading, sub }] or ["heading", ...]
"""

import argparse, base64, json, mimetypes, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def encode_image(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        return ""
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

def esc(v) -> str:
    return (str(v)
        .replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;"))

# ---------------------------------------------------------------------------
# Icon system — Lucide-style stroke SVGs (replaces emoji)
# ---------------------------------------------------------------------------

ICON_PATHS = {
    "check":      '<polyline points="20 6 9 17 4 12"/>',
    "warning":    '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "info":       '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "megaphone":  '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    "database":   '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "user":       '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "key":        '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
    "settings":   '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.09a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.09a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "link":       '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "file":       '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "rocket":     '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    "brain":      '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>',
    "lightbulb":  '<line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>',
    "chart":      '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "refresh":    '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    "diamond":    '<path d="M12 2 22 12 12 22 2 12Z"/>',
    "circle":     '<circle cx="12" cy="12" r="9"/>',
    "target":     '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "zap":        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "trend":      '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "shield":     '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "compass":    '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
}

EMOJI_TO_ICON = {
    "🔷": "diamond", "🔶": "diamond", "✅": "check", "✔": "check", "✔️": "check",
    "⚠️": "warning", "⚠": "warning", "ℹ️": "info", "📢": "megaphone", "📣": "megaphone",
    "💾": "database", "🗄️": "database", "🗃️": "database",
    "👤": "user", "👥": "user", "🧑": "user",
    "🔑": "key", "🗝️": "key",
    "⚙️": "settings", "⚙": "settings", "🔧": "settings",
    "🔗": "link", "📄": "file", "📋": "file", "📃": "file", "📑": "file",
    "🚀": "rocket", "🧠": "brain", "💡": "lightbulb", "🔭": "lightbulb",
    "📊": "chart", "📈": "trend", "📉": "trend",
    "🔁": "refresh", "🔄": "refresh",
    "🎯": "target", "⚡": "zap", "🛡️": "shield", "🧭": "compass",
}

def _icon_svg(name: str, size: int = 28, stroke: float = 1.75) -> str:
    body = ICON_PATHS.get(name)
    if not body:
        return ""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )

def _resolve_icon(raw: str, size: int = 28) -> str:
    """이모지 또는 아이콘 이름을 inline SVG로 변환. 매칭 없으면 빈 문자열."""
    if not raw:
        return ""
    name = EMOJI_TO_ICON.get(raw)
    if name:
        return _icon_svg(name, size)
    if raw in ICON_PATHS:
        return _icon_svg(raw, size)
    return ""

# ---------------------------------------------------------------------------
# Content validation (P3-3)
# ---------------------------------------------------------------------------

MAX_ITEMS = {
    "bullets":   5,
    "flow":      5,
    "agenda":    8,
    "metric":    4,
    "table":     8,   # rows
}

def _validate_slide(slide: dict, index: int) -> None:
    t = slide.get("type", "")
    n = None
    if t in ("bullets", "flow", "agenda", "metric"):
        n = len(slide.get("items", []))
    elif t == "two_column":
        l = slide.get("left", {})
        r = slide.get("right", {})
        n = max(
            len(l.get("items", []) or l.get("rows", [])),
            len(r.get("items", []) or r.get("rows", [])),
        )
        limit = 6
        if n > limit:
            print(
                f"  ⚠ 슬라이드 #{index+1} (two_column): 항목 {n}개 — 권장 최대 {limit}개",
                file=sys.stderr,
            )
        return
    elif t == "table":
        n = len(slide.get("rows", []))
    limit = MAX_ITEMS.get(t)
    if limit and n is not None and n > limit:
        print(
            f"  ⚠ 슬라이드 #{index+1} ({t}): 항목 {n}개 — 권장 최대 {limit}개",
            file=sys.stderr,
        )

# ---------------------------------------------------------------------------
# Shared fragment helpers
# ---------------------------------------------------------------------------

def _banner(s: dict) -> str:
    b = s.get("banner")
    if not b:
        return ""
    lv = b.get("level", "info")
    cls = {"warning": "sb-warn", "error": "sb-err", "success": "sb-ok"}.get(lv, "sb-info")
    return f'<div class="sbanner {cls}">{esc(b.get("text", ""))}</div>'

def _label(s: dict) -> str:
    lbl = s.get("label", "")
    return f'<div class="slide-lbl">{esc(lbl)}</div>' if lbl else ""

def _summary(s: dict) -> str:
    txt = s.get("summary", "")
    return f'<div class="slide-sum">{esc(txt)}</div>' if txt else ""

def _accent() -> str:
    return '<div class="acc-bar"></div>'

def _slide_meta(s: dict, i: int, default_label: str = "") -> str:
    """상단 kicker: 페이지 번호 + 짧은 가로선 + 라벨."""
    num = str(i + 1).zfill(2)
    label = s.get("label") or default_label
    label_h = f'<span class="meta-label">{esc(label)}</span>' if label else ""
    return (
        f'<div class="slide-meta">'
        f'<span class="meta-num">{num}</span>'
        f'<span class="meta-line"></span>'
        f'{label_h}'
        f'</div>'
    )

def _wrap(content: str, index: int, cls: str = "") -> str:
    classes = "slide"
    if cls.strip():
        classes += " " + cls.strip()
    if index == 0:
        classes += " active"
    return f'<div class="{classes}" data-index="{index}">{content}</div>'

def _items_html(items: list) -> str:
    if not items:
        return ""
    parts = ['<ul class="bullet-list">']
    for item in items:
        if isinstance(item, dict):
            head = esc(item.get("heading", ""))
            subs = item.get("sub", [])
            sub_h = ""
            if subs:
                sub_h = '<ul class="bi-subs">' + "".join(
                    f"<li>{esc(str(s))}</li>" for s in subs
                ) + "</ul>"
            parts.append(
                f'<li class="bi"><div class="bi-dot"></div>'
                f'<div class="bi-body"><span class="bi-heading">{head}</span>{sub_h}</div></li>'
            )
        else:
            parts.append(
                f'<li class="bi"><div class="bi-dot"></div>'
                f'<div class="bi-body"><span class="bi-text">{esc(str(item))}</span></div></li>'
            )
    parts.append("</ul>")
    return "".join(parts)

def _is_numeric_cell(s: str) -> bool:
    """천 단위 콤마, %, 한글 단위(원/명/억/만), 부호, 화살표를 제거한 뒤 숫자 검사."""
    cleaned = s.strip()
    for ch in [",", "%", "원", "명", "억", "만", "+", "-", "▲", "▼", " ", ".", "건", "회"]:
        cleaned = cleaned.replace(ch, "")
    return bool(cleaned) and cleaned.isdigit()

# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def _title(s: dict, i: int) -> str:
    title  = esc(s.get("title", ""))
    sub    = esc(s.get("subtitle", ""))
    date   = esc(s.get("date", ""))
    author = esc(s.get("author", ""))
    label  = esc(s.get("label", "PRESENTATION"))
    author_h = f'<span class="title-author">{author}</span>' if author else '<span></span>'
    date_h   = f'<span class="title-date">{date}</span>'     if date   else '<span></span>'
    return _wrap(
        _banner(s) +
        f'<div class="title-stage">'
        f'<div class="title-top"><span class="title-tag">{label}</span></div>'
        f'<div class="title-mid">'
        f'<h1 class="title-h1">{title}</h1>'
        f'<div class="title-line"></div>'
        + (f'<p class="title-sub">{sub}</p>' if sub else "") +
        f'</div>'
        f'<div class="title-bot">{author_h}{date_h}</div>'
        f'</div>' +
        _summary(s),
        i, "s-title",
    )

def _section(s: dict, i: int) -> str:
    num = str(i + 1).zfill(2)
    return _wrap(
        _banner(s) +
        f'<div class="section-stage">'
        f'<div class="section-num">{num}</div>'
        f'<div class="section-tag">SECTION</div>'
        f'<h2 class="section-h2">{esc(s.get("title", ""))}</h2>'
        f'<div class="section-accent"></div>'
        + (f'<p class="section-sub">{esc(s.get("subtitle",""))}</p>' if s.get("subtitle") else "") +
        f'</div>' +
        _summary(s),
        i, "s-section",
    )

def _bullets(s: dict, i: int) -> str:
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>'
        f'<div class="slide-body">{_items_html(s.get("items", []))}</div>' +
        _summary(s) +
        f'</main>',
        i, "s-bullets",
    )

def _flow(s: dict, i: int) -> str:
    COLOR_MAP = {
        "blue": "fc-b", "green": "fc-g", "yellow": "fc-y",
        "purple": "fc-p", "red": "fc-r", "cyan": "fc-c",
    }
    DEFAULTS = ["fc-b", "fc-g", "fc-y", "fc-p", "fc-r", "fc-c"]
    items = s.get("items", [])
    parts = []
    for j, item in enumerate(items):
        col = COLOR_MAP.get(item.get("color", ""), DEFAULTS[j % len(DEFAULTS)])
        icon_svg = _resolve_icon(item.get("icon", ""), 24)
        icon = f'<span class="fc-icon">{icon_svg}</span>' if icon_svg else ""
        step = f'<span class="fc-step">{str(j+1).zfill(2)}</span>'
        parts.append(
            f'<div class="flow-card {col}">'
            f'<div class="fc-top">{step}{icon}</div>'
            f'<div class="fc-heading">{esc(item.get("heading",""))}</div>'
            f'<p class="fc-text">{esc(item.get("text",""))}</p>'
            f'</div>'
        )
    arrow_svg = (
        '<div class="flow-arr">'
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>'
        '</svg></div>'
    )
    cards_html = arrow_svg.join(parts)
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>'
        f'<div class="flow-row">{cards_html}</div>' +
        _summary(s) +
        f'</main>',
        i, "s-flow",
    )

def _two_column(s: dict, i: int) -> str:
    COLOR_MAP = {"blue": "panel-b", "purple": "panel-p", "green": "panel-g", "yellow": "panel-y"}
    DEFAULTS  = ["panel-b", "panel-p"]

    def panel(data: dict, idx: int) -> str:
        col   = COLOR_MAP.get(data.get("color", ""), DEFAULTS[idx % 2])
        icon_svg = _resolve_icon(data.get("icon", ""), 22)
        icon  = f'<span class="ph-icon">{icon_svg}</span>' if icon_svg else ""
        hdr   = (f'<div class="panel-hdr">{icon}'
                 f'<span class="ph-name">{esc(data.get("heading",""))}</span></div>')
        rows  = data.get("rows", [])
        items = data.get("items", [])
        note  = data.get("note", "")
        if rows:
            rows_html = "".join(
                f'<div class="pr">'
                f'<span class="pr-k">{esc(str(r[0]) if len(r) > 0 else "")}</span>'
                f'<span class="pr-v">{esc(str(r[1]) if len(r) > 1 else "")}</span>'
                f'</div>'
                for r in rows
            )
            body = f'<div class="panel-rows">{rows_html}</div>'
        else:
            lis  = "".join(f'<li>{esc(str(it))}</li>' for it in items)
            body = f'<div class="panel-body"><ul class="panel-items">{lis}</ul></div>'
        note_h = f'<div class="panel-note">{esc(note)}</div>' if note else ""
        return f'<div class="panel {col}">{hdr}{body}{note_h}</div>'

    left  = s.get("left", {})
    right = s.get("right", {})
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>'
        f'<div class="panels-row">{panel(left, 0)}{panel(right, 1)}</div>' +
        _summary(s) +
        f'</main>',
        i, "s-two-col",
    )

def _image_slide(s: dict, i: int) -> str:
    title   = s.get("title", "")
    caption = s.get("caption", "")
    src     = encode_image(s.get("image", ""))
    img     = (f'<img src="{src}" alt="{esc(caption)}" class="slide-img">'
               if src else f'<div class="img-ph">[이미지: {esc(s.get("image",""))}]</div>')
    cap     = f'<p class="img-cap">{esc(caption)}</p>' if caption else ""
    if title:
        hdr  = f'<div class="slide-hdr"><h2 class="slide-h2">{esc(title)}</h2>{_accent()}</div>'
        body = f'<div class="img-body">{img}{cap}</div>'
        return _wrap(
            _banner(s) +
            _slide_meta(s, i) +
            f'<main class="slide-main">{hdr}{body}{_summary(s)}</main>',
            i, "s-image",
        )
    body = f'<div class="img-body-full">{img}{cap}</div>'
    return _wrap(_banner(s) + body + _summary(s), i, "s-image s-image-full")

def _quote(s: dict, i: int) -> str:
    attr_h = f'<p class="q-attr">— {esc(s.get("attribution",""))}</p>' if s.get("attribution") else ""
    return _wrap(
        _banner(s) +
        f'<div class="q-mark">"</div>'
        f'<blockquote class="q-text">{esc(s.get("text",""))}</blockquote>'
        f'{attr_h}' +
        _summary(s),
        i, "s-quote",
    )

def _table(s: dict, i: int) -> str:
    headers = s.get("headers", [])
    rows    = s.get("rows", [])
    # P1-8: 숫자 컬럼 자동 감지 → 우측 정렬 + tabular-nums
    num_cols: set[int] = set()
    if rows:
        col_count = max((len(r) for r in rows), default=0)
        for ci in range(col_count):
            cells = [str(r[ci]).strip() for r in rows if ci < len(r) and str(r[ci]).strip()]
            if cells and all(_is_numeric_cell(c) for c in cells):
                num_cols.add(ci)
    thead   = ""
    if headers:
        ths = "".join(
            f'<th class="num-col">{esc(h)}</th>' if idx in num_cols else f"<th>{esc(h)}</th>"
            for idx, h in enumerate(headers)
        )
        thead = f"<thead><tr>{ths}</tr></thead>"
    tbody   = ""
    if rows:
        trs = []
        for r in rows:
            cells = []
            for idx, c in enumerate(r):
                cls = ' class="num-col"' if idx in num_cols else ""
                cells.append(f"<td{cls}>{esc(str(c))}</td>")
            trs.append("<tr>" + "".join(cells) + "</tr>")
        tbody = f"<tbody>{''.join(trs)}</tbody>"
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>'
        f'<div class="slide-body tbl-body"><table class="data-tbl">{thead}{tbody}</table></div>' +
        _summary(s) +
        f'</main>',
        i, "s-table",
    )

def _closing(s: dict, i: int) -> str:
    sub_h = f'<p class="closing-sub">{esc(s.get("subtitle",""))}</p>' if s.get("subtitle") else ""
    return _wrap(
        _banner(s) +
        f'<div class="closing-body"><h2 class="closing-h">{esc(s.get("title","감사합니다"))}</h2>{sub_h}</div>'
        f'<div class="closing-bar"></div>',
        i, "s-closing",
    )

def _callout(s: dict, i: int) -> str:
    lbl_h = f'<div class="callout-lbl">{esc(s.get("label",""))}</div>' if s.get("label") else ""
    return _wrap(
        _banner(s) +
        f'<div class="callout-body">{lbl_h}'
        f'<div class="callout-rule"></div>'
        f'<p class="callout-text">{esc(s.get("title",""))}</p>'
        f'<div class="callout-rule"></div>'
        f'</div>',
        i, "s-callout",
    )

def _metric(s: dict, i: int) -> str:
    """metric: 1-4개 빅 넘버 카드. 타이틀 없으면 hero(중앙) 모드."""
    title = s.get("title", "")
    items = s.get("items", [])
    if not items:
        items = [{
            "value":   s.get("value", ""),
            "label":   s.get("metric_label") or s.get("label", ""),
            "delta":   s.get("delta", ""),
            "caption": s.get("caption", ""),
        }]
    n = max(1, min(len(items), 4))
    grid_cls = f"metric-grid-{n}"
    is_hero  = (n == 1 and not title)

    cards = []
    for it in items:
        value   = esc(it.get("value", ""))
        label   = esc(it.get("label", ""))
        caption = esc(it.get("caption", ""))
        delta_raw = str(it.get("delta", "")).strip()
        delta_h = ""
        if delta_raw:
            first = delta_raw[0] if delta_raw else ""
            if first in ("+", "▲"):
                d_cls = "metric-delta-up"
            elif first in ("-", "▼", "−"):
                d_cls = "metric-delta-down"
            else:
                d_cls = "metric-delta-neutral"
            delta_h = f'<span class="metric-delta {d_cls}">{esc(delta_raw)}</span>'
        label_h   = f'<div class="metric-label">{label}</div>' if label else ""
        caption_h = f'<div class="metric-caption">{caption}</div>' if caption else ""
        cards.append(
            f'<div class="metric-card">'
            f'{label_h}'
            f'<div class="metric-value">{value}{delta_h}</div>'
            f'{caption_h}'
            f'</div>'
        )
    cards_html = "".join(cards)

    if is_hero:
        # 표지급 단일 메트릭 — 슬라이드 가운데 큰 숫자
        return _wrap(
            _banner(s) +
            f'<div class="metric-hero">{cards_html}</div>' +
            _summary(s),
            i, "s-metric s-metric-hero",
        )
    title_h = (
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(title)}</h2>{_accent()}</div>'
        if title else ""
    )
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'{title_h}'
        f'<div class="metric-row {grid_cls}">{cards_html}</div>' +
        _summary(s) +
        f'</main>',
        i, "s-metric",
    )

def _agenda(s: dict, i: int) -> str:
    """agenda/TOC: 번호 매김 + 헤딩 (+ 부제)."""
    title = esc(s.get("title", "AGENDA"))
    items = s.get("items", [])
    rows = []
    for j, it in enumerate(items):
        if isinstance(it, dict):
            heading = esc(it.get("heading", ""))
            sub     = esc(it.get("sub", ""))
        else:
            heading = esc(str(it))
            sub     = ""
        sub_h = f'<span class="ag-sub">{sub}</span>' if sub else ""
        rows.append(
            f'<li class="ag-item">'
            f'<span class="ag-num">{str(j+1).zfill(2)}</span>'
            f'<div class="ag-body">'
            f'<span class="ag-heading">{heading}</span>'
            f'{sub_h}'
            f'</div>'
            f'</li>'
        )
    return _wrap(
        _banner(s) +
        _slide_meta(s, i) +
        f'<main class="slide-main">'
        f'<div class="slide-hdr"><h2 class="slide-h2">{title}</h2>{_accent()}</div>'
        f'<ol class="agenda-list">{"".join(rows)}</ol>' +
        _summary(s) +
        f'</main>',
        i, "s-agenda",
    )

RENDERERS = {
    "title":      _title,
    "section":    _section,
    "bullets":    _bullets,
    "flow":       _flow,
    "two_column": _two_column,
    "image":      _image_slide,
    "quote":      _quote,
    "table":      _table,
    "closing":    _closing,
    "callout":    _callout,
    "metric":     _metric,
    "agenda":     _agenda,
}

def render_slide_html(slide: dict, index: int) -> str:
    fn = RENDERERS.get(slide.get("type", "bullets"), _bullets)
    return fn(slide, index)

# ---------------------------------------------------------------------------
# CSS — semantic tokens, dark mode, presenter UX
# ---------------------------------------------------------------------------

CSS = """\
*{margin:0;padding:0;box-sizing:border-box}

/* === Design tokens — semantic naming (P3-5) === */
:root{
  /* Surface */
  --color-bg-default:#F4F1EC;
  --color-surface-default:#FCFBF8;
  --color-surface-elevated:#F5F2EC;
  --color-surface-section:#EAE3D5;        /* P1-2: section 명도차 강화 */
  --color-surface-muted:#F0EDE5;
  --color-surface-overlay:#FBFAF6;
  /* Border */
  --color-border-subtle:#DDD8CE;
  --color-border-default:#C4BEB1;
  --color-border-strong:#9C9689;
  --color-border-ink:#1A1815;
  /* Text */
  --color-text-primary:#1A1815;
  --color-text-secondary:#3D3A33;
  --color-text-tertiary:#6B6660;
  --color-text-disabled:#B5B0A5;
  --color-text-inverse:#FCFBF8;
  /* Accents — P0-1: 실제 다른 색 */
  --color-accent-primary:#F5A623;          /* 주 오렌지 — 그룹 브랜드 */
  --color-accent-info:#3A7CA5;             /* AS-IS, 정보 */
  --color-accent-success:#5A8F4A;          /* TO-BE, 성공 */
  --color-accent-warning:#C68D2A;
  --color-accent-danger:#C84545;
  --color-accent-purple:#7A5BA5;
  --color-accent-cyan:#2B8AA5;
  /* Banner tints */
  --color-banner-info-bg:rgba(245,166,35,.08);
  --color-banner-warn-bg:rgba(245,166,35,.14);
  --color-banner-err-bg:rgba(200,69,69,.07);
  --color-banner-ok-bg:rgba(90,143,74,.08);
  /* Spacing — 8pt grid (P1-6) */
  --sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;
  --sp-5:24px;--sp-6:32px;--sp-7:48px;--sp-8:64px;--sp-9:80px;
  /* Slide padding — stage container 기준 (cqi/cqb), viewport에 종속되지 않음 */
  --sp-v:clamp(28px,5.5cqb,72px);--sp-h:clamp(36px,5.5cqi,96px);
  /* Type scale — stage 너비(cqi) 기반: 브라우저 크기와 무관하게 슬라이드에 비례 */
  --fs-2xs:clamp(9px,.85cqi,12px);
  --fs-xs: clamp(10px,1cqi,13px);
  --fs-sm: clamp(12px,1.2cqi,15px);
  --fs-base:clamp(13px,1.35cqi,17px);
  --fs-md: clamp(14px,1.55cqi,20px);
  --fs-lg: clamp(17px,2cqi,26px);
  --fs-xl: clamp(20px,2.6cqi,34px);
  --fs-2xl:clamp(24px,3.4cqi,44px);
  --fs-3xl:clamp(30px,4.4cqi,58px);
  --fs-4xl:clamp(38px,5.8cqi,74px);
  --fs-display:clamp(48px,8cqi,116px);
  --fs-metric-l:clamp(48px,7.5cqi,120px);
  --fs-metric-m:clamp(36px,5.5cqi,90px);
  /* Line heights */
  --lh-tight:1.22;--lh-snug:1.45;--lh-normal:1.6;--lh-relaxed:1.75;
  /* Weights — P1-1: 3-step ladder */
  --fw-normal:400;--fw-medium:600;--fw-bold:700;
  /* Shadow */
  --shadow-stage:0 1px 2px rgba(0,0,0,.04),0 8px 32px rgba(0,0,0,.08);
  --shadow-card:0 1px 3px rgba(0,0,0,.04);
  /* Fonts */
  --font:Pretendard,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
  --mono:'JetBrains Mono','SF Mono','Menlo','Consolas','Monaco','Courier New',monospace;
  /* Measure — P0-4: 한글 35-45자 */
  --measure:38ch;
  --measure-wide:48ch;

  /* Backwards-compat aliases (legacy short names) */
  --bg:var(--color-bg-default);--sbg:var(--color-surface-default);
  --c1:var(--color-surface-elevated);--c2:#EFEBE3;--c3:#E6E1D7;
  --tone:var(--color-surface-section);
  --bo:var(--color-border-subtle);--bm:var(--color-border-default);--bl:var(--color-border-strong);
  --b:var(--color-accent-primary);--p:var(--color-accent-purple);
  --cy:var(--color-accent-cyan);--y:var(--color-accent-warning);
  --g:var(--color-accent-success);--r:var(--color-accent-danger);
  --t1:var(--color-text-primary);--t2:var(--color-text-secondary);
  --t3:var(--color-text-tertiary);--t4:var(--color-text-disabled);
}

/* === Dark mode (P2-1) — light/dark only, manual toggle === */
:root[data-theme='dark']{
  --color-bg-default:#15130F;
  --color-surface-default:#1F1C16;
  --color-surface-elevated:#28241D;
  --color-surface-section:#2A251D;
  --color-surface-muted:#231F18;
  --color-surface-overlay:#1A1814;
  --color-border-subtle:#332F26;
  --color-border-default:#4D4839;
  --color-border-strong:#736D5C;
  --color-border-ink:#D6D2C8;
  --color-text-primary:#F4F1EC;
  --color-text-secondary:#C4BEB1;
  --color-text-tertiary:#9C9689;
  --color-text-disabled:#6B6660;
  --color-text-inverse:#1A1815;
  --color-banner-info-bg:rgba(245,166,35,.14);
  --color-banner-warn-bg:rgba(245,166,35,.18);
  --color-banner-err-bg:rgba(200,69,69,.14);
  --color-banner-ok-bg:rgba(90,143,74,.14);
  --shadow-stage:0 1px 2px rgba(0,0,0,.5),0 8px 32px rgba(0,0,0,.55);
  --shadow-card:0 1px 3px rgba(0,0,0,.4);
}

html,body{width:100%;height:100%;background:var(--color-bg-default);font-family:var(--font);overflow:hidden;color:var(--color-text-primary);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;font-feature-settings:'tnum','calt';transition:background .25s,color .25s}

/* Layout — viewport 크기에 안전 (toolbar+nav 높이 = 약 100px 차감) */
.pres{width:100vw;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:60px 12px 12px;box-sizing:border-box}
.deck{display:flex;flex-direction:column;gap:10px;width:min(calc((100vh - 120px) * 16/9),calc(100vw - 24px));max-width:100%}
.stage{
  position:relative;width:100%;aspect-ratio:16/9;
  background:var(--color-surface-default);overflow:hidden;
  border-radius:2px;
  box-shadow:var(--shadow-stage);
  container-type:size;container-name:stage
}

/* Progress bar */
.prog{position:absolute;top:0;left:0;height:2px;width:0;z-index:50;
  background:var(--color-accent-primary);transition:width .35s cubic-bezier(.4,0,.2,1)}

/* Slide base — 모든 콘텐츠는 stage 안에서 잘림 (overflow:hidden) */
.slide{
  position:absolute;inset:0;display:none;flex-direction:column;justify-content:flex-start;
  padding:var(--sp-v) var(--sp-h);background:var(--color-surface-default);
  overflow:hidden;min-width:0;min-height:0
}
.slide.active{display:flex;animation:fadein .22s ease-out}
.s-bullets.active,.s-flow.active,.s-two-col.active,.s-table.active,
.s-image:not(.s-image-full).active,.s-metric.active:not(.s-metric-hero),
.s-agenda.active{
  display:flex;flex-direction:column;
  align-items:stretch;justify-content:flex-start;
  padding-bottom:calc(var(--sp-v) + clamp(20px,2.6cqb,36px))
}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
@media (prefers-reduced-motion:reduce){
  .slide.active{animation:none}
  *{transition:none !important}
}

/* Slide-meta — top kicker */
.slide-meta{display:flex;align-items:center;gap:14px;width:100%;flex-shrink:0;margin-bottom:clamp(14px,1.6cqb,22px)}
.meta-num{font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-text-primary);font-family:var(--mono);line-height:1;letter-spacing:.06em;font-variant-numeric:tabular-nums}
.meta-line{flex:0 0 24px;height:1px;background:var(--color-text-primary)}
.meta-label{font-size:var(--fs-2xs);font-weight:var(--fw-bold);color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.08em;line-height:1.3;font-family:var(--mono)}
.slide-main{display:flex;flex-direction:column;min-width:0;min-height:0;flex:1;justify-content:flex-start;width:100%;overflow:hidden}

/* Banner — P0-2: 한글 친화 자간 */
.sbanner{
  margin:calc(-1*var(--sp-v)) calc(-1*var(--sp-h)) 14px;
  padding:8px var(--sp-h);
  font-size:var(--fs-xs);font-family:var(--mono);letter-spacing:.04em;
  display:flex;align-items:center;flex-shrink:0;border-left:3px solid;gap:8px
}
.sb-info{background:var(--color-banner-info-bg);border-color:var(--color-accent-primary);color:#A07000}
.sb-warn{background:var(--color-banner-warn-bg);border-color:var(--color-accent-warning);color:#92600A}
.sb-err{background:var(--color-banner-err-bg);border-color:var(--color-accent-danger);color:#9C2828}
.sb-ok{background:var(--color-banner-ok-bg);border-color:var(--color-accent-success);color:#1F5C30}
:root[data-theme='dark'] .sb-info{color:#FFC675}
:root[data-theme='dark'] .sb-warn{color:#FFC675}
:root[data-theme='dark'] .sb-err{color:#FF9090}
:root[data-theme='dark'] .sb-ok{color:#A4D894}

/* Label / header / accent — P0-2: letter-spacing 0.22em → 0.04em */
.slide-lbl{font-size:var(--fs-2xs);font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-tertiary);margin-bottom:8px;flex-shrink:0;font-family:var(--mono)}
.slide-hdr{flex-shrink:0;margin-bottom:clamp(20px,2.6cqb,36px)}
.slide-h2{font-size:var(--fs-2xl);font-weight:var(--fw-bold);color:var(--color-text-primary);margin-bottom:clamp(10px,1.2cqb,16px);line-height:1.28;letter-spacing:-.005em;max-width:var(--measure-wide);word-break:keep-all;overflow-wrap:break-word}
.acc-bar{height:2px;width:clamp(32px,3.5cqi,44px);border-radius:0;background:var(--color-accent-primary);margin-top:14px}
.slide-body{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-start;width:100%}

/* Summary bar */
.slide-sum{flex-shrink:0;margin-top:clamp(20px,2.4cqb,28px);padding:clamp(14px,1.6cqb,18px) clamp(18px,1.8cqi,22px);background:var(--color-surface-elevated);border-left:2px solid var(--color-accent-primary);font-size:var(--fs-sm);color:var(--color-text-secondary);font-weight:var(--fw-normal);line-height:1.6;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}

/* Title slide */
.s-title{overflow:hidden;justify-content:stretch;background:var(--color-surface-default)}
.s-title::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:var(--color-border-subtle)}
.title-stage{flex:1;display:grid;grid-template-rows:auto 1fr auto;width:100%;position:relative;z-index:2}
.title-top{display:flex;align-items:flex-start;padding-top:clamp(56px,6cqb,84px)}
.title-tag{font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-accent-primary);text-transform:uppercase;letter-spacing:.12em;font-family:var(--mono)}
.title-mid{display:flex;flex-direction:column;justify-content:center;max-width:92%}
.title-h1{font-size:var(--fs-4xl);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.14;letter-spacing:-.01em;margin-bottom:clamp(24px,3cqb,40px);word-break:keep-all;overflow-wrap:break-word}
.title-line{width:clamp(40px,4.5cqi,56px);height:2px;flex-shrink:0;background:var(--color-accent-primary);border-radius:0;margin-bottom:clamp(20px,2.6cqb,30px)}
.title-sub{font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--color-text-secondary);line-height:1.55;max-width:var(--measure-wide);word-break:keep-all;overflow-wrap:break-word;letter-spacing:0}
.title-bot{display:flex;align-items:flex-end;justify-content:space-between;padding-bottom:clamp(8px,1cqb,14px);border-top:1px solid var(--color-border-subtle);padding-top:clamp(16px,2cqb,24px);margin-top:clamp(16px,2cqb,24px)}
.title-date{font-size:var(--fs-xs);font-weight:var(--fw-medium);color:var(--color-text-tertiary);font-family:var(--mono);letter-spacing:.06em}
.title-author{font-size:var(--fs-sm);font-weight:var(--fw-medium);color:var(--color-text-secondary);letter-spacing:0;word-break:keep-all}

/* Section slide — P1-2: tone & layout 강화 */
.s-section{background:var(--color-surface-section);align-items:flex-start;justify-content:center;overflow:hidden;border-left:6px solid var(--color-accent-primary)}
.section-stage{position:relative;z-index:2;display:flex;flex-direction:column;align-items:flex-start;max-width:80%}
.section-num{font-family:var(--mono);font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-accent-primary);letter-spacing:.08em;font-variant-numeric:tabular-nums;margin-bottom:8px}
.section-tag{font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.08em;font-family:var(--mono);margin-bottom:clamp(20px,2.4cqb,32px);font-variant-numeric:tabular-nums;padding-top:8px;border-top:1px solid var(--color-text-primary)}
.section-h2{font-size:var(--fs-4xl);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.14;letter-spacing:-.008em;margin-bottom:clamp(20px,2.4cqb,32px);word-break:keep-all;overflow-wrap:break-word}
.section-accent{width:clamp(40px,4.5cqi,56px);height:2px;border-radius:0;background:var(--color-accent-primary);margin-bottom:clamp(22px,2.8cqb,36px);flex-shrink:0}
.section-sub{font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--color-text-secondary);max-width:var(--measure-wide);line-height:1.6;word-break:keep-all;overflow-wrap:break-word;letter-spacing:0}

/* Bullets — P0-3 위계 강화 */
.bullet-list{list-style:none;display:flex;flex-direction:column;gap:clamp(20px,2.6cqb,36px);width:100%;counter-reset:bullet}
.bi{display:flex;align-items:flex-start;gap:clamp(20px,2.4cqi,36px);padding:0;background:transparent;border:none;border-radius:0;position:relative;overflow:hidden;counter-increment:bullet}
.bi-dot{width:auto;height:auto;border-radius:0;flex-shrink:0;background:transparent;color:var(--color-accent-primary);display:flex;align-items:flex-start;justify-content:center;font-size:var(--fs-md);font-weight:var(--fw-bold);font-family:var(--mono);letter-spacing:0;padding-top:.1em;min-width:42px;font-variant-numeric:tabular-nums}
.bi-dot::before{content:counter(bullet,decimal-leading-zero)}
.bi-body{flex:1;min-width:0;padding-bottom:0;max-width:var(--measure-wide)}
.bi-heading{display:block;font-size:var(--fs-lg);font-weight:var(--fw-bold);color:var(--color-text-primary);margin-bottom:10px;line-height:1.35;letter-spacing:-.005em;word-break:keep-all;overflow-wrap:break-word}
.bi-text{font-size:var(--fs-md);font-weight:var(--fw-normal);color:var(--color-text-primary);line-height:1.6;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}
.bi-subs{list-style:none;margin-top:10px;display:flex;flex-direction:column;gap:8px}
.bi-subs li{font-size:var(--fs-base);font-weight:var(--fw-normal);color:var(--color-text-secondary);padding-left:18px;position:relative;line-height:1.6;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}
.bi-subs li::before{content:'';position:absolute;left:0;top:.7em;width:10px;height:1px;background:var(--color-text-disabled)}

/* Flow — P0-1: 실제 색상 차등 + P0-3: 위계 강화 */
.flow-row{flex:1;min-height:0;display:flex;align-items:stretch;width:100%;gap:clamp(12px,1.4cqi,20px)}
.flow-card{flex:1;background:var(--color-surface-elevated);border-radius:0;padding:clamp(22px,2.4cqi,32px) clamp(22px,2.2cqi,28px);position:relative;overflow:hidden;display:flex;flex-direction:column;gap:clamp(14px,1.6cqb,20px);border:1px solid var(--color-border-subtle);border-top:3px solid var(--color-accent-primary);box-shadow:var(--shadow-card);transition:transform .15s ease-out}
.flow-card:hover{transform:translateY(-2px)}
.fc-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.fc-step{font-size:var(--fs-sm);font-weight:var(--fw-bold);font-family:var(--mono);color:var(--color-accent-primary);letter-spacing:.06em;font-variant-numeric:tabular-nums}
.fc-b{border-top-color:var(--color-accent-info)}
.fc-b .fc-step,.fc-b .fc-icon{color:var(--color-accent-info)}
.fc-g{border-top-color:var(--color-accent-success)}
.fc-g .fc-step,.fc-g .fc-icon{color:var(--color-accent-success)}
.fc-y{border-top-color:var(--color-accent-warning)}
.fc-y .fc-step,.fc-y .fc-icon{color:var(--color-accent-warning)}
.fc-p{border-top-color:var(--color-accent-purple)}
.fc-p .fc-step,.fc-p .fc-icon{color:var(--color-accent-purple)}
.fc-r{border-top-color:var(--color-accent-danger)}
.fc-r .fc-step,.fc-r .fc-icon{color:var(--color-accent-danger)}
.fc-c{border-top-color:var(--color-accent-cyan)}
.fc-c .fc-step,.fc-c .fc-icon{color:var(--color-accent-cyan)}
.fc-icon{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;color:var(--color-accent-primary);flex-shrink:0}
.fc-heading{font-size:var(--fs-lg);font-weight:var(--fw-bold);color:var(--color-text-primary);letter-spacing:-.005em;line-height:1.35;word-break:keep-all;overflow-wrap:break-word}
.fc-text{font-size:var(--fs-base);font-weight:var(--fw-normal);color:var(--color-text-secondary);line-height:1.6;flex:1;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}
.flow-arr{display:flex;align-items:center;justify-content:center;padding:0;color:var(--color-text-disabled);flex-shrink:0;align-self:center;width:clamp(20px,2cqi,28px)}

/* Two-column / panel — P0-1: 실제 색상 차등 */
.panels-row{flex:1;min-height:0;display:flex;gap:clamp(20px,2.4cqi,32px);align-items:stretch;width:100%}
.panel{flex:1;background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-top:3px solid var(--color-accent-primary);border-radius:0;overflow:hidden;display:flex;flex-direction:column;padding:clamp(20px,2.2cqb,28px) clamp(22px,2.2cqi,28px);min-width:0;box-shadow:var(--shadow-card)}
.panel-hdr{padding:0 0 clamp(14px,1.7cqb,20px) 0;margin-bottom:clamp(10px,1.2cqb,14px);display:flex;align-items:center;gap:12px;flex-shrink:0;background:transparent;border-bottom:1px solid var(--color-border-subtle)}
.ph-icon{display:inline-flex;width:28px;height:28px;border-radius:0;align-items:center;justify-content:center;background:transparent;flex-shrink:0;color:var(--color-accent-primary)}
.panel-b{border-top-color:var(--color-accent-info)}
.panel-b .ph-icon{color:var(--color-accent-info)}
.panel-p{border-top-color:var(--color-accent-purple)}
.panel-p .ph-icon{color:var(--color-accent-purple)}
.panel-g{border-top-color:var(--color-accent-success)}
.panel-g .ph-icon{color:var(--color-accent-success)}
.panel-y{border-top-color:var(--color-accent-warning)}
.panel-y .ph-icon{color:var(--color-accent-warning)}
.ph-name{font-size:var(--fs-lg);font-weight:var(--fw-bold);color:var(--color-text-primary);letter-spacing:-.005em;word-break:keep-all;overflow-wrap:break-word}
.panel-body{flex:1;overflow:hidden}
.panel-rows{flex:1;display:flex;flex-direction:column;justify-content:flex-start;overflow:hidden}
.pr{display:flex;align-items:flex-start;padding:clamp(11px,1.4cqb,16px) 0;border-bottom:1px solid var(--color-border-subtle);gap:20px;flex:0 0 auto;min-height:0}
.pr:last-child{border-bottom:none}
.pr-k{min-width:96px;max-width:32%;font-size:var(--fs-sm);color:var(--color-text-tertiary);font-weight:var(--fw-medium);flex-shrink:0;letter-spacing:0;padding-top:2px;line-height:1.5;word-break:keep-all;overflow-wrap:break-word}
.pr-v{flex:1;font-size:var(--fs-md);font-weight:var(--fw-medium);color:var(--color-text-primary);line-height:1.5;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word;align-self:center}
.panel-items{list-style:none;padding:0;display:flex;flex-direction:column;gap:clamp(10px,1.2cqb,16px)}
.panel-items li{font-size:var(--fs-md);font-weight:var(--fw-normal);color:var(--color-text-primary);padding-left:20px;position:relative;line-height:1.55;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}
.panel-items li::before{content:'';position:absolute;left:0;top:.7em;width:10px;height:1.5px;background:var(--color-accent-primary)}
.panel-b .panel-items li::before{background:var(--color-accent-info)}
.panel-p .panel-items li::before{background:var(--color-accent-purple)}
.panel-g .panel-items li::before{background:var(--color-accent-success)}
.panel-y .panel-items li::before{background:var(--color-accent-warning)}
.panel-note{margin:clamp(16px,1.8cqb,22px) 0 0 0;padding:clamp(12px,1.4cqb,16px) 0 0 0;background:transparent;border-radius:0;border-top:1px solid var(--color-border-subtle);font-size:var(--fs-sm);font-weight:var(--fw-normal);color:var(--color-text-tertiary);flex-shrink:0;letter-spacing:0;line-height:1.55;word-break:keep-all;overflow-wrap:break-word}

/* Image */
.img-body{flex:1;display:flex;flex-direction:column;gap:7px;min-height:0;overflow:hidden}
.img-body-full{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;gap:7px}
.slide-img{max-width:100%;max-height:100%;object-fit:contain;flex:1;min-height:0;border-radius:4px}
.img-ph{background:var(--color-surface-elevated);border:2px dashed var(--color-border-default);border-radius:6px;flex:1;display:flex;align-items:center;justify-content:center;color:var(--color-text-tertiary);font-size:var(--fs-sm)}
.img-cap{font-size:var(--fs-xs);color:var(--color-text-tertiary);text-align:center;font-style:italic}

/* Quote */
.s-quote{justify-content:center;overflow:hidden;background:var(--color-surface-default)}
.q-mark{display:none}
.q-text{font-size:var(--fs-xl);font-weight:var(--fw-normal);color:var(--color-text-primary);line-height:1.5;margin-bottom:24px;letter-spacing:-.005em;border-left:2px solid var(--color-accent-primary);padding-left:28px;position:relative;z-index:1;word-break:keep-all;overflow-wrap:break-word;max-width:var(--measure-wide)}
.q-attr{font-size:var(--fs-sm);font-weight:var(--fw-medium);color:var(--color-text-tertiary);padding-left:30px;letter-spacing:.04em;position:relative;z-index:1}

/* Table — P1-8: 숫자 컬럼 우측 정렬 + tabular-nums */
.tbl-body{justify-content:flex-start !important;overflow:auto}
.data-tbl{width:100%;border-collapse:collapse;border-top:1px solid var(--color-border-ink)}
.data-tbl th{background:transparent;color:var(--color-text-tertiary);padding:clamp(14px,1.7cqb,20px) clamp(14px,1.5cqi,20px);text-align:left;font-weight:var(--fw-medium);font-size:var(--fs-xs);letter-spacing:.04em;border-bottom:1px solid var(--color-border-ink);vertical-align:bottom;line-height:1.4}
.data-tbl th:first-child{padding-left:0}
.data-tbl th:last-child{padding-right:0}
.data-tbl th.num-col{text-align:right}
.data-tbl td{padding:clamp(14px,1.7cqb,22px) clamp(14px,1.5cqi,20px);font-weight:var(--fw-normal);color:var(--color-text-primary);border-bottom:1px solid var(--color-border-subtle);font-size:var(--fs-md);line-height:1.55;letter-spacing:0;vertical-align:top;word-break:keep-all;overflow-wrap:break-word}
.data-tbl td:first-child{padding-left:0;font-weight:var(--fw-medium);color:var(--color-text-primary)}
.data-tbl td:last-child{padding-right:0}
.data-tbl td.num-col{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:0}
.data-tbl tbody tr:hover td{background:var(--color-surface-elevated)}
.data-tbl tbody tr:last-child td{border-bottom:1px solid var(--color-border-ink)}

/* Closing */
.s-closing{background:var(--color-surface-default);align-items:center;justify-content:center;overflow:hidden}
.closing-body{text-align:center;position:relative;z-index:1;padding:0 clamp(20px,3cqi,40px);max-width:80%}
.closing-h{font-size:var(--fs-4xl);font-weight:var(--fw-bold);color:var(--color-text-primary);margin-bottom:clamp(20px,2.5cqb,30px);letter-spacing:-.01em;line-height:1.18;word-break:keep-all;overflow-wrap:break-word}
.closing-h::after{content:'';display:block;width:clamp(40px,4.5cqi,56px);height:2px;background:var(--color-accent-primary);border-radius:0;margin:clamp(20px,2.5cqb,30px) auto 0}
.closing-sub{font-size:var(--fs-md);font-weight:var(--fw-normal);color:var(--color-text-secondary);line-height:1.6;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}
.closing-bar{display:none}

/* Callout — P1-3 강조 강화 */
.s-callout{background:var(--color-surface-default);align-items:center;justify-content:center;overflow:hidden}
.callout-body{max-width:84%;text-align:center;position:relative;z-index:1;padding:0 clamp(20px,3cqi,40px);display:flex;flex-direction:column;align-items:center;gap:clamp(20px,2.4cqb,32px)}
.callout-lbl{display:inline-block;font-size:var(--fs-2xs);font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.12em;color:var(--color-accent-primary);font-family:var(--mono);padding:0;background:transparent;border-radius:0}
.callout-rule{width:clamp(60px,8cqi,100px);height:1px;background:var(--color-border-default)}
.callout-text{font-size:var(--fs-3xl);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.3;letter-spacing:-.01em;word-break:keep-all;overflow-wrap:break-word;max-width:var(--measure-wide)}

/* Metric — P0-5 신규 */
.metric-row{flex:1;min-height:0;display:grid;gap:clamp(16px,1.8cqi,28px);align-items:stretch;width:100%}
.metric-grid-1{grid-template-columns:1fr}
.metric-grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.metric-grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.metric-grid-4{grid-template-columns:repeat(4,minmax(0,1fr))}
@container stage (max-width:600px){
  .metric-grid-3,.metric-grid-4{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@container stage (max-width:380px){
  .metric-grid-2,.metric-grid-3,.metric-grid-4{grid-template-columns:1fr}
  .flow-row{flex-direction:column}
  .flow-arr{transform:rotate(90deg);width:auto;height:clamp(16px,2cqi,24px)}
  .panels-row{flex-direction:column}
}
.metric-card{background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-top:3px solid var(--color-accent-primary);padding:clamp(24px,2.6cqi,40px);display:flex;flex-direction:column;gap:clamp(10px,1.4cqb,16px);box-shadow:var(--shadow-card);overflow:hidden}
.metric-label{font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-text-tertiary);text-transform:uppercase;letter-spacing:.08em;font-family:var(--mono);word-break:keep-all}
.metric-value{font-family:var(--mono);font-size:var(--fs-metric-m);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.05;letter-spacing:-.02em;font-variant-numeric:tabular-nums;display:flex;align-items:baseline;gap:clamp(8px,1cqi,14px);flex-wrap:wrap;word-break:break-word;overflow-wrap:break-word;min-width:0}
.metric-grid-1 .metric-value{font-size:var(--fs-metric-l)}
.metric-delta{font-family:var(--mono);font-size:var(--fs-md);font-weight:var(--fw-bold);letter-spacing:0;font-variant-numeric:tabular-nums}
.metric-delta-up{color:var(--color-accent-success)}
.metric-delta-down{color:var(--color-accent-danger)}
.metric-delta-neutral{color:var(--color-text-tertiary)}
.metric-caption{font-size:var(--fs-sm);font-weight:var(--fw-normal);color:var(--color-text-secondary);line-height:1.55;word-break:keep-all;overflow-wrap:break-word}
.s-metric-hero{align-items:center;justify-content:center}
.metric-hero{display:flex;flex-direction:column;align-items:center;gap:clamp(16px,2cqb,24px);text-align:center}
.metric-hero .metric-card{background:transparent;border:none;border-top:none;box-shadow:none;align-items:center;text-align:center;padding:0}
.metric-hero .metric-value{font-size:var(--fs-display);justify-content:center}
.metric-hero .metric-label{font-size:var(--fs-sm);letter-spacing:.12em}

/* Agenda — P3-2 신규 */
.agenda-list{list-style:none;display:flex;flex-direction:column;gap:clamp(8px,1.2cqb,16px);width:100%;counter-reset:none;min-height:0;overflow:hidden}
.ag-item{display:flex;align-items:flex-start;gap:clamp(16px,2cqi,32px);padding:clamp(6px,.8cqb,10px) 0;border-bottom:1px solid var(--color-border-subtle);min-width:0}
.ag-item:last-child{border-bottom:none}
.ag-num{font-family:var(--mono);font-size:var(--fs-md);font-weight:var(--fw-bold);color:var(--color-accent-primary);letter-spacing:.04em;font-variant-numeric:tabular-nums;min-width:42px;flex-shrink:0;padding-top:.15em}
.ag-body{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.ag-heading{font-size:var(--fs-md);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.3;letter-spacing:-.005em;word-break:keep-all;overflow-wrap:break-word}
.ag-sub{font-size:var(--fs-sm);font-weight:var(--fw-normal);color:var(--color-text-tertiary);line-height:1.45;letter-spacing:0;word-break:keep-all;overflow-wrap:break-word}

/* Toolbar (PDF/Theme/Handout) */
.toolbar{position:fixed;top:14px;right:16px;z-index:200;display:flex;align-items:center;gap:6px}
.tool-btn{display:flex;align-items:center;gap:6px;padding:7px 12px;background:var(--color-surface-default);color:var(--color-text-secondary);border:1px solid var(--color-border-subtle);border-radius:2px;font-size:var(--fs-xs);font-weight:var(--fw-medium);cursor:pointer;transition:background .15s,color .15s,border-color .15s;font-family:var(--font);letter-spacing:0}
.tool-btn:hover{background:var(--color-accent-primary);color:#fff;border-color:var(--color-accent-primary)}
.tool-btn:focus-visible{outline:2px solid var(--color-accent-primary);outline-offset:2px}
.tool-btn svg{width:14px;height:14px}
.dl-btn{display:flex;align-items:center;gap:6px}

/* Navigation */
.nav{display:flex;align-items:center;justify-content:space-between;height:44px;padding:0 4px;gap:12px;background:transparent;border:none}
.nav-prev,.nav-next{font-size:var(--fs-2xs);font-weight:var(--fw-medium);color:var(--color-text-secondary);cursor:pointer;padding:8px 14px;background:transparent;border:1px solid var(--color-border-subtle);border-radius:2px;font-family:var(--mono);letter-spacing:.06em;transition:background .15s,color .15s,border-color .15s;flex-shrink:0;white-space:nowrap}
.nav-prev:hover,.nav-next:hover{background:var(--color-text-primary);color:var(--color-surface-default);border-color:var(--color-text-primary)}
.nav-prev:focus-visible,.nav-next:focus-visible{outline:2px solid var(--color-accent-primary);outline-offset:2px}
.nav-prev:disabled,.nav-next:disabled{opacity:.25;cursor:default;border-color:var(--color-border-subtle);color:var(--color-text-disabled)}
.counter{font-size:var(--fs-sm);font-weight:var(--fw-medium);color:var(--color-text-tertiary);font-family:var(--mono);min-width:60px;text-align:center;letter-spacing:.06em;font-variant-numeric:tabular-nums}
.counter b{color:var(--color-text-primary);font-weight:var(--fw-bold);margin-right:1px}
.counter .sep{color:var(--color-text-disabled);margin:0 4px}

/* Overview mode (P3-1) */
.overview-overlay{position:fixed;inset:0;z-index:300;background:var(--color-bg-default);padding:clamp(48px,5cqb,72px) clamp(32px,4cqi,64px) 32px;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:clamp(14px,1.6cqi,22px);align-content:start}
.overview-overlay::before{content:'OVERVIEW · ESC 또는 O 로 닫기';position:fixed;top:14px;left:16px;font-family:var(--mono);font-size:var(--fs-xs);font-weight:var(--fw-bold);color:var(--color-text-tertiary);letter-spacing:.08em;z-index:301}
.ov-card{background:var(--color-surface-default);border:1px solid var(--color-border-subtle);padding:clamp(16px,1.6cqi,22px);cursor:pointer;text-align:left;font-family:var(--font);display:flex;flex-direction:column;gap:8px;aspect-ratio:16/9;justify-content:flex-end;transition:transform .15s,outline .15s;box-shadow:var(--shadow-card)}
.ov-card:hover{outline:2px solid var(--color-accent-primary);transform:translateY(-2px)}
.ov-card:focus-visible{outline:2px solid var(--color-accent-primary);outline-offset:2px}
.ov-card.current{outline:2px solid var(--color-accent-primary)}
.ov-num{font-family:var(--mono);font-size:var(--fs-xs);color:var(--color-text-tertiary);letter-spacing:.06em;font-variant-numeric:tabular-nums}
.ov-title{font-size:var(--fs-md);font-weight:var(--fw-bold);color:var(--color-text-primary);line-height:1.35;word-break:keep-all;overflow-wrap:break-word;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.ov-type{font-family:var(--mono);font-size:10px;color:var(--color-text-disabled);letter-spacing:.06em;text-transform:uppercase}

/* Blackout/whiteout (P3-1) */
body.blackout::after,body.whiteout::after{content:'';position:fixed;inset:0;z-index:400;pointer-events:none}
body.blackout::after{background:#000}
body.whiteout::after{background:#fff}

/* Print / PDF — strict 1 슬라이드 = 1 페이지 (16:9 가로 A4) */
@media print{
  @page{size:297mm 167mm;margin:0}
  *{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}
  html,body{background:#FFFFFF !important;overflow:visible !important;width:297mm !important;height:auto !important;margin:0 !important;padding:0 !important}
  .pres{display:block !important;background:#FFFFFF !important;padding:0 !important;margin:0 !important;width:297mm !important;min-height:0 !important;gap:0 !important}
  .deck{display:block !important;width:297mm !important;max-width:297mm !important;margin:0 !important;padding:0 !important;gap:0 !important}
  .stage{position:static !important;width:297mm !important;height:auto !important;box-shadow:none !important;overflow:visible !important;border:none !important;border-radius:0 !important;aspect-ratio:auto !important;container-type:size !important;contain:none !important}
  .stage::after{display:none !important}
  .slide{
    display:flex !important;position:relative !important;
    width:297mm !important;height:167mm !important;
    aspect-ratio:auto !important;
    overflow:hidden !important;
    page-break-after:always !important;break-after:page !important;
    page-break-inside:avoid !important;break-inside:avoid !important;
    margin:0 !important;
    box-sizing:border-box !important
  }
  .slide:last-of-type{page-break-after:auto !important;break-after:auto !important}
  .slide-main{overflow:hidden !important;justify-content:flex-start !important}
  .toolbar,.nav,.prog,.overview-overlay{display:none !important}
  @keyframes fadein{from{opacity:1;transform:none}to{opacity:1;transform:none}}
}

/* === Responsive — true mobile-first structure === */

/* Tablet (720–1023px): 16:9 deck 유지, chrome 컴팩트 */
@media (max-width:1023px) and (min-width:721px){
  .pres{padding:54px 8px 8px}
  .deck{width:min(calc((100vh - 110px) * 16/9),calc(100vw - 16px))}
  .toolbar{padding:6px 10px;gap:6px}
  .tool-btn{padding:6px 10px;font-size:11px}
  .overview-overlay{padding:60px 24px 24px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
}

/* Mobile (≤720px): 16:9 해제, 콘텐츠가 세로로 자연스럽게 흐름 */
@media (max-width:720px){
  html,body{overflow-y:auto;height:auto;min-height:100vh}
  .pres{width:100%;min-height:100vh;padding:0;gap:0;justify-content:flex-start;padding-bottom:56px}
  .deck{width:100% !important;max-width:100% !important;gap:0 !important}
  .stage{
    aspect-ratio:auto !important;
    width:100% !important;
    min-height:calc(100svh - 56px - 50px); /* nav + toolbar */
    height:auto !important;
    border-radius:0 !important;
    box-shadow:none !important;
    container-type:inline-size !important
  }
  .slide{
    position:relative !important;inset:auto !important;
    width:100% !important;height:auto !important;
    min-height:calc(100svh - 56px - 50px);
    padding:clamp(20px,5cqi,32px) clamp(16px,4cqi,24px) !important;
    overflow:visible !important;
    padding-bottom:clamp(28px,6cqi,40px) !important
  }
  .slide:not(.active){display:none !important}
  .slide.active{display:flex !important;animation:none}

  /* Toolbar — 상단 고정, 컴팩트 */
  .toolbar{
    position:sticky;top:0;left:0;right:0;
    width:100%;padding:8px 12px;gap:6px;
    background:var(--color-bg-default);
    border-bottom:1px solid var(--color-border-subtle);
    z-index:100;justify-content:flex-end
  }
  .theme-label{display:none}
  .tool-btn{padding:8px 10px;font-size:11px}
  .tool-btn .theme-label{display:none}

  /* Nav — 하단 고정 */
  .nav{
    position:fixed;bottom:0;left:0;right:0;
    height:56px;padding:0 16px;gap:8px;margin:0;
    background:var(--color-surface-default);
    border-top:1px solid var(--color-border-subtle);
    z-index:99
  }
  .nav-prev,.nav-next{padding:10px 14px;font-size:11px;flex:1;max-width:120px}
  .counter{min-width:56px;font-size:12px}

  /* 가로 스택 → 세로 스택 */
  .panels-row{flex-direction:column;gap:14px}
  .flow-row{flex-direction:column;gap:10px}
  .flow-arr{transform:rotate(90deg);width:auto;height:20px;align-self:center;padding:2px 0}
  .metric-grid-3,.metric-grid-4{grid-template-columns:repeat(2,minmax(0,1fr))}

  /* 테이블 가로 스크롤 허용 */
  .tbl-body{overflow-x:auto !important;-webkit-overflow-scrolling:touch}
  .data-tbl{min-width:520px}

  /* 폰트는 viewport 기반으로 fallback (mobile에서는 슬라이드가 거의 viewport 폭) */
  .slide{font-size:15px}

  /* Title / closing 모바일 패딩 */
  .title-top{padding-top:24px}
  .title-bot{padding-bottom:8px;padding-top:16px;margin-top:16px}

  /* Quote / callout */
  .q-text,.callout-text{max-width:100%}
  .callout-body{max-width:100%;padding:0 4px}

  /* Section */
  .s-section{border-left-width:4px}
  .section-stage{max-width:100%}

  /* Bullets / agenda 컴팩트 */
  .bullet-list{gap:18px}
  .bi-body{max-width:100%}
  .agenda-list{gap:14px}

  /* Image */
  .img-body-full{padding:12px}

  /* Banner */
  .sbanner{margin:calc(-1*var(--sp-v)) calc(-1*var(--sp-h)) 12px;padding:8px clamp(16px,4cqi,24px)}

  /* Overview */
  .overview-overlay{padding:60px 12px 16px;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
  .overview-overlay::before{top:8px;left:12px;font-size:10px}
}

@media (max-width:480px){
  .metric-grid-2,.metric-grid-3,.metric-grid-4{grid-template-columns:1fr}
  .nav-prev,.nav-next{font-size:10px;padding:8px 10px}
  .data-tbl{min-width:380px}
}

/* 가로형 모바일 (예: 가로 660 × 세로 360) — landscape 모드 */
@media (max-width:960px) and (max-height:480px) and (orientation:landscape){
  .pres{padding:40px 8px 8px}
  .deck{width:min(calc((100vh - 90px) * 16/9),calc(100vw - 16px))}
  .stage{aspect-ratio:16/9 !important;container-type:size !important;min-height:0 !important;height:auto !important}
  .slide{position:absolute !important;inset:0 !important;min-height:0 !important;overflow:hidden !important;padding:var(--sp-v) var(--sp-h) !important}
  .slide:not(.active){display:none !important}
  .nav{position:relative;bottom:auto;height:36px}
  .pres{padding-bottom:8px}
}
"""

# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

JS = """\
(function(){
  const slides=document.querySelectorAll('.slide');
  const counter=document.querySelector('.counter');
  const prev=document.querySelector('.nav-prev');
  const next=document.querySelector('.nav-next');
  const prog=document.getElementById('prog');
  const themeBtn=document.querySelector('.theme-btn');
  const total=slides.length;
  let cur=0;
  let overlay=null;

  function go(n){
    slides[cur].classList.remove('active');
    cur=Math.max(0,Math.min(n,total-1));
    slides[cur].classList.add('active');
    counter.innerHTML='<b>'+String(cur+1).padStart(2,'0')+'</b><span class="sep">/</span>'+String(total).padStart(2,'0');
    prev.disabled=cur===0;
    next.disabled=cur===total-1;
    if(prog) prog.style.width=((cur+1)/total*100)+'%';
    history.replaceState(null,'','#/'+(cur+1));
    if(overlay){
      overlay.querySelectorAll('.ov-card').forEach((c,i)=>c.classList.toggle('current',i===cur));
    }
  }
  prev.addEventListener('click',()=>go(cur-1));
  next.addEventListener('click',()=>go(cur+1));

  /* === Overview / Grid mode === */
  function slideTitle(sl){
    const h=sl.querySelector('.title-h1, .section-h2, .slide-h2, .closing-h, .callout-text, .ph-name, .metric-value, .ag-heading, .q-text');
    return h ? h.textContent.trim() : '(슬라이드)';
  }
  function slideType(sl){
    const m=sl.className.match(/s-(\\w+)/);
    return m ? m[1] : '';
  }
  function showOverview(){
    if(overlay) return;
    overlay=document.createElement('div');
    overlay.className='overview-overlay';
    slides.forEach((sl,idx)=>{
      const card=document.createElement('button');
      card.className='ov-card'+(idx===cur?' current':'');
      card.type='button';
      card.innerHTML='<span class="ov-num">'+String(idx+1).padStart(2,'0')+'</span>'+
        '<span class="ov-title"></span>'+
        '<span class="ov-type">'+slideType(sl)+'</span>';
      card.querySelector('.ov-title').textContent=slideTitle(sl);
      card.addEventListener('click',()=>{hideOverview();go(idx);});
      overlay.appendChild(card);
    });
    document.body.appendChild(overlay);
  }
  function hideOverview(){
    if(!overlay) return;
    overlay.remove();
    overlay=null;
  }
  function toggleOverview(){overlay?hideOverview():showOverview();}

  /* === Blackout / Whiteout === */
  function setMask(c){
    document.body.classList.remove('blackout','whiteout');
    if(c) document.body.classList.add(c);
  }
  function toggleMask(c){
    if(document.body.classList.contains(c)) setMask(null);
    else setMask(c);
  }

  /* === Theme toggle (light / dark only) === */
  function applyTheme(t){
    const root=document.documentElement;
    root.setAttribute('data-theme',t);
    try{localStorage.setItem('theme',t);}catch(e){}
    if(themeBtn){
      themeBtn.querySelector('.theme-label').textContent=(t==='dark'?'다크':'라이트');
      themeBtn.setAttribute('aria-pressed',String(t==='dark'));
    }
  }
  let storedTheme=null;
  try{storedTheme=localStorage.getItem('theme');}catch(e){}
  if(storedTheme!=='light'&&storedTheme!=='dark'){
    storedTheme=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';
  }
  applyTheme(storedTheme);
  if(themeBtn){
    themeBtn.addEventListener('click',()=>{
      const cur=document.documentElement.getAttribute('data-theme')||'light';
      applyTheme(cur==='dark'?'light':'dark');
    });
  }

  /* === Keyboard === */
  document.addEventListener('keydown',e=>{
    if(e.target&&['INPUT','TEXTAREA'].includes(e.target.tagName)) return;
    if(e.key==='ArrowRight'||e.key===' '){e.preventDefault();go(cur+1);}
    else if(e.key==='ArrowLeft'){e.preventDefault();go(cur-1);}
    else if(e.key==='Home'){e.preventDefault();go(0);}
    else if(e.key==='End'){e.preventDefault();go(total-1);}
    else if(e.key==='Escape'||e.key==='o'||e.key==='O'){e.preventDefault();toggleOverview();}
    else if(e.key==='b'||e.key==='B'){e.preventDefault();toggleMask('blackout');}
    else if(e.key==='w'||e.key==='W'){e.preventDefault();toggleMask('whiteout');}
  });

  /* === URL hash sync === */
  function fromHash(){
    const m=location.hash.match(/^#\\/?(\\d+)/);
    return m?parseInt(m[1],10)-1:null;
  }
  window.addEventListener('hashchange',()=>{
    const n=fromHash();
    if(n!==null && n!==cur) go(n);
  });

  /* === Touch swipe (mobile) === */
  let tStartX=0,tStartY=0,tStartT=0;
  document.addEventListener('touchstart',e=>{
    if(overlay) return;
    if(e.target.closest('button,a,.tbl-body,.overview-overlay')) return;
    const t=e.changedTouches[0];
    tStartX=t.screenX;tStartY=t.screenY;tStartT=Date.now();
  },{passive:true});
  document.addEventListener('touchend',e=>{
    if(overlay) return;
    if(e.target.closest('button,a,.tbl-body,.overview-overlay')) return;
    const t=e.changedTouches[0];
    const dx=t.screenX-tStartX, dy=t.screenY-tStartY, dt=Date.now()-tStartT;
    if(dt>800) return;
    if(Math.abs(dx)>50 && Math.abs(dx)>Math.abs(dy)*1.6){
      if(dx<0) go(cur+1); else go(cur-1);
    }
  },{passive:true});

  window.downloadPDF=function(){window.print();};

  const initial=fromHash();
  go(initial!==null?initial:0);
})();
"""

# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------

_DL_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'
    "</svg>"
)
_SUN_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="4"/>'
    '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>'
    "</svg>"
)
_MOON_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
    "</svg>"
)

TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="toolbar">
  <button class="tool-btn theme-btn" type="button" title="라이트 / 다크 전환" aria-label="테마 전환">
    <span class="theme-icon theme-icon-sun" aria-hidden="true">{sun_icon}</span>
    <span class="theme-icon theme-icon-moon" aria-hidden="true">{moon_icon}</span>
    <span class="theme-label">테마</span>
  </button>
  <button class="tool-btn dl-btn" type="button" onclick="downloadPDF()" title="PDF 저장">{dl_icon} PDF 저장</button>
</div>
<div class="pres">
  <div class="deck">
    <div class="stage">
      <div class="prog" id="prog"></div>
{slides_html}
    </div>
    <nav class="nav">
      <button class="nav-prev" disabled>← 이전</button>
      <span class="counter"><b>01</b><span class="sep">/</span>{total_str}</span>
      <button class="nav-next">다음 →</button>
    </nav>
  </div>
</div>
<script>{js}</script>
</body>
</html>"""


def build_html(data: dict) -> str:
    meta       = data.get("meta", {})
    title      = meta.get("title", "Presentation")
    slide_list = data.get("slides", [])
    for i, s in enumerate(slide_list):
        _validate_slide(s, i)
    slides_html = "\n".join(
        render_slide_html(s, i) for i, s in enumerate(slide_list)
    )
    return TEMPLATE.format(
        title=esc(title), css=CSS,
        dl_icon=_DL_ICON, sun_icon=_SUN_ICON, moon_icon=_MOON_ICON,
        slides_html=slides_html,
        total=len(slide_list), total_str=str(len(slide_list)).zfill(2), js=JS,
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render(slides_json_path: str, output_dir: str) -> str:
    data    = json.loads(Path(slides_json_path).read_text(encoding="utf-8"))
    html    = build_html(data)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out     = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  ✓ HTML 저장: {out}")
    return str(out)


def main():
    parser = argparse.ArgumentParser(description="slides.json → HTML 프레젠테이션 렌더러")
    parser.add_argument("slides_json", help="슬라이드 구조 JSON 파일 경로")
    parser.add_argument("--output-dir", "-o", default=None)
    args = parser.parse_args()
    p = Path(args.slides_json)
    if not p.exists():
        print(f"ERROR: {args.slides_json} 파일이 없습니다.", file=sys.stderr)
        sys.exit(1)
    render(str(p), args.output_dir or str(p.parent))


if __name__ == "__main__":
    main()
