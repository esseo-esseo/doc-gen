#!/usr/bin/env python3
"""
render_html.py — slides.json → self-contained HTML presentation (light corporate theme)

Slide types: title, section, bullets, flow, two_column, image, quote, table, closing, callout

Any slide accepts optional fields:
  banner:  { text, level }  — top alert bar  (info / warning / error / success)
  label:   "CATEGORY · SUB" — small uppercase label above title
  summary: "text"           — bottom callout bar

Enhanced two_column fields:
  left/right.icon, left/right.color (blue|purple|green|yellow),
  left/right.rows [["label","value"],...], left/right.note

flow items: { heading, icon, text, color }
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

# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def _title(s: dict, i: int) -> str:
    title = esc(s.get("title", ""))
    sub   = esc(s.get("subtitle", ""))
    date  = esc(s.get("date", ""))
    return _wrap(
        _banner(s) + _label(s) +
        f'<div class="title-center">'
        f'<h1 class="title-h1">{title}</h1>'
        f'<div class="title-line"></div>' +
        (f'<p class="title-sub">{sub}</p>' if sub else "") +
        (f'<p class="title-date">{date}</p>' if date else "") +
        f'</div>' +
        _summary(s),
        i, "s-title",
    )

def _section(s: dict, i: int) -> str:
    num = str(i + 1).zfill(2)
    return _wrap(
        _banner(s) + _label(s) +
        f'<div class="section-num">{num}</div>' +
        f'<div class="section-accent"></div>'
        f'<h2 class="section-h2">{esc(s.get("title", ""))}</h2>' +
        (f'<p class="section-sub">{esc(s.get("subtitle",""))}</p>' if s.get("subtitle") else "") +
        _summary(s),
        i, "s-section",
    )

def _bullets(s: dict, i: int) -> str:
    return _wrap(
        _banner(s) + _label(s) +
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>' +
        f'<div class="slide-body">{_items_html(s.get("items", []))}</div>' +
        _summary(s),
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
        icon = f'<span class="fc-icon">{esc(item.get("icon",""))}</span>' if item.get("icon") else ""
        parts.append(
            f'<div class="flow-card {col}">'
            f'{icon}'
            f'<div class="fc-heading">{esc(item.get("heading",""))}</div>'
            f'<p class="fc-text">{esc(item.get("text",""))}</p>'
            f'</div>'
        )
    cards_html = '<div class="flow-arr">→</div>'.join(parts)
    return _wrap(
        _banner(s) + _label(s) +
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>' +
        f'<div class="flow-row">{cards_html}</div>' +
        _summary(s),
        i, "s-flow",
    )

def _two_column(s: dict, i: int) -> str:
    COLOR_MAP = {"blue": "panel-b", "purple": "panel-p", "green": "panel-g", "yellow": "panel-y"}
    DEFAULTS  = ["panel-b", "panel-p"]

    def panel(data: dict, idx: int) -> str:
        col   = COLOR_MAP.get(data.get("color", ""), DEFAULTS[idx % 2])
        icon  = f'<span class="ph-icon">{esc(data.get("icon",""))}</span>' if data.get("icon") else ""
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
        _banner(s) + _label(s) +
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>' +
        f'<div class="panels-row">{panel(left, 0)}{panel(right, 1)}</div>' +
        _summary(s),
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
    else:
        hdr  = ""
        body = f'<div class="img-body-full">{img}{cap}</div>'
    return _wrap(_banner(s) + hdr + body + _summary(s), i, "s-image")

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
    thead   = ""
    if headers:
        ths   = "".join(f"<th>{esc(h)}</th>" for h in headers)
        thead = f"<thead><tr>{ths}</tr></thead>"
    tbody   = ""
    if rows:
        trs   = "".join("<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>" for r in rows)
        tbody = f"<tbody>{trs}</tbody>"
    return _wrap(
        _banner(s) + _label(s) +
        f'<div class="slide-hdr"><h2 class="slide-h2">{esc(s.get("title",""))}</h2>{_accent()}</div>' +
        f'<div class="slide-body tbl-body"><table class="data-tbl">{thead}{tbody}</table></div>' +
        _summary(s),
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
        f'<p class="callout-text">{esc(s.get("title",""))}</p>'
        f'</div>',
        i, "s-callout",
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
}

def render_slide_html(slide: dict, index: int) -> str:
    fn = RENDERERS.get(slide.get("type", "bullets"), _bullets)
    return fn(slide, index)

# ---------------------------------------------------------------------------
# CSS — light corporate theme
# ---------------------------------------------------------------------------

CSS = """\
*{margin:0;padding:0;box-sizing:border-box}
:root{
  /* ── backgrounds ── */
  --bg:#FFFFFF;--sbg:#FFFFFF;
  --c1:#F7F8FA;--c2:#F0F2F5;--c3:#E9ECEF;
  /* ── borders ── */
  --bo:#DEE2E6;--bm:#CED4DA;--bl:#ADB5BD;
  /* ── brand: orange accent ── */
  --b:#F5A623;--p:#E07B00;--cy:#3AAFA9;
  --y:#F59E0B;--g:#22C55E;--r:#EF4444;
  /* ── text ── */
  --t1:#1A1E2A;--t2:#4A5568;--t3:#718096;--t4:#CBD5E0;
  --sp-v:clamp(20px,2.8vh,34px);--sp-h:clamp(26px,3.5vw,48px);
  /* ── type scale ── */
  --fs-2xs:clamp(8px,.65vw,10px);
  --fs-xs: clamp(9px,.78vw,11px);
  --fs-sm: clamp(11px,.95vw,13px);
  --fs-base:clamp(12px,1.1vw,14px);
  --fs-md: clamp(13px,1.25vw,16px);
  --fs-lg: clamp(15px,1.5vw,19px);
  --fs-xl: clamp(18px,1.9vw,24px);
  --fs-2xl:clamp(22px,2.4vw,30px);
  --fs-3xl:clamp(28px,3.3vw,44px);
  --fs-4xl:clamp(34px,4.4vw,56px);
  /* ── line heights ── */
  --lh-tight:1.18;--lh-snug:1.38;--lh-normal:1.6;--lh-relaxed:1.75;
  /* ── font weights ── */
  --fw-normal:400;--fw-medium:500;--fw-semi:600;--fw-bold:700;--fw-extra:800;--fw-black:900;
  /* ── fonts ── */
  --font:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',Pretendard,-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
  --mono:'Menlo','Consolas','Monaco','Courier New',monospace
}
html,body{width:100%;height:100%;background:#FFFFFF;font-family:var(--font);overflow:hidden;color:var(--t1);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}

/* ── layout ── */
.pres{width:100vw;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}
.deck{display:flex;flex-direction:column;gap:10px;width:min(calc((100vh - 72px) * 16/9),calc(100vw - 24px))}
.stage{
  position:relative;width:100%;aspect-ratio:16/9;
  background:var(--sbg);overflow:hidden;
  border-radius:2px;
  box-shadow:0 1px 12px rgba(0,0,0,.06)
}

/* ── progress bar ── */
.prog{position:absolute;top:0;left:0;height:2px;width:0;z-index:50;
  background:var(--b);transition:width .35s cubic-bezier(.4,0,.2,1)}

/* ── slide base ── */
.slide{
  position:absolute;inset:0;display:none;flex-direction:column;justify-content:center;
  padding:var(--sp-v) var(--sp-h);background:var(--sbg)
}
.slide.active{display:flex;animation:fadein .2s ease}
@keyframes fadein{from{opacity:0;transform:translateX(6px)}to{opacity:1;transform:translateX(0)}}

/* ── banner ── */
.sbanner{
  margin:calc(-1*var(--sp-v)) calc(-1*var(--sp-h)) 14px;
  padding:8px var(--sp-h);
  font-size:var(--fs-xs);font-family:var(--mono);letter-spacing:.04em;
  display:flex;align-items:center;flex-shrink:0;border-left:3px solid;gap:8px
}
.sb-info{background:rgba(245,166,35,.08);border-color:var(--b);color:#A07000}
.sb-warn{background:rgba(245,166,35,.12);border-color:var(--y);color:#92600A}
.sb-err{background:rgba(239,68,68,.07);border-color:var(--r);color:#DC2626}
.sb-ok{background:rgba(34,197,94,.07);border-color:var(--g);color:#15803D}

/* ── label / header / accent ── */
.slide-lbl{
  font-size:var(--fs-2xs);font-weight:var(--fw-bold);text-transform:uppercase;
  letter-spacing:3.5px;color:var(--b);margin-bottom:6px;flex-shrink:0
}
.slide-hdr{
  flex-shrink:0;margin-bottom:clamp(10px,1.3vh,16px);
  padding-bottom:clamp(8px,1vh,12px);border-bottom:2px solid var(--bo)
}
.slide-h2{
  font-size:var(--fs-xl);font-weight:var(--fw-bold);color:var(--t1);
  margin-bottom:8px;line-height:var(--lh-snug);letter-spacing:-.012em;text-align:center
}
.acc-bar{height:3px;width:clamp(32px,4vw,48px);border-radius:2px;background:var(--b)}
.slide-body{overflow:hidden;display:flex;flex-direction:column;justify-content:center;width:100%}

/* ── summary bar ── */
.slide-sum{
  flex-shrink:0;margin-top:10px;padding:9px 16px;
  background:rgba(245,166,35,.08);border:1px solid rgba(245,166,35,.3);
  border-radius:5px;font-size:var(--fs-sm);color:var(--t2);
  text-align:center;line-height:var(--lh-normal)
}

/* ── title ── */
.s-title{overflow:hidden}
.title-center{
  flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center
}
.s-title::before{
  content:'';position:absolute;bottom:-80px;right:-60px;
  width:clamp(200px,36vw,440px);height:clamp(200px,36vw,440px);
  background:radial-gradient(circle,rgba(245,166,35,.07),transparent 62%);pointer-events:none
}
.title-h1{
  font-size:var(--fs-4xl);font-weight:var(--fw-extra);color:var(--t1);
  line-height:var(--lh-tight);letter-spacing:-.025em;position:relative;z-index:1
}
.title-line{
  width:clamp(44px,5.5vw,70px);height:4px;flex-shrink:0;
  background:var(--b);border-radius:2px;margin:clamp(12px,1.6vh,18px) 0
}
.title-sub{
  font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--t2);
  line-height:var(--lh-relaxed);margin-bottom:clamp(14px,2vh,22px);
  max-width:78%;text-align:center;position:relative;z-index:1
}
.title-date{font-size:var(--fs-xs);font-weight:var(--fw-normal);color:var(--t3);font-family:var(--mono);letter-spacing:.06em}

/* ── section ── */
.s-section{
  background:var(--c1);align-items:center;justify-content:center;text-align:center;
  overflow:hidden
}
.s-section::before{
  content:'';position:absolute;inset:0;
  background-image:radial-gradient(var(--bo) 1px,transparent 1px);
  background-size:20px 20px;opacity:.7;pointer-events:none
}
.section-num{
  position:absolute;right:clamp(20px,3vw,44px);bottom:clamp(6px,1.2vh,14px);
  font-size:clamp(72px,11.5vw,140px);font-weight:var(--fw-black);color:var(--bo);
  font-family:var(--mono);line-height:1;user-select:none;letter-spacing:-.06em
}
.section-accent{
  width:clamp(36px,5vw,60px);height:4px;border-radius:2px;background:var(--b);
  margin-bottom:clamp(12px,1.6vh,18px);position:relative;z-index:1;flex-shrink:0
}
.section-h2{
  font-size:var(--fs-3xl);font-weight:var(--fw-extra);color:var(--t1);
  line-height:var(--lh-tight);letter-spacing:-.02em;margin-bottom:12px;position:relative;z-index:1
}
.section-sub{
  font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--t2);
  max-width:70%;text-align:center;line-height:var(--lh-relaxed);position:relative;z-index:1
}

/* ── bullets ── */
.bullet-list{list-style:none;display:flex;flex-direction:column;gap:clamp(5px,.55vh,8px)}
.bi{
  display:flex;align-items:flex-start;gap:12px;
  padding:clamp(10px,1.1vh,14px) clamp(14px,1.6vw,20px);
  background:var(--c1);border:1px solid var(--bo);border-radius:5px;
  position:relative;overflow:hidden
}
.bi-dot{width:6px;height:6px;border-radius:50%;margin-top:.62em;flex-shrink:0;background:var(--b)}
.bi-body{flex:1}
.bi-heading{display:block;font-size:var(--fs-md);font-weight:var(--fw-bold);color:var(--t1);margin-bottom:3px;line-height:var(--lh-snug)}
.bi-text{font-size:var(--fs-md);font-weight:var(--fw-medium);color:var(--t1);line-height:var(--lh-normal)}
.bi-subs{list-style:none;margin-top:5px;display:flex;flex-direction:column;gap:3px}
.bi-subs li{font-size:var(--fs-base);font-weight:var(--fw-normal);color:var(--t2);padding-left:12px;position:relative;line-height:var(--lh-normal)}
.bi-subs li::before{content:'';position:absolute;left:0;top:.62em;width:4px;height:4px;background:var(--t4);border-radius:50%}

/* ── flow ── */
.flow-row{height:clamp(140px,25vh,280px);display:flex;align-items:stretch;width:100%}
.flow-card{
  flex:1;background:var(--sbg);border-radius:6px;
  padding:clamp(12px,1.5vw,20px);position:relative;overflow:hidden;
  display:flex;flex-direction:column;gap:9px;border:1px solid var(--bo)
}
.flow-card::before{content:'';position:absolute;left:0;top:0;right:0;height:3px}
.fc-b::before{background:var(--b)}  .fc-b{border-color:rgba(245,166,35,.35)}
.fc-g::before{background:var(--g)}  .fc-g{border-color:rgba(34,197,94,.35)}
.fc-y::before{background:var(--y)}  .fc-y{border-color:rgba(245,158,11,.35)}
.fc-p::before{background:var(--p)}  .fc-p{border-color:rgba(224,123,0,.35)}
.fc-r::before{background:var(--r)}  .fc-r{border-color:rgba(239,68,68,.35)}
.fc-c::before{background:var(--cy)} .fc-c{border-color:rgba(58,175,169,.35)}
.fc-icon{font-size:var(--fs-xl);line-height:1}
.fc-heading{font-size:var(--fs-2xs);font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:1.8px;color:var(--t3)}
.fc-text{font-size:var(--fs-base);font-weight:var(--fw-normal);color:var(--t2);line-height:var(--lh-relaxed);flex:1}
.flow-arr{display:flex;align-items:center;justify-content:center;padding:0 clamp(4px,.6vw,10px);color:var(--bl);font-size:clamp(14px,1.8vw,22px);flex-shrink:0}

/* ── two column / panel ── */
.panels-row{height:clamp(140px,25vh,280px);display:flex;gap:clamp(10px,1.4vw,18px);align-items:stretch;width:100%}
.panel{flex:1;background:var(--sbg);border:1px solid var(--bm);border-radius:8px;overflow:hidden;display:flex;flex-direction:column}
.panel-hdr{
  padding:clamp(10px,1.1vh,14px) clamp(13px,1.5vw,18px);
  border-bottom:1px solid var(--bo);
  display:flex;align-items:center;gap:9px;flex-shrink:0;background:var(--c1)
}
.panel-b .panel-hdr{border-top:3px solid var(--b)} .panel-b .ph-name{color:var(--p)}
.panel-p .panel-hdr{border-top:3px solid var(--p)} .panel-p .ph-name{color:var(--p)}
.panel-g .panel-hdr{border-top:3px solid var(--g)} .panel-g .ph-name{color:var(--g)}
.panel-y .panel-hdr{border-top:3px solid var(--y)} .panel-y .ph-name{color:var(--y)}
.ph-icon{font-size:var(--fs-xl)}
.ph-name{font-size:var(--fs-lg);font-weight:var(--fw-bold);color:var(--t1)}
.panel-body{flex:1;overflow:auto}
.panel-rows{flex:1;overflow:auto}
.pr{display:flex;align-items:center;padding:clamp(7px,.85vh,10px) clamp(12px,1.5vw,18px);border-bottom:1px solid var(--bo);gap:12px}
.pr:nth-child(even){background:var(--c1)}
.pr-k{min-width:52px;max-width:84px;font-size:var(--fs-xs);color:var(--t3);font-weight:var(--fw-bold);flex-shrink:0;text-transform:uppercase;letter-spacing:.6px}
.pr-v{flex:1;font-size:var(--fs-md);font-weight:var(--fw-semi);color:var(--t1)}
.panel-items{list-style:none;padding:clamp(8px,1vh,12px) clamp(12px,1.5vw,16px);display:flex;flex-direction:column;gap:7px}
.panel-items li{font-size:var(--fs-md);font-weight:var(--fw-normal);color:var(--t2);padding-left:13px;position:relative;line-height:var(--lh-normal)}
.panel-items li::before{content:'';position:absolute;left:0;top:.62em;width:4px;height:4px;background:var(--t4);border-radius:50%}
.panel-note{
  margin:0 clamp(8px,1vw,14px) clamp(8px,1vh,12px);
  padding:clamp(6px,.7vh,8px) clamp(10px,1.2vw,14px);
  background:var(--c2);border-radius:4px;border-left:2px solid var(--bl);
  font-size:var(--fs-xs);font-weight:var(--fw-normal);color:var(--t3);font-family:var(--mono);flex-shrink:0
}

/* ── image ── */
.img-body{flex:1;display:flex;flex-direction:column;gap:7px;min-height:0;overflow:hidden}
.img-body-full{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;gap:7px}
.slide-img{max-width:100%;max-height:100%;object-fit:contain;flex:1;min-height:0;border-radius:4px}
.img-ph{
  background:var(--c1);border:2px dashed var(--bm);border-radius:6px;
  flex:1;display:flex;align-items:center;justify-content:center;
  color:var(--t3);font-size:var(--fs-sm)
}
.img-cap{font-size:var(--fs-xs);color:var(--t3);text-align:center;font-style:italic}

/* ── quote ── */
.s-quote{justify-content:center;overflow:hidden;background:var(--c1)}
.s-quote::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 25% 50%,rgba(245,166,35,.07),transparent 55%);
  pointer-events:none
}
.q-mark{
  font-size:clamp(56px,8vw,96px);color:rgba(245,166,35,.3);
  line-height:.8;margin-bottom:10px;font-family:Georgia,serif;
  font-weight:900;position:relative;z-index:1
}
.q-text{
  font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--t1);font-style:italic;
  line-height:var(--lh-relaxed);margin-bottom:18px;
  border-left:4px solid var(--b);padding-left:20px;position:relative;z-index:1
}
.q-attr{
  font-size:var(--fs-sm);font-weight:var(--fw-normal);color:var(--t3);
  padding-top:12px;border-top:1px solid var(--bo);position:relative;z-index:1
}

