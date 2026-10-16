#!/usr/bin/env python3
"""
Generates every SVG used by the profile README.

* 100% self-contained: no external fonts, scripts or images (GitHub blocks them in <img> SVGs).
* "3D" is done the way it can be done on GitHub: extruded type, isometric cubes,
  stacked slabs with depth, a perspective floor grid and gentle CSS motion.

Edit the copy at the bottom of the file, then run:  python3 build_assets.py
"""
import html
import math
import os
import random
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "tools" else HERE
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

SANS = "'Segoe UI', Inter, system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

# palette -----------------------------------------------------------------
VIOLET, CYAN, PINK = "#8b5cf6", "#22d3ee", "#f472b6"
GREEN, AMBER, TG, INDIGO = "#22c55e", "#f59e0b", "#26a5e4", "#6366f1"
INK, PANEL1, PANEL2 = "#0b1020", "#1a2142", "#0f1530"
MUTED, TEXT = "#94a3b8", "#e2e8f0"

BASE_CSS = """
text{font-family:@SANS@}
.m{font-family:@MONO@}
@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes tw{0%,100%{opacity:.12}50%{opacity:.95}}
@keyframes ring{0%{transform:scale(1);opacity:.8}100%{transform:scale(3.4);opacity:0}}
@keyframes sweep{0%{transform:translateX(-30%)}100%{transform:translateX(130%)}}
@keyframes grow{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}
@keyframes rise{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}
.fl{animation:fl 5.5s ease-in-out infinite}
.fl2{animation:fl 7s ease-in-out -2s infinite}
.fl3{animation:fl 4.6s ease-in-out -1s infinite}
.tw{animation:tw 3.4s ease-in-out infinite}
.pr{transform-box:fill-box;transform-origin:center;animation:ring 2.2s ease-out infinite}
.sw{animation:sweep 5s linear infinite}
.sw2{animation:sweep 4s linear infinite}
.rise{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}
.grow{transform-box:fill-box;transform-origin:left;animation:grow 2.2s .4s cubic-bezier(.2,.8,.2,1) both}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""".replace("@SANS@", SANS).replace("@MONO@", MONO)

FILTERS = "".join(
    f'<filter id="b{n}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{n}"/></filter>'
    for n in (4, 10, 18)
)

_uid = [0]


def uid(p="u"):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


# helpers -----------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=True)


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    return _hex([x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def dark(c, t):
    return mix(c, "#000000", t)


def light(c, t):
    return mix(c, "#ffffff", t)


def lg(id_, stops, x1=0, y1=0, x2=0, y2=1):
    s = ""
    for st in stops:
        o, c = st[0], st[1]
        op = f' stop-opacity="{st[2]}"' if len(st) > 2 else ""
        s += f'<stop offset="{o}" stop-color="{c}"{op}/>'
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def svg(w, h, title, body, defs="", css="", desc=None):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d">\n'
        f'<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc or title)}</desc>\n'
        f"<defs>{FILTERS}{defs}</defs>\n<style>{BASE_CSS}{css}</style>\n{body}\n</svg>\n"
    )


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {name:28s} {len(content) / 1024:6.1f} KB")


def star_pts(cx, cy, R, r, n=5):
    pts = []
    for i in range(n * 2):
        a = -math.pi / 2 + i * math.pi / n
        rad = R if i % 2 == 0 else r
        pts.append(f"{cx + rad * math.cos(a):.1f},{cy + rad * math.sin(a):.1f}")
    return " ".join(pts)


def shadow(cx, cy, rx, op=0.4):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx * 0.28:.1f}" fill="#000" opacity="{op}" filter="url(#b4)"/>'


# 3D primitives -----------------------------------------------------------
def glyph(name, accent):
    """Flat icons drawn in a 100x100 box; they get projected onto a cube's top face."""
    fg = "#ffffff"
    dk = dark(accent, 0.55)
    sw = 'stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    if name == "chat":
        return (
            f'<rect x="10" y="14" width="80" height="52" rx="15" fill="{fg}"/>'
            f'<path d="M28 64 L26 88 L54 64 Z" fill="{fg}"/>'
            + "".join(f'<circle cx="{x}" cy="40" r="6.5" fill="{dk}"/>' for x in (32, 50, 68))
        )
    if name == "radar":
        return (
            f'<circle cx="50" cy="50" r="40" {sw} opacity=".9"/>'
            f'<circle cx="50" cy="50" r="22" {sw} opacity=".7"/>'
            f'<path d="M50 50 L90 50 A40 40 0 0 0 78.3 21.7 Z" fill="{fg}" opacity=".5"/>'
            f'<line x1="50" y1="50" x2="78.3" y2="21.7" stroke="#fff" stroke-width="6" stroke-linecap="round"/>'
            f'<circle cx="32" cy="68" r="6" fill="{fg}"/>'
        )
    if name == "template":
        return (
            f'<rect x="8" y="14" width="84" height="72" rx="11" fill="{fg}"/>'
            f'<path d="M8 33 V25 a11 11 0 0 1 11 -11 H81 a11 11 0 0 1 11 11 V33 Z" fill="{accent}"/>'
            + "".join(f'<circle cx="{x}" cy="23.5" r="3.6" fill="#fff"/>' for x in (21, 32, 43))
            + f'<rect x="18" y="42" width="28" height="36" rx="5" fill="{accent}" opacity=".9"/>'
            f'<rect x="54" y="42" width="28" height="15" rx="5" fill="{accent}" opacity=".6"/>'
            f'<rect x="54" y="63" width="28" height="15" rx="5" fill="{accent}" opacity=".6"/>'
        )
    if name == "crescent":
        m = uid("m")
        return (
            f'<mask id="{m}"><rect width="100" height="100" fill="#fff"/><circle cx="64" cy="42" r="31" fill="#000"/></mask>'
            f'<circle cx="46" cy="54" r="37" fill="{fg}" mask="url(#{m})"/>'
            f'<polygon points="{star_pts(72, 36, 11, 4.6)}" fill="{fg}"/>'
        )
    if name == "wallet":
        return (
            f'<rect x="8" y="26" width="84" height="58" rx="13" fill="{fg}"/>'
            f'<path d="M16 26 L64 12 a6 6 0 0 1 8 6 V26 Z" fill="{light(accent, .5)}"/>'
            f'<rect x="56" y="43" width="36" height="24" rx="9" fill="{accent}"/>'
            f'<circle cx="70" cy="55" r="5.5" fill="{fg}"/>'
        )
    if name == "bot":
        return (
            f'<line x1="50" y1="30" x2="50" y2="15" stroke="#fff" stroke-width="6" stroke-linecap="round"/>'
            f'<circle cx="50" cy="12" r="6.5" fill="{fg}"/>'
            f'<rect x="16" y="30" width="68" height="54" rx="17" fill="{fg}"/>'
            f'<rect x="5" y="47" width="8" height="21" rx="4" fill="{fg}"/><rect x="87" y="47" width="8" height="21" rx="4" fill="{fg}"/>'
            f'<circle cx="36" cy="54" r="8" fill="{accent}"/><circle cx="64" cy="54" r="8" fill="{accent}"/>'
            f'<rect x="38" y="68" width="24" height="5" rx="2.5" fill="{dk}"/>'
        )
    if name == "chip":
        pin = 'stroke="#fff" stroke-width="5" stroke-linecap="round"'
        pins = ""
        for v in (38, 50, 62):
            pins += (f'<line x1="{v}" y1="12" x2="{v}" y2="28" {pin}/><line x1="{v}" y1="72" x2="{v}" y2="88" {pin}/>'
                     f'<line x1="12" y1="{v}" x2="28" y2="{v}" {pin}/><line x1="72" y1="{v}" x2="88" y2="{v}" {pin}/>')
        return (pins + f'<rect x="24" y="24" width="52" height="52" rx="10" fill="{fg}"/>'
                f'<text x="50" y="59" text-anchor="middle" font-size="26" font-weight="800" fill="{accent}">AI</text>')
    if name == "web":
        return (f'<polyline points="34,26 11,50 34,74" {sw}/><polyline points="66,26 89,50 66,74" {sw}/>'
                f'<line x1="57" y1="20" x2="43" y2="80" {sw}/>')
    if name == "offline":
        return (
            f'<rect x="27" y="7" width="46" height="86" rx="11" fill="{fg}"/>'
            f'<rect x="33" y="18" width="34" height="58" rx="4" fill="{dk}"/>'
            f'<circle cx="50" cy="85" r="3.2" fill="{dk}"/>'
            f'<path d="M50 28 V54 M39 44 L50 56 L61 44" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            f'<line x1="39" y1="67" x2="61" y2="67" stroke="{accent}" stroke-width="5.5" stroke-linecap="round"/>'
        )
    if name == "iot":
        nodes = [(16, 18), (84, 18), (16, 82), (84, 82)]
        return (
            "".join(f'<line x1="50" y1="50" x2="{x}" y2="{y}" {sw}/>' for x, y in nodes)
            + "".join(f'<circle cx="{x}" cy="{y}" r="10" fill="{fg}"/>' for x, y in nodes)
            + f'<circle cx="50" cy="50" r="18" fill="{fg}"/><circle cx="50" cy="50" r="7.5" fill="{accent}"/>'
        )
    if name == "doc":
        return (
            f'<path d="M20 6 H62 L82 26 V94 H20 Z" fill="{fg}"/><path d="M62 6 V26 H82 Z" fill="{light(accent, .45)}"/>'
            + "".join(f'<rect x="30" y="{y}" width="{w}" height="6" rx="3" fill="{accent}"/>'
                      for y, w in ((40, 42), (54, 42), (68, 28)))
        )
    if name == "user":
        return (f'<circle cx="50" cy="32" r="19" fill="{fg}"/>'
                f'<path d="M12 92 C12 56 88 56 88 92 Z" fill="{fg}"/>')
    if name == "bars":
        return "".join(f'<rect x="{x}" y="{y}" width="20" height="{92 - y}" rx="5" fill="{fg}"/>'
                       for x, y in ((12, 56), (40, 34), (68, 10)))
    if name == "star":
        return f'<polygon points="{star_pts(50, 54, 46, 19)}" fill="{fg}"/>'
    if name == "signal":
        return (f'<circle cx="18" cy="82" r="8" fill="{fg}"/>'
                f'<path d="M18 54 A28 28 0 0 1 46 82" {sw}/><path d="M18 30 A52 52 0 0 1 70 82" {sw}/>'
                f'<path d="M18 8 A74 74 0 0 1 92 82" {sw}/>')
    if name == "book":
        return (
            f'<path d="M50 8 C38 14 24 14 12 10 V86 C24 90 38 90 50 84 C62 90 76 90 88 86 V10 C76 14 62 14 50 8 Z" fill="{fg}"/>'
            f'<line x1="50" y1="8" x2="50" y2="84" stroke="{accent}" stroke-width="5"/>'
            + "".join(f'<line x1="20" y1="{y}" x2="42" y2="{y}" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>'
                      for y in (34, 46, 58))
            + "".join(f'<line x1="58" y1="{y}" x2="80" y2="{y}" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>'
                      for y in (34, 46, 58))
        )
    if name == "rocket":
        return (
            f'<path d="M50 4 C74 20 80 48 66 70 L50 62 L34 70 C20 48 26 20 50 4 Z" fill="{fg}"/>'
            f'<circle cx="50" cy="38" r="10" fill="{accent}"/>'
            f'<path d="M34 70 L26 92 L42 78 Z" fill="{fg}"/><path d="M66 70 L74 92 L58 78 Z" fill="{fg}"/>'
            f'<polygon points="46,92 54,92 50,100" fill="{fg}"/>'
        )
    if name == "api":
        return (
            f'<circle cx="50" cy="58" r="24" {sw}/>'
            f'<line x1="50" y1="58" x2="50" y2="22" {sw}/><line x1="50" y1="58" x2="80" y2="36" {sw}/>'
            f'<circle cx="50" cy="16" r="8" fill="{fg}"/><circle cx="86" cy="32" r="8" fill="{fg}"/>'
            f'<circle cx="50" cy="58" r="7" fill="{fg}"/>'
        )
    if name == "compass":
        return (
            f'<circle cx="50" cy="50" r="42" {sw}/>'
            f'<polygon points="50,20 60,50 50,80 40,50" fill="{fg}"/>'
            f'<polygon points="50,20 60,50 40,50" fill="{accent}"/>'
            f'<circle cx="50" cy="50" r="5" fill="{dk}"/>'
        )
    if name == "layers":
        return (
            f'<polygon points="50,8 90,30 50,52 10,30" fill="{fg}"/>'
            f'<polygon points="10,50 50,72 90,50 90,60 50,82 10,60" fill="{fg}" opacity=".75"/>'
            f'<polygon points="10,68 50,90 90,68 90,76 50,96 10,76" fill="{fg}" opacity=".5"/>'
        )
    if name == "route":
        return (
            f'<path d="M12 82 C30 82 30 60 48 60 C66 60 60 34 78 34 L88 34" {sw}/>'
            f'<circle cx="12" cy="82" r="9" fill="{fg}"/><circle cx="88" cy="34" r="9" fill="{fg}"/>'
            f'<circle cx="48" cy="60" r="6" fill="{fg}"/>'
        )
    return ""


def cube(cx, cy, s, c, cls="", glyph_name=None):
    """Isometric cube whose top vertex is at (cx, cy)."""
    w, h = s * 0.866, s * 0.5
    top, left, right, edge = light(c, .28), dark(c, .22), dark(c, .5), light(c, .6)

    def P(pts):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    t = [(cx, cy), (cx + w, cy + h), (cx, cy + 2 * h), (cx - w, cy + h)]
    l = [(cx - w, cy + h), (cx, cy + 2 * h), (cx, cy + 2 * h + s), (cx - w, cy + h + s)]
    r = [(cx, cy + 2 * h), (cx + w, cy + h), (cx + w, cy + h + s), (cx, cy + 2 * h + s)]
    g = f'<g class="{cls}">'
    g += f'<polygon points="{P(l)}" fill="{left}"/><polygon points="{P(r)}" fill="{right}"/>'
    g += f'<polygon points="{P(t)}" fill="{top}"/>'
    if glyph_name:
        g += (f'<g transform="matrix({w / 100:.4f} {h / 100:.4f} {-w / 100:.4f} {h / 100:.4f} {cx:.2f} {cy:.2f})">'
              f"{glyph(glyph_name, c)}</g>")
    g += (f'<polyline points="{P([(cx - w, cy + h), (cx, cy), (cx + w, cy + h)])}" fill="none" stroke="{edge}" '
          f'stroke-opacity=".55" stroke-width="1" stroke-linejoin="round"/>')
    return g + "</g>"