/* ── table ── */
.tbl-body{justify-content:flex-start !important;overflow:auto}
.data-tbl{width:100%;border-collapse:collapse;font-size:var(--fs-base)}
.data-tbl th{
  background:rgba(245,166,35,.1);color:var(--p);
  padding:clamp(8px,.9vh,11px) clamp(12px,1.3vw,18px);
  text-align:left;font-weight:var(--fw-bold);font-size:var(--fs-xs);
  text-transform:uppercase;letter-spacing:1.3px;
  border-bottom:2px solid var(--b)
}
.data-tbl td{
  padding:clamp(8px,.9vh,11px) clamp(12px,1.3vw,18px);
  font-weight:var(--fw-normal);color:var(--t2);border-bottom:1px solid var(--bo)
}
.data-tbl tbody tr:nth-child(even) td{background:var(--c1)}
.data-tbl tbody tr:hover td{background:rgba(245,166,35,.06);color:var(--t1)}

/* ── closing ── */
.s-closing{background:var(--c1);align-items:center;justify-content:center;overflow:hidden}
.s-closing::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 120%,rgba(245,166,35,.18),rgba(224,123,0,.06) 45%,transparent 65%);
  pointer-events:none
}
.s-closing::after{
  content:'';position:absolute;inset:0;
  background-image:radial-gradient(var(--bo) 1px,transparent 1px);
  background-size:20px 20px;opacity:.7;pointer-events:none
}
.closing-body{text-align:center;position:relative;z-index:1;padding:0 clamp(20px,3vw,40px)}
.closing-h{
  font-size:var(--fs-4xl);font-weight:var(--fw-extra);color:var(--t1);
  margin-bottom:12px;letter-spacing:-.025em;line-height:var(--lh-tight)
}
.closing-sub{font-size:var(--fs-lg);font-weight:var(--fw-normal);color:var(--t3);line-height:var(--lh-normal)}
.closing-bar{position:absolute;bottom:0;left:0;right:0;height:4px;background:var(--b);z-index:2}