def ext_text(x, y, txt, size, weight=900, anchor="start", depth=8, far="#24105c", near="#5b32c9",
             dx=.75, dy=.95, spacing=0, top="#fff", extra="", cls="", style=""):
    """Faux-3D type: a stack of offset copies plus a bright top face."""
    out = []
    for i in range(depth, 0, -1):
        c = mix(near, far, i / depth)
        out.append(f'<text x="{x + i * dx:.2f}" y="{y + i * dy:.2f}" font-size="{size}" font-weight="{weight}" '
                   f'text-anchor="{anchor}" letter-spacing="{spacing}" fill="{c}" {extra}>{esc(txt)}</text>')
    out.append(f'<text class="{cls}" style="{style}" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
               f'text-anchor="{anchor}" letter-spacing="{spacing}" fill="{top}" {extra}>{esc(txt)}</text>')
    return "".join(out)


def slab(idp, x, y, w, h, accent, depth=12, rx=18):
    """A card with physical thickness. Returns (defs, markup)."""
    d = lg(f"{idp}f", [(0, PANEL1), (1, PANEL2)])
    d += lg(f"{idp}b", [(0, accent, .95), (.55, accent, .28), (1, accent, .08)], 0, 0, 1, 1)
    d += (f'<radialGradient id="{idp}g" cx=".1" cy=".05" r=".8"><stop offset="0" stop-color="{accent}" stop-opacity=".28"/>'
          f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')
    s = f'<rect x="{x + 10}" y="{y + depth + 8}" width="{w - 20}" height="{h - 4}" rx="{rx}" fill="#000" opacity=".5" filter="url(#b10)"/>'
    s += f'<rect x="{x}" y="{y + depth}" width="{w}" height="{h}" rx="{rx}" fill="{dark(accent, .74)}"/>'
    s += f'<rect x="{x}" y="{y + depth * .5:.1f}" width="{w}" height="{h}" rx="{rx}" fill="{dark(accent, .58)}"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{idp}f)"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{idp}g)"/>'
    s += (f'<rect x="{x + .75}" y="{y + .75}" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .5}" fill="none" '
          f'stroke="url(#{idp}b)" stroke-width="1.5"/>')
    s += f'<line x1="{x + rx}" y1="{y + 1.5}" x2="{x + w - rx}" y2="{y + 1.5}" stroke="#fff" stroke-opacity=".14"/>'
    return d, s


def pill(x, y, text, col, size=10.5, pad=9, h=22):
    w = len(text) * size * 0.62 + pad * 2
    m = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{col}" fill-opacity=".14" '
         f'stroke="{col}" stroke-opacity=".55"/>'
         f'<text class="m" x="{x + w / 2:.1f}" y="{y + h / 2 + size * .36:.1f}" font-size="{size}" text-anchor="middle" '
         f'fill="{light(col, .5)}" letter-spacing=".3">{esc(text)}</text>')
    return m, w


def wrap(txt, width):
    return textwrap.wrap(txt, width=width, break_long_words=False)


# =========================================================================
# HERO
# =========================================================================
def build_header():
    W, H, HY = 1200, 440, 300
    rnd = random.Random(7)
    d = lg("bg", [(0, "#060913"), (.55, "#0f0a2b"), (1, "#1a0f45")])
    d += ('<radialGradient id="gv" cx=".22" cy=".3" r=".6"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".45"/>'
          '<stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></radialGradient>'
          '<radialGradient id="gc" cx=".82" cy=".35" r=".55"><stop offset="0" stop-color="#22d3ee" stop-opacity=".30"/>'
          '<stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>')
    d += lg("face", [(0, "#ffffff"), (.5, "#ece4ff"), (1, "#a78bfa")])
    d += lg("fade", [(0, "#fff", 0), (.22, "#fff", 1), (1, "#fff", .85)])
    d += f'<mask id="gm"><rect x="0" y="{HY}" width="{W}" height="{H - HY}" fill="url(#fade)"/></mask>'
    d += lg("hz", [(0, "#8b5cf6", 0), (.5, "#c4b5fd", 1), (1, "#22d3ee", 0)], 0, 0, 1, 0)
    d += lg("bd", [(0, VIOLET, .8), (.5, "#ffffff", .08), (1, CYAN, .7)], 0, 0, 1, 1)
    d += lg("sc", [(0, CYAN, 0), (.5, "#a5f3fc", 1), (1, CYAN, 0)], 0, 0, 1, 0)
    d += f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="28"/></clipPath>'

    b = f'<g clip-path="url(#cp)"><rect width="{W}" height="{H}" fill="url(#bg)"/>'
    b += f'<rect width="{W}" height="{H}" fill="url(#gv)"/><rect width="{W}" height="{H}" fill="url(#gc)"/>'
    for _ in range(46):
        x, y = rnd.uniform(20, W - 20), rnd.uniform(14, HY - 24)
        if 200 < x < 1000 and 110 < y < 330:
            continue
        b += (f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([.8, 1, 1.2, 1.6])}" fill="#fff" '
              f'style="animation-delay:-{rnd.uniform(0, 3.4):.2f}s"/>')

    # perspective floor
    grid = ""
    for xb in range(-1500, 2701, 150):
        grid += f'<line x1="600" y1="{HY}" x2="{xb}" y2="{H}"/>'
    for k in range(1, 12):
        y = HY + (H - HY) * ((k / 11) ** 2.1)
        grid += f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"/>'
    b += f'<g mask="url(#gm)" stroke="#a78bfa" stroke-opacity=".5" stroke-width="1">{grid}</g>'
    b += f'<rect x="0" y="{HY - 1}" width="{W}" height="2" fill="url(#hz)" filter="url(#b4)" opacity=".9"/>'
    b += f'<rect x="0" y="{HY - .5}" width="{W}" height="1" fill="url(#hz)"/>'
    b += f'<rect class="sw" x="0" y="{HY - 1.5}" width="300" height="3" fill="url(#sc)"/>'

    # floating cubes (kept outside the title's footprint)
    cubes = [
        (118, 112, 44, VIOLET, "fl", 338), (58, 246, 26, CYAN, "fl2", 352), (170, 252, 20, PINK, "fl3", 346),
        (52, 92, 15, INDIGO, "fl3", 0),
        (1084, 126, 48, CYAN, "fl2", 340), (1142, 258, 24, VIOLET, "fl", 354), (1030, 262, 18, PINK, "fl3", 344),
        (1150, 84, 14, "#a78bfa", "fl", 0),
    ]
    for cx, cy, s, c, cls, sy in cubes:
        if sy:
            b += shadow(cx, sy, s * .95, .38)
        b += cube(cx, cy, s, c, cls)

    # status + role pills
    b += '<rect x="886" y="20" width="294" height="32" rx="16" fill="#052e1b" fill-opacity=".85" stroke="#22c55e" stroke-opacity=".6"/>'
    b += '<circle class="pr" cx="907" cy="36" r="4" fill="#22c55e"/><circle cx="907" cy="36" r="4" fill="#4ade80"/>'
    b += ('<text class="m" x="923" y="40.5" font-size="12" letter-spacing="1" fill="#86efac" font-weight="700">'
          'OPEN FOR FREELANCE QUESTS</text>')
    b += '<rect x="440" y="36" width="320" height="32" rx="16" fill="#ffffff" fill-opacity=".06" stroke="#a78bfa" stroke-opacity=".55"/>'
    b += ('<text class="m" x="600" y="57" font-size="13" text-anchor="middle" letter-spacing="2.2" fill="#c4b5fd" '
          'font-weight="700">FULL STACK DEVELOPER</text>')

    # the hero: extruded name
    NAME, NX, NY = "OMAR M. ETMAN", 200, 200
    glow = (f'<text x="{NX}" y="{NY}" font-size="80" font-weight="900" fill="#8b5cf6" opacity=".6" filter="url(#b18)" '
            f'textLength="800" lengthAdjust="spacingAndGlyphs">{NAME}</text>')
    b += glow
    ex = 'textLength="800" lengthAdjust="spacingAndGlyphs"'
    b += ext_text(NX, NY, NAME, 80, 900, "start", depth=16, far="#1c0c4d", near="#6d3ee0", dx=.8, dy=1.0,
                  top="url(#face)", extra=ex)
    b += (f'<text x="{NX}" y="{NY}" font-size="80" font-weight="900" fill="none" stroke="#fff" stroke-opacity=".35" '
          f'stroke-width="1" {ex}>{NAME}</text>')
    b += (f'<text x="600" y="256" font-size="20" text-anchor="middle" fill="#cbd5e1" font-style="italic">'
          f'Software Engineer from Planet Earth, currently operating at full stack</text>')

    # rotating one-liners (self-contained replacement for the typing-svg service)
    b += '<rect x="300" y="274" width="600" height="44" rx="22" fill="#0b1020" fill-opacity=".78" stroke="#22d3ee" stroke-opacity=".4"/>'
    b += '<circle class="pr" cx="330" cy="296" r="4" fill="#22d3ee"/><circle cx="330" cy="296" r="4" fill="#67e8f9"/>'
    for i, t in enumerate(["I turn caffeine into production code", "Bots. Apps. AI. Shipped.",
                           "Sleep is a deprecated feature"], 1):
        b += (f'<text class="m rl r{i}" x="618" y="303" font-size="21" text-anchor="middle" fill="#67e8f9" '
              f'font-weight="600">&gt; {esc(t)}</text>')

    # capability strip
    items = ["Telegram Bots", "AI Chatbots", "Offline-first Apps", "IoT Systems"]
    widths = [len(t) * 14 * .64 for t in items]
    gap = 44
    total = sum(widths) + gap * (len(items) - 1)
    x = 600 - total / 2
    for i, (t, w) in enumerate(zip(items, widths)):
        b += (f'<text class="m" x="{x + w / 2:.1f}" y="392" font-size="14" text-anchor="middle" fill="none" '
              f'stroke="#0b1020" stroke-width="5" stroke-linejoin="round" font-weight="600">{esc(t)}</text>')
        b += (f'<text class="m" x="{x + w / 2:.1f}" y="392" font-size="14" text-anchor="middle" fill="#fff" '
              f'font-weight="600">{esc(t)}</text>')
        x += w
        if i < len(items) - 1:
            b += (f'<rect x="{x + gap / 2 - 3:.1f}" y="383" width="6" height="6" fill="#a78bfa" '
                  f'transform="rotate(45 {x + gap / 2:.1f} 386)"/>')
        x += gap
    b += "</g>"
    b += f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="27" fill="none" stroke="url(#bd)" stroke-width="1.5"/>'

    css = """
@keyframes role{0%{opacity:0;transform:translateY(8px)}6%{opacity:1;transform:translateY(0)}30%{opacity:1;transform:translateY(0)}36%{opacity:0;transform:translateY(-8px)}100%{opacity:0}}
.rl{opacity:0;animation:role 9s infinite both}
.r2{animation-delay:3s}.r3{animation-delay:6s}
@media (prefers-reduced-motion:reduce){.r1{opacity:1}}
"""
    save("header.svg", svg(W, H, "Omar M. Etman: Software Engineer from Planet Earth, currently operating at full stack",
                           b, d, css))


# =========================================================================
# SECTION HEADERS
# =========================================================================
def build_section(fname, title, sub, gname, c1=VIOLET, c2=CYAN):
    W, H = 900, 88
    d = lg("pn", [(0, "#0b1020"), (1, "#171036")], 0, 0, 1, 1)
    d += lg("ln", [(0, c1), (.6, c2), (1, c2, 0)], 0, 0, 1, 0)
    d += lg("sp", [(0, "#fff", 0), (.5, "#fff", .9), (1, "#fff", 0)], 0, 0, 1, 0)
    d += lg("bd", [(0, c1, .8), (1, c2, .35)], 0, 0, 1, 1)
    d += f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
    b = f'<g clip-path="url(#cp)"><rect width="{W}" height="{H}" fill="url(#pn)"/>'
    b += f'<circle cx="60" cy="40" r="90" fill="{c1}" opacity=".10" filter="url(#b18)"/>'
    b += shadow(46, 74, 19, .45)
    b += cube(46, 14, 24, c1, "fl", gname)
    b += ext_text(92, 54, title, 34, 900, "start", depth=6, far="#24105c", near="#5b32c9", spacing=2.5,
                  top="#fff")
    b += (f'<text class="m" x="{W - 28}" y="50" font-size="14" text-anchor="end" fill="{MUTED}">{esc(sub)}</text>')
    b += f'<rect x="24" y="75" width="{W - 48}" height="2" rx="1" fill="url(#ln)"/>'
    b += f'<rect class="sw2" x="0" y="74" width="160" height="4" fill="url(#sp)"/></g>'
    b += f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="17.5" fill="none" stroke="url(#bd)" stroke-width="1.5"/>'
    save(fname, svg(W, H, title.title(), b, d))


# =========================================================================
# CARDS
# =========================================================================
def project_card(fname, w, title, kind, desc, chips, accent, gname, link_label, flag=False, idp="p"):
    PH, D = 222, 14
    H = PH + D + 10
    sw_ = w - 8
    d, b = slab(idp, 4, 4, sw_, PH, accent, depth=D, rx=20)
    b += shadow(70, 112, 30, .45)
    b += cube(70, 32, 34, accent, "fl", gname)
    b += f'<text class="m" x="128" y="48" font-size="11" letter-spacing="2.2" fill="{light(accent, .5)}" font-weight="700">{esc(kind)}</text>'
    b += f'<text x="128" y="82" font-size="26" font-weight="800" fill="#fff">{esc(title)}</text>'
    b += f'<rect x="128" y="94" width="44" height="3" rx="1.5" fill="{accent}"/>'
    chars = int((w - 56) / 7.7)
    for i, ln in enumerate(wrap(desc, chars)):
        b += f'<text x="28" y="{134 + i * 22}" font-size="14.5" fill="#cbd5e1">{esc(ln)}</text>'
    x = 28
    for c in chips:
        m, cw = pill(x, 188, c, accent)
        b += m
        x += cw + 8
    lw = 106
    lx = w - 28 - lw
    b += f'<rect x="{lx}" y="187" width="{lw}" height="30" rx="15" fill="{dark(accent, .5)}"/>'
    b += f'<rect x="{lx}" y="184" width="{lw}" height="30" rx="15" fill="{accent}"/>'
    b += (f'<rect x="{lx + 2}" y="185" width="{lw - 4}" height="12" rx="6" fill="#fff" opacity=".18"/>'
          f'<text class="m" x="{lx + lw / 2}" y="203.5" font-size="12" font-weight="800" text-anchor="middle" '
          f'fill="{INK}" letter-spacing="1.2">{esc(link_label)}</text>')
    if flag:
        m, fw = pill(w - 28 - 84, 20, "FLAGSHIP", AMBER)
        b += m
    save(fname, svg(w, H, f"{title}: {desc}", b, d))


def quest_card(fname, title, desc, accent, gname, idp="q"):
    w, PH, D = 432, 128, 12
    H = PH + D + 10
    d, b = slab(idp, 4, 4, w - 8, PH, accent, depth=D, rx=18)
    b += shadow(56, 88, 24, .45)
    b += cube(56, 24, 26, accent, "fl", gname)
    b += f'<text x="104" y="50" font-size="20" font-weight="800" fill="#fff">{esc(title)}</text>'
    b += f'<rect x="104" y="60" width="36" height="3" rx="1.5" fill="{accent}"/>'
    for i, ln in enumerate(wrap(desc, 40)):
        b += f'<text x="104" y="{86 + i * 20}" font-size="13.5" fill="#cbd5e1">{esc(ln)}</text>'
    save(fname, svg(w, H, f"{title}: {desc}", b, d))