/* ── callout ── */
.s-callout{background:var(--c1);align-items:center;justify-content:center;overflow:hidden}
.s-callout::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 50%,rgba(245,166,35,.08),transparent 55%);
  pointer-events:none
}
.callout-body{
  max-width:78%;text-align:center;
  padding:clamp(24px,3.5vw,42px) clamp(30px,4.5vw,52px);
  background:var(--sbg);border:2px solid var(--b);border-radius:10px;
  position:relative;z-index:1;box-shadow:0 4px 24px rgba(245,166,35,.12)
}
.callout-lbl{font-size:var(--fs-2xs);font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:3.5px;color:var(--b);margin-bottom:16px}
.callout-text{font-size:var(--fs-2xl);font-weight:var(--fw-semi);color:var(--t1);line-height:var(--lh-snug)}

/* ── download button ── */
.dl-btn{
  position:fixed;top:12px;right:14px;z-index:200;
  display:flex;align-items:center;gap:6px;
  padding:7px 15px;background:var(--sbg);color:var(--t2);
  border:1px solid var(--bm);border-radius:6px;
  font-size:var(--fs-xs);font-weight:var(--fw-semi);cursor:pointer;
  transition:all .15s;font-family:var(--font);letter-spacing:.02em
}
.dl-btn:hover{background:var(--b);color:#fff;border-color:var(--b)}
.dl-btn svg{width:12px;height:12px}

/* ── navigation ── */
.nav{
  display:flex;align-items:center;justify-content:space-between;
  height:44px;padding:0 4px;gap:12px;
  background:transparent;border:none
}
.nav-prev,.nav-next{
  font-size:var(--fs-xs);font-weight:var(--fw-semi);color:var(--t2);cursor:pointer;
  padding:5px 14px;background:var(--c1);border:1px solid var(--bo);border-radius:5px;
  font-family:var(--font);letter-spacing:.04em;transition:all .15s;flex-shrink:0;white-space:nowrap
}
.nav-prev:hover,.nav-next:hover{background:var(--b);color:#fff;border-color:var(--b)}
.nav-prev:disabled,.nav-next:disabled{opacity:.3;cursor:default}
.dots{display:flex;gap:5px;align-items:center}
.dot{
  width:8px;height:8px;border-radius:50%;background:var(--t4);
  cursor:pointer;transition:all .28s cubic-bezier(.4,0,.2,1)
}
.dot.active{width:26px;border-radius:5px;background:var(--b);box-shadow:0 0 10px rgba(245,166,35,.45)}
.dot:hover:not(.active){background:var(--bl);transform:scale(1.2)}
.counter{
  font-size:var(--fs-sm);font-weight:var(--fw-bold);color:var(--t2);
  font-family:var(--mono);min-width:46px;text-align:center
}

/* ── print / PDF ── */
@media print{
  @page{size:29.7cm 16.73cm;margin:0}
  *{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}
  html,body{background:#FFFFFF !important;overflow:visible !important;width:100% !important;height:auto !important}
  .pres{display:block !important;background:#FFFFFF !important}
  .deck{display:block !important;width:100% !important}
  .stage{position:static !important;width:100% !important;height:auto !important;box-shadow:none !important;overflow:visible !important;border:none !important;border-radius:0 !important}
  .stage::after{display:none !important}
  .slide{display:flex !important;position:relative !important;width:100% !important;aspect-ratio:16/9;height:auto !important;page-break-after:always !important;break-after:page !important}
  .dl-btn,.nav,.prog{display:none !important}
  @keyframes fadein{from{opacity:1;transform:none}to{opacity:1;transform:none}}
}
"""

# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

JS = """\
(function(){
  const slides=document.querySelectorAll('.slide');
  const dots=document.querySelectorAll('.dot');
  const counter=document.querySelector('.counter');
  const prev=document.querySelector('.nav-prev');
  const next=document.querySelector('.nav-next');
  const prog=document.getElementById('prog');
  const total=slides.length;
  let cur=0;
  function go(n){
    slides[cur].classList.remove('active');
    dots[cur].classList.remove('active');
    cur=Math.max(0,Math.min(n,total-1));
    slides[cur].classList.add('active');
    dots[cur].classList.add('active');
    counter.textContent=(cur+1)+' / '+total;
    prev.disabled=cur===0;
    next.disabled=cur===total-1;
    if(prog) prog.style.width=((cur+1)/total*100)+'%';
  }
  prev.addEventListener('click',()=>go(cur-1));
  next.addEventListener('click',()=>go(cur+1));
  dots.forEach((d,i)=>d.addEventListener('click',()=>go(i)));
  document.addEventListener('keydown',e=>{
    if(e.key==='ArrowRight'||e.key===' '){e.preventDefault();go(cur+1);}
    else if(e.key==='ArrowLeft'){e.preventDefault();go(cur-1);}
    else if(e.key==='Home'){e.preventDefault();go(0);}
    else if(e.key==='End'){e.preventDefault();go(total-1);}
  });
  window.downloadPDF=function(){window.print();};
  go(0);
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
<button class="dl-btn" onclick="downloadPDF()">{dl_icon} PDF 저장</button>
<div class="pres">
  <div class="deck">
    <div class="stage">
      <div class="prog" id="prog"></div>
{slides_html}
    </div>
    <nav class="nav">
      <button class="nav-prev" disabled>← 이전</button>
      <div class="dots">{dots_html}</div>
      <span class="counter">1 / {total}</span>
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
    slides_html = "\n".join(render_slide_html(s, i) for i, s in enumerate(slide_list))
    dots_html   = "".join(
        f'<div class="dot{" active" if i == 0 else ""}" title="{i + 1}"></div>'
        for i in range(len(slide_list))
    )
    return TEMPLATE.format(
        title=esc(title), css=CSS, dl_icon=_DL_ICON,
        slides_html=slides_html, dots_html=dots_html,
        total=len(slide_list), js=JS,
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