# =========================================================================
# CHARACTER SHEET + ACHIEVEMENTS
# =========================================================================
def build_character():
    W, PH, D = 888, 330, 14
    H = PH + D + 10
    d, b = slab("c", 4, 4, W - 8, PH, VIOLET, depth=D, rx=22)
    d += lg("bar", [(0, VIOLET), (1, CYAN)], 0, 0, 1, 0)
    d += lg("vl", [(0, VIOLET, 0), (.5, VIOLET, .6), (1, VIOLET, 0)])
    b += shadow(140, 188, 62, .5)
    b += cube(140, 42, 64, VIOLET, "fl", "user")
    b += '<text x="140" y="216" font-size="17" font-weight="800" text-anchor="middle" fill="#fff" letter-spacing="1.5">OMAR M. ETMAN</text>'
    b += f'<text class="m" x="140" y="236" font-size="11" text-anchor="middle" fill="{MUTED}" letter-spacing="1.5">PLAYER ONE</text>'
    b += '<rect x="18" y="258" width="248" height="38" rx="19" fill="#052e1b" fill-opacity=".9" stroke="#22c55e" stroke-opacity=".6"/>'
    b += '<circle class="pr" cx="40" cy="277" r="4" fill="#22c55e"/><circle cx="40" cy="277" r="4" fill="#4ade80"/>'
    b += ('<text class="m" x="54" y="281" font-size="10.5" font-weight="700" fill="#86efac" letter-spacing=".5">'
          'OPEN FOR FREELANCE QUESTS</text>')
    b += '<rect x="278" y="30" width="1.5" height="274" fill="url(#vl)"/>'

    X0 = 312
    rows = [("ORIGIN", "Mansoura, Egypt"), ("CLASS", "Full Stack Software Developer"),
            ("LEVEL", "5+ years in production"), ("EDUCATION", "Mechatronics Engineering @ Delta University")]
    for i, (k, v) in enumerate(rows):
        y = 46 + i * 46
        b += f'<text class="m" x="{X0}" y="{y}" font-size="11" letter-spacing="2.4" fill="{light(VIOLET, .4)}" font-weight="700">{k}</text>'
        b += f'<text x="{X0}" y="{y + 24}" font-size="19" font-weight="600" fill="#fff">{esc(v)}</text>'
    b += f'<text class="m" x="{X0}" y="230" font-size="11" letter-spacing="2.4" fill="{light(VIOLET, .4)}" font-weight="700">SPECIAL ATTACK</text>'
    b += f'<text x="{X0}" y="256" font-size="19" font-weight="700" fill="#fff">Telegram Bots</text>'
    bx, bw = 490, 310
    b += f'<rect x="{bx}" y="242" width="{bw}" height="14" rx="7" fill="#1e2547"/>'
    b += f'<rect class="grow" x="{bx}" y="242" width="{bw * .95:.1f}" height="14" rx="7" fill="url(#bar)"/>'
    b += f'<rect x="{bx + 4}" y="244" width="{bw * .95 - 8:.1f}" height="4" rx="2" fill="#fff" opacity=".25"/>'
    b += f'<text class="m" x="{bx + bw + 12}" y="255" font-size="14" font-weight="800" fill="{CYAN}">95%</text>'
    b += f'<text class="m" x="{X0}" y="286" font-size="11" letter-spacing="2.4" fill="{light(VIOLET, .4)}" font-weight="700">SIDE QUESTS</text>'
    x = X0
    for t, c in (("AI chatbots", CYAN), ("Offline-first mobile apps", VIOLET), ("IoT systems", GREEN)):
        m, cw = pill(x, 296, t, c, size=11.5, h=24)
        b += m
        x += cw + 10
    save("character.svg", svg(W, H, "Character sheet: Omar M. Etman",
                              b, d, desc="Origin Mansoura, Egypt. Class: Full Stack Software Developer. Level: 5+ years in production. "
                                         "Education: Mechatronics Engineering at Delta University. Special attack: Telegram Bots, 95% mastery. "
                                         "Side quests: AI chatbots, offline-first mobile apps, IoT systems. Open for freelance quests."))


def build_achievements():
    tw, gap, PH, D = 204, 24, 112, 12
    rows = [
        [("5+", "YEARS IN PRODUCTION", VIOLET, "bars"), ("29", "PROJECTS SHIPPED", CYAN, "template"),
         ("64+", "TECHNICAL ARTICLES", PINK, "doc"), ("1", "PRODUCT SOLD", AMBER, "star")],
        [("10+", "BOTS DEPLOYED", TG, "bot"), ("100%", "SUCCESS RATE", GREEN, "signal"),
         ("24+", "SITE PAGES, AR + EN", INDIGO, "web"), ("8", "SKILL DOMAINS", VIOLET, "layers")],
    ]
    W = 4 * tw + 3 * gap
    RH = PH + D
    H = 2 * RH + 20 + 14
    d, b = "", ""
    for r, tiles in enumerate(rows):
        y0 = r * (RH + 20)
        for i, (num, label, col, g) in enumerate(tiles):
            x = i * (tw + gap)
            dd, s = slab(f"a{r}{i}", x + 2, y0 + 4, tw - 4, PH, col, depth=D, rx=18)
            d += dd
            b += f'<g class="rise" style="animation-delay:{(r * 4 + i) * .1:.2f}s">' + s
            b += ext_text(x + 24, y0 + 74, num, 50, 900, "start", depth=6, far=dark(col, .8), near=dark(col, .35),
                          top=light(col, .55))
            b += f'<text class="m" x="{x + 24}" y="{y0 + 100}" font-size="10.5" letter-spacing="1.1" fill="{MUTED}" font-weight="700">{label}</text>'
            b += cube(x + tw - 44, y0 + 20, 18, col, ["fl", "fl2", "fl3", "fl"][i], g)
            b += "</g>"
    save("achievements.svg", svg(W, H, "Achievements: 5+ years, 29 projects shipped, 64+ technical articles, 1 product sold, "
                                      "10+ bots deployed, 100% success rate, 24+ site pages, 8 skill domains",
                                 b, d))


# =========================================================================
# FULL STACK MASTERY (mirrors the 8 TECH_STACK domains on omarmetman.vercel.app)
# =========================================================================
STACK_CATS = [
    ("Frontend", CYAN, [("HTML5 / CSS3", 95, "5y"), ("JavaScript ES6+", 90, "5y"), ("Tailwind CSS", 90, "3y")]),
    ("Backend", GREEN, [("Telegram Bot API", 95, "4y"), ("Python", 90, "4y"), ("RESTful APIs", 90, "4y")]),
    ("Databases", AMBER, [("Firebase", 88, "3y"), ("SQLite", 88, "2y"), ("MySQL", 86, "3y")]),
    ("DevOps & Tools", INDIGO, [("Git / GitHub", 92, "5y"), ("Vercel", 88, "3y"), ("Linux / Bash", 87, "4y")]),
    ("Specializations", PINK, [("Telegram Bots", 95, "4y"), ("Business Automation", 90, "4y"), ("AI Integration", 88, "2y")]),
    ("Soft Skills", CYAN, [("Problem Solving", 95, "5y"), ("Fast Delivery", 93, "5y"), ("Self-Learning", 92, "5y")]),
    ("Systems & Embedded", "#f97316", [("C++", 87, "3y"), ("Arduino", 87, "3y"), ("ESP32", 85, "2y")]),
    ("Mobile", VIOLET, [("Flutter", 87, "2y"), ("Firebase Push", 87, "2y"), ("Dart", 86, "2y")]),
]


def build_stack():
    W, D = 888, 12
    COLW, VGAP, PAD = 432, 16, 20
    BH = 30 + 3 * 32 + 14
    PH = PAD + 4 * BH + 3 * VGAP
    H = PH + D + 10
    d, b = slab("st", 4, 4, W - 8, PH, VIOLET, depth=D, rx=22)
    d += lg("stbar", [(0, "#1e2547"), (1, "#1e2547")])
    for idx, (cat, col, skills) in enumerate(STACK_CATS):
        col_i, row = idx % 2, idx // 2
        x0 = 28 + col_i * (COLW + VGAP)
        y0 = PAD + row * (BH + VGAP)
        b += f'<rect x="{x0}" y="{y0 + 4}" width="14" height="14" rx="4" fill="{col}"/>'
        b += f'<text x="{x0 + 22}" y="{y0 + 17}" font-size="15" font-weight="800" fill="#fff" letter-spacing="1">{esc(cat)}</text>'
        for j, (name, lvl, yrs) in enumerate(skills):
            ry = y0 + 30 + j * 32
            b += f'<text x="{x0}" y="{ry + 12}" font-size="12.5" fill="#cbd5e1">{esc(name)}</text>'
            b += f'<text class="m" x="{x0 + COLW - 44}" y="{ry + 12}" font-size="11" text-anchor="end" fill="{MUTED}">{yrs}</text>'
            bx, bw = x0 + 150, COLW - 150 - 52
            b += f'<rect x="{bx}" y="{ry}" width="{bw}" height="11" rx="5.5" fill="#1e2547"/>'
            b += f'<rect class="grow" x="{bx}" y="{ry}" width="{bw * lvl / 100:.1f}" height="11" rx="5.5" fill="{col}"/>'
            b += f'<rect x="{bx + 2}" y="{ry + 1.5}" width="{bw * lvl / 100 - 4:.1f}" height="3" rx="1.5" fill="#fff" opacity=".25"/>'
            b += f'<text class="m" x="{bx + bw + 6}" y="{ry + 11}" font-size="11.5" font-weight="800" fill="{light(col, .5)}">{lvl}%</text>'
    save("stack.svg", svg(W, H, "Full stack mastery: 8 skill domains with proficiency levels from omarmetman.vercel.app",
                           b, d, desc="Frontend, Backend, Databases, DevOps, Specializations, Soft Skills, Systems and Embedded, Mobile."))


# =========================================================================
# ODYSSEY — experience timeline 2021 -> 2026 + education
# =========================================================================
def build_journey():
    W, D = 888, 12
    steps = [
        ("2021-2022", "Getting Started", "HTML, CSS, basic JavaScript and the first simple projects.", VIOLET),
        ("2023", "Leveling Up", "React, Node.js, first professional projects and Telegram bots.", CYAN),
        ("2024", "Going Pro", "13+ client projects, Next.js, Firebase and AI integration.", PINK),
        ("2025-2026", "Specialization", "Full-stack AI, a 24-page site, 64+ articles and full automation.", GREEN),
        ("EDU", "Mechatronics Engineering", "Delta University, Sophomore. First-year Smart Garage: Arduino, fingerprint, WebSocket remote.", AMBER),
    ]
    RH, TOP = 92, 20
    PH = TOP + len(steps) * RH + 8
    H = PH + D + 10
    SX = 190
    d, b = slab("jo", 4, 4, W - 8, PH, CYAN, depth=D, rx=22)
    b += f'<line x1="{SX}" y1="{TOP + 10}" x2="{SX}" y2="{TOP + len(steps) * RH - 10}" stroke="#334155" stroke-width="3"/>'
    for i, (yr, title, desc, col) in enumerate(steps):
        y = TOP + i * RH
        cy = y + RH / 2
        b += f'<circle cx="{SX}" cy="{cy}" r="13" fill="{dark(col, .7)}"/><circle cx="{SX}" cy="{cy}" r="7" fill="{col}"/>'
        b += f'<line x1="60" y1="{cy - 2}" x2="{SX - 20}" y2="{cy - 2}" stroke="{col}" stroke-opacity=".4" stroke-width="1.5"/>'
        m, _ = pill(28, cy - 26, yr, col, size=11, h=24)
        b += m
        b += f'<text x="{SX + 28}" y="{cy - 8}" font-size="18" font-weight="800" fill="#fff">{esc(title)}</text>'
        for k, ln in enumerate(wrap(desc, 62)):
            b += f'<text x="{SX + 28}" y="{cy + 16 + k * 20}" font-size="13.5" fill="#94a3b8">{esc(ln)}</text>'
    save("journey.svg", svg(W, H, "Odyssey: experience timeline 2021 to 2026 plus Mechatronics Engineering education",
                             b, d, desc="Getting Started 2021-2022, Leveling Up 2023, Going Pro 2024, Specialization 2025-2026, "
                                        "Mechatronics Engineering at Delta University."))


# =========================================================================
# OBSERVATION DECK — cinematic entry portal + "how to read" legend
# for the Battle Record section (3D city, radar, donut, serpent)
# =========================================================================
def build_portal():
    W, H = 888, 300
    rnd = random.Random(99)
    d = lg("pbg", [(0, "#05070f"), (.55, "#0c0623"), (1, "#160b3d")])
    d += ('<radialGradient id="pgl" cx=".5" cy=".42" r=".55"><stop offset="0" stop-color="#22d3ee" stop-opacity=".30"/>'
          '<stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>'
          '<radialGradient id="pgr" cx=".85" cy=".5" r=".4"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".35"/>'
          '<stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></radialGradient>')
    d += f'<clipPath id="pcp"><rect width="{W}" height="{H}" rx="22"/></clipPath>'
    d += lg("pbd", [(0, CYAN, .9), (.5, "#fff", .08), (1, VIOLET, .9)], 0, 0, 1, 0)
    b = f'<g clip-path="url(#pcp)"><rect width="{W}" height="{H}" fill="url(#pbg)"/>'
    b += f'<rect width="{W}" height="{H}" fill="url(#pgl)"/><rect width="{W}" height="{H}" fill="url(#pgr)"/>'
    for _ in range(60):
        b += (f'<circle class="tw" cx="{rnd.uniform(8, W - 8):.0f}" cy="{rnd.uniform(8, H - 8):.0f}" '
              f'r="{rnd.choice([.8, 1, 1.3, 1.7])}" fill="#fff" style="animation-delay:-{rnd.uniform(0, 3.4):.2f}s"/>')
    # radar scope on the right
    RX, RY, RR = 742, 150, 104
    b += f'<circle cx="{RX}" cy="{RY}" r="{RR + 18}" fill="#0b1020" fill-opacity=".7"/>'
    for r in (RR, RR * .72, RR * .44):
        b += f'<circle cx="{RX}" cy="{RY}" r="{r:.0f}" fill="none" stroke="#22d3ee" stroke-opacity=".45"/>'
    b += f'<line x1="{RX - RR}" y1="{RY}" x2="{RX + RR}" y2="{RY}" stroke="#22d3ee" stroke-opacity=".3"/>'
    b += f'<line x1="{RX}" y1="{RY - RR}" x2="{RX}" y2="{RY + RR}" stroke="#22d3ee" stroke-opacity=".3"/>'
    b += (f'<g class="spin"><polygon points="{RX - RR},{RY - 10} {RX - RR},{RY + 10} {RX + RR},{RY}" '
          f'fill="#22d3ee" opacity=".28"/></g>')
    b += f'<circle class="tw" cx="{RX + 52}" cy="{RY - 30}" r="4" fill="#f472b6"/>'
    b += f'<circle class="tw" cx="{RX - 40}" cy="{RY + 44}" r="4" fill="#22c55e" style="animation-delay:-1.4s"/>'
    b += f'<circle class="tw" cx="{RX + 10}" cy="{RY + 62}" r="3" fill="#f59e0b" style="animation-delay:-2.2s"/>'
    b += f'<circle cx="{RX}" cy="{RY}" r="4" fill="#fff"/>'
    # copy on the left
    b += ('<text class="m" x="48" y="72" font-size="12" letter-spacing="3" fill="#67e8f9" font-weight="700">'
          '// LIVE TELEMETRY</text>')
    b += ext_text(46, 140, "OBSERVATION", 56, 900, "start", depth=10, far="#0b3a44", near="#0e7490",
                  top="#ffffff", spacing=1)
    b += ext_text(46, 196, "DECK", 56, 900, "start", depth=10, far="#24105c", near="#6d3ee0",
                  top="#c4b5fd", spacing=8)
    for i, ln in enumerate(["You are looking at live data, not decoration.",
                            "Every chart below rebuilds itself from the commit history."]):
        b += f'<text x="48" y="{226 + i * 24}" font-size="15" fill="#94a3b8">{esc(ln)}</text>'
    b += '<rect x="48" y="272" width="220" height="2" fill="#22d3ee" opacity=".5"/>'
    b += "</g>"
    b += f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="url(#pbd)" stroke-width="1.5"/>'
    css = ("@keyframes spin{to{transform:rotate(360deg)}}"
           ".spin{transform-box:fill-box;transform-origin:center;animation:spin 5s linear infinite}")
    save("portal.svg", svg(W, H, "Observation deck: live telemetry portal",
                            b, d, css, desc="You are looking at live data, not decoration."))


def build_legend():
    W, D = 888, 12
    rows = [
        ("THE LIVING CITY", "The isometric hologram is a full year of GitHub, rebuilt daily: every floor tile is one "
         "day, every tower is code shipped that day. The pentagon radar scores 5 dimensions — Commit, Issue, "
         "Pull Request, Review, Repo. Pure proof of work, with no language labels by design.",
         CYAN, "layers"),
        ("THE LANGUAGE MIX", "The top-languages card counts code across every public repository, live on every "
         "render — it is a GitHub snapshot, not the whole story. The full 53-skill arsenal with mastery levels "
         "lives up in the Full Arsenal section.",
         PINK, "compass"),
        ("THE SERPENT", "A snake that eats the contribution grid, cell by cell. It only moves where there is history "
         "to devour — so a long snake is proof of consistency, the one statistic that cannot be faked.",
         GREEN, "route"),
    ]
    RH, TOP, FOOT = 132, 74, 64
    PH = TOP + len(rows) * RH + FOOT + 12
    H = PH + D + 10
    d, b = slab("lgd", 4, 4, W - 8, PH, VIOLET, depth=D, rx=22)
    b += ('<text class="m" x="32" y="36" font-size="12" letter-spacing="3" fill="#c4b5fd" font-weight="700">'
          'FIELD MANUAL</text>')
    b += f'<text x="30" y="64" font-size="21" font-weight="800" fill="#fff">How to read this battlefield</text>'
    for i, (title, desc, col, g) in enumerate(rows):
        y = TOP + i * RH
        b += f'<rect x="30" y="{y}" width="{W - 60}" height="{RH - 12}" rx="14" fill="#0b1020" fill-opacity=".65" stroke="{col}" stroke-opacity=".35"/>'
        b += shadow(84, y + 66, 22, .45)
        b += cube(84, y + 12, 24, col, "fl", g)
        b += f'<text x="128" y="{y + 36}" font-size="16" font-weight="800" fill="{light(col, .5)}" letter-spacing="1">{esc(title)}</text>'
        for k, ln in enumerate(wrap(desc, 74)):
            b += f'<text x="128" y="{y + 60 + k * 20}" font-size="13" fill="#cbd5e1">{esc(ln)}</text>'
    fy = TOP + len(rows) * RH + 8
    b += f'<rect x="30" y="{fy}" width="{W - 60}" height="44" rx="22" fill="#052e1b" fill-opacity=".8" stroke="#22c55e" stroke-opacity=".5"/>'
    b += ('<text x="44" y="{0}" font-size="14" font-weight="700" fill="#86efac">Vanity metrics rot — but a daily-rebuilt city '
          'cannot lie.</text>').format(fy + 28)
    save("legend.svg", svg(W, H, "Field manual: how to read the living city, the language mix and the serpent",
                            b, d, desc="How to read this battlefield. Vanity metrics rot; a daily-rebuilt city does not lie."))


# =========================================================================
# DOCTRINE, CTA, FOOTER
# =========================================================================
def build_doctrine():
    W, PH, D, GAP = 888, 58, 8, 18
    quotes = [("Ship fast. Break nothing.", VIOLET),
              ("If it is not bilingual, realtime and offline-first, it is not finished.", CYAN),
              ("Sleep is a deprecated feature.", PINK)]
    H = 4 + len(quotes) * (PH + D + GAP)
    d, b = "", ""
    for i, (q, c) in enumerate(quotes):
        y = 4 + i * (PH + D + GAP)
        dd, s = slab(f"d{i}", 4, y, W - 8, PH, c, depth=D, rx=16)
        d += dd
        b += f'<g class="rise" style="animation-delay:{i * .15:.2f}s">' + s
        b += f'<text x="34" y="{y + 56}" font-size="64" font-weight="900" fill="{c}" opacity=".9" font-family="Georgia,serif">&#8220;</text>'
        b += f'<text x="84" y="{y + 36}" font-size="21" font-style="italic" font-weight="600" fill="#fff">{esc(q)}</text>'
        b += "</g>"
    save("doctrine.svg", svg(W, H, "Combat doctrine: " + " ".join(q for q, _ in quotes), b, d))


def build_cta(fname, label, w=440):
    H = 100
    d = lg("bt", [(0, "#a78bfa"), (1, "#7c3aed")])
    d += lg("sh", [(0, "#fff", 0), (.5, "#fff", .55), (1, "#fff", 0)], 0, 0, 1, 0)
    d += f'<clipPath id="bc"><rect x="8" y="12" width="{w - 16}" height="60" rx="30"/></clipPath>'
    b = f'<ellipse class="fl3" cx="{w / 2}" cy="52" rx="{w / 2 - 20}" ry="24" fill="#8b5cf6" opacity=".35" filter="url(#b18)"/>'
    b += f'<rect x="8" y="24" width="{w - 16}" height="60" rx="30" fill="#3b1585"/>'
    b += f'<rect x="8" y="18" width="{w - 16}" height="60" rx="30" fill="#5b21b6"/>'
    b += f'<rect x="8" y="12" width="{w - 16}" height="60" rx="30" fill="url(#bt)"/>'
    b += f'<rect x="12" y="14" width="{w - 24}" height="26" rx="13" fill="#fff" opacity=".16"/>'
    b += f'<g clip-path="url(#bc)"><rect class="sw" x="0" y="12" width="90" height="60" fill="url(#sh)" transform="skewX(-18)"/></g>'
    b += (f'<text x="{w / 2}" y="50" font-size="23" font-weight="800" text-anchor="middle" fill="none" letter-spacing="2.4" '
          f'stroke="#3b1585" stroke-width="4" stroke-linejoin="round">{esc(label)}</text>')
    b += (f'<text x="{w / 2}" y="50" font-size="23" font-weight="800" text-anchor="middle" fill="#fff" '
          f'letter-spacing="2.4">{esc(label)}</text>')
    save(fname, svg(w, H, label, b, d))


def wave_path(amp, period, base, phase, width, height):
    pts, x = [], 0.0
    while x <= width + 0.1:
        pts.append(f"{x:.1f},{base + amp * math.sin(2 * math.pi * x / period + phase):.1f}")
        x += period / 16
    return "M" + " L".join(pts) + f" L{width},{height} L0,{height} Z"


def build_footer():
    W, H = 1200, 200
    d = lg("bg", [(0, "#0b0a24"), (1, "#150c3a")])
    d += lg("w1", [(0, VIOLET, .55), (1, VIOLET, .15)])
    d += lg("w2", [(0, CYAN, .45), (1, CYAN, .10)])
    d += lg("w3", [(0, "#a78bfa", .7), (1, "#4c1d95", .5)])
    d += lg("bd", [(0, VIOLET, .8), (.5, "#fff", .06), (1, CYAN, .7)], 0, 0, 1, 0)
    d += f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
    css = """
@keyframes wv{0%{transform:translateX(0)}100%{transform:translateX(-1200px)}}
.w1{animation:wv 16s linear infinite}.w2{animation:wv 11s linear infinite}.w3{animation:wv 8s linear infinite}
"""
    b = f'<g clip-path="url(#cp)"><rect width="{W}" height="{H}" fill="url(#bg)"/>'
    rnd = random.Random(11)
    for _ in range(26):
        b += (f'<circle class="tw" cx="{rnd.uniform(20, W - 20):.0f}" cy="{rnd.uniform(10, 110):.0f}" r="{rnd.choice([.8, 1, 1.3])}" '
              f'fill="#fff" style="animation-delay:-{rnd.uniform(0, 3.4):.2f}s"/>')
    b += cube(96, 30, 26, VIOLET, "fl") + cube(1104, 40, 22, CYAN, "fl2") + cube(170, 70, 12, PINK, "fl3")
    b += cube(1034, 22, 12, INDIGO, "fl3")
    b += ('<text x="600" y="72" font-size="24" font-weight="700" text-anchor="middle" fill="#fff" letter-spacing="1.5">'
          'Forged in Mansoura, deployed to the world</text>')
    b += f'<text class="m" x="600" y="102" font-size="13" text-anchor="middle" fill="{MUTED}" letter-spacing="2">THANKS FOR STOPPING BY THE LAB</text>'
    b += f'<path class="w1" d="{wave_path(12, 600, 128, 0, 2400, H)}" fill="url(#w1)"/>'
    b += f'<path class="w2" d="{wave_path(9, 400, 146, 1.3, 2400, H)}" fill="url(#w2)"/>'
    b += f'<path class="w3" d="{wave_path(7, 300, 164, 2.6, 2400, H)}" fill="url(#w3)"/></g>'
    b += f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="27" fill="none" stroke="url(#bd)" stroke-width="1.5"/>'
    save("footer.svg", svg(W, H, "Forged in Mansoura, deployed to the world", b, d, css))


# =========================================================================
# COPY (edit here)
# =========================================================================
if __name__ == "__main__":
    build_header()

    build_section("section-character.svg", "CHARACTER SHEET", "// about.me", "user")
    build_section("section-arsenal.svg", "ARSENAL", "// skills.unlock()", "web", VIOLET, CYAN)
    build_section("section-stack.svg", "FULL ARSENAL", "// stack.mastery()", "layers", CYAN, GREEN)
    build_section("section-journey.svg", "ODYSSEY", "// journey.log()", "route", GREEN, AMBER)
    build_section("section-record.svg", "BATTLE RECORD", "// github.stats()", "bars", CYAN, VIOLET)
    build_section("section-builds.svg", "LEGENDARY BUILDS", "// projects.showcase()", "star", PINK, VIOLET)
    build_section("section-quests.svg", "QUEST BOARD", "// hire.me()", "doc", GREEN, CYAN)
    build_section("section-doctrine.svg", "COMBAT DOCTRINE", "// principles.md", "quote", AMBER, PINK)
    build_section("section-channels.svg", "TRANSMISSION CHANNELS", "// contact.open()", "signal", TG, VIOLET)

    build_character()
    build_achievements()
    build_stack()
    build_journey()
    build_portal()
    build_legend()

    project_card("card-whisper.svg", 888, "Whisper", "REAL-TIME CHAT REALM",
                 "A real-time bilingual chat realm: fingerprint-locked vaults, an AI oracle, expiring stories "
                 "and offline mode. Co-forged with Sara Waleed.",
                 ["Realtime", "Bilingual", "AI oracle", "Offline mode"], VIOLET, "chat", "ENTER  \u2192", flag=True, idp="p0")
    project_card("card-devforge.svg", 432, "DevForge", "OFFLINE DEV WORKSHOP",
                 "An offline Windows workshop for developers: projects, commands and monitoring in one fast bilingual app.",
                 ["Rust", "Tauri 2", "Offline"], INDIGO, "rocket", "GET  \u2192", idp="p1")
    project_card("card-baseeraa.svg", 432, "Baseeraa", "KNOWLEDGE PLATFORM",
                 "An interactive knowledge and culture platform: psychology, philosophy and science with social dynamics.",
                 ["Next.js", "Firebase", "Community"], PINK, "book", "ENTER  \u2192", idp="p2")
    project_card("card-sirat.svg", 432, "Sirat-E-Mustaqeem", "ISLAMIC APP",
                 "A free, ad-free sanctuary: Quran, Athkar and prayer times.",
                 ["Quran", "Athkar", "Prayer times"], AMBER, "crescent", "ENTER  \u2192", idp="p3")
    project_card("card-finance.svg", 432, "Etman Finance", "PERSONAL FINANCE",
                 "An offline vault for personal finance: bilingual, with zero accounts.",
                 ["Offline", "Bilingual", "No accounts"], CYAN, "wallet", "ENTER  \u2192", idp="p4")
    project_card("card-archive.svg", 888, "The Full Archive", "MORE FROM THE LAB",
                 "29 conquered projects, 16 client deliveries, 1 sold product and 64+ scrolls of knowledge.",
                 ["Projects", "Articles", "Case studies"], INDIGO, "doc", "EXPLORE  \u2192", idp="p5")

    quest_card("quest-bots.svg", "Telegram Bots",
               "Custom bots, automations and integrations. My special attack.", TG, "bot", "q0")
    quest_card("quest-ai.svg", "AI Chatbots",
               "Conversational assistants wired into real products.", VIOLET, "chip", "q1")
    quest_card("quest-web.svg", "Full-Stack Web Apps",
               "From idea to deployed product with React, Next.js and Node.", PINK, "web", "q2")
    quest_card("quest-mobile.svg", "Offline-first Apps",
               "Apps that stay fast and useful with no connection at all.", AMBER, "offline", "q3")
    quest_card("quest-iot.svg", "IoT Systems",
               "Mechatronics meets software: connected hardware that talks to the cloud.", GREEN, "iot", "q4")
    quest_card("quest-api.svg", "API Development",
               "Robust RESTful and GraphQL APIs that connect systems seamlessly.", INDIGO, "api", "q6")
    quest_card("quest-consult.svg", "Tech Consulting",
               "Stack decisions, architecture reviews and code audits.", CYAN, "compass", "q7")
    quest_card("quest-writing.svg", "Technical Writing",
               "64+ articles sharing what I learn while shipping.", CYAN, "doc", "q5")

    build_cta("cta.svg", "START A PROJECT  \u2192")
    build_doctrine()
    build_footer()
