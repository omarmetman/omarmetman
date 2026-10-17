#!/usr/bin/env python3
"""
Builds every live telemetry visual in the profile from the GitHub REST API,
then commits nothing on its own — the workflow does that.

Why not third-party badge services? They render flat, break silently, and
drift from the profile's visual language. Here every panel is drawn with the
same extruded/3D helpers the rest of the profile uses, so the Observation Deck
reads as one artifact.

Usage (workflow):
    GITHUB_TOKEN=... python3 tools/build_telemetry.py omarmetman

With no token it still works: only the public REST endpoints are used, and a
failed fetch degrades to a styled "signal lost" panel instead of a broken image.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "tools" else HERE
OUT = os.path.join(ROOT, "telemetry")
os.makedirs(OUT, exist_ok=True)

API = "https://api.github.com"
UA = "omarmetman-profile-telemetry"

VIOLET, CYAN, PINK = "#8b5cf6", "#22d3ee", "#f472b6"
GREEN, AMBER, INDIGO = "#22c55e", "#f59e0b", "#6366f1"
INK, PANEL, TEXT, MUTED = "#080c18", "#141b36", "#e2e8f0", "#94a3b8"
PAGE_BG = "#050914"

SANS = "'Segoe UI', Inter, system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

CSS = f"""
text{{font-family:{SANS}}}
.m{{font-family:{MONO}}}
@keyframes sweep{{0%{{transform:translateX(-40%)}}100%{{transform:translateX(140%)}}}}
@keyframes pulseGlow{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
@keyframes rise{{0%{{opacity:0;transform:translateY(14px)}}100%{{opacity:1;transform:translateY(0)}}}}
.sw{{animation:sweep 6s linear infinite}}
.glow{{animation:pulseGlow 3.4s ease-in-out infinite}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


# --- tiny svg toolkit (same visual language as build_assets.py) -----------
def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def rgb(h: str):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def hexc(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a: str, b: str, t: float) -> str:
    return hexc([x + (y - x) * t for x, y in zip(rgb(a), rgb(b))])


def light(c: str, t: float) -> str:
    return mix(c, "#ffffff", t)


def dark(c: str, t: float) -> str:
    return mix(c, "#000000", t)


def grad(gid, stops, x1=0, y1=0, x2=0, y2=1) -> str:
    s = ""
    for st in stops:
        op = f' stop-opacity="{st[2]}"' if len(st) > 2 else ""
        s += f'<stop offset="{st[0]}" stop-color="{st[1]}"{op}/>'
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def svg(w, h, title, body, defs="", desc=None) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
            f'<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc or title)}</desc>\n'
            f"<defs>{defs}</defs>\n<style>{CSS}</style>\n"
            f'<rect width="{w}" height="{h}" fill="{PAGE_BG}"/>\n{body}\n</svg>\n')


def save(name: str, data: str) -> None:
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"wrote {name:34s} {len(data) / 1024:6.1f} KB")


def slab(idp, x, y, w, h, accent, depth=14, rx=22, glow=True):
    """Card with physical thickness + corner bloom."""
    d = grad(f"{idp}f", [(0, PANEL), (1, dark(PANEL, .3))], 0, 0, 1, 1)
    d += grad(f"{idp}b", [(0, accent, .95), (.6, accent, .25), (1, accent, .07)], 0, 0, 1, 1)
    if glow:
        d += (f'<radialGradient id="{idp}g" cx=".08" cy="0" r=".85">'
              f'<stop offset="0" stop-color="{accent}" stop-opacity=".30"/>'
              f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')
    s = (f'<rect x="{x + 8}" y="{y + depth + 6}" width="{w - 16}" height="{h - 4}" rx="{rx}" '
         f'fill="#000" opacity=".42" filter="url(#soft2)"/>')
    s += f'<rect x="{x}" y="{y + depth}" width="{w}" height="{h}" rx="{rx}" fill="{dark(accent, .72)}"/>'
    s += f'<rect x="{x}" y="{y + depth * .5:.1f}" width="{w}" height="{h}" rx="{rx}" fill="{dark(accent, .55)}"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{idp}f)"/>'
    if glow:
        s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{idp}g)"/>'
    s += (f'<rect x="{x + .75}" y="{y + .75}" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .5}" fill="none" '
          f'stroke="url(#{idp}b)" stroke-width="1.5"/>')
    s += f'<line x1="{x + rx}" y1="{y + 1.5}" x2="{x + w - rx}" y2="{y + 1.5}" stroke="#fff" stroke-opacity=".13"/>'
    return d, s


FILTERS = ('<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
           '<feGaussianBlur stdDeviation="7"/></filter>'
           '<filter id="soft2" x="-40%" y="-40%" width="180%" height="180%">'
           '<feGaussianBlur stdDeviation="3"/></filter>')


def heading(d, b, x, y, kicker, title, accent):
    b += (f'<text class="m" x="{x}" y="{y}" font-size="11" letter-spacing="3.4" '
          f'fill="{light(accent, .35)}" font-weight="700">{esc(kicker)}</text>')
    b += f'<text x="{x}" y="{y + 30}" font-size="26" font-weight="800" fill="#fff" letter-spacing="1.6">{esc(title)}</text>'
    b += f'<rect x="{x}" y="{y + 40}" width="54" height="3" rx="1.5" fill="{accent}"/>'
    return d, b


# --- data -----------------------------------------------------------------
def fetch(path: str, token: str | None):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
        "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def n(v) -> str:
    """1234 -> 1.2k"""
    v = int(v or 0)
    return f"{v / 1000:.1f}k".replace(".0k", "k") if v >= 10000 else str(v)


# --- panels ---------------------------------------------------------------
def build_overview(user, repos, followers, tokens):
    W, H, PAD = 880, 240, 34
    d = FILTERS
    tiles = [
        ("PUBLIC REPOS", n(len(repos)), VIOLET),
        ("FOLLOWERS", n(followers), CYAN),
        ("TOTAL STARS", n(sum(r.get("stargazers_count", 0) for r in repos)), PINK),
        ("FORKS SERVED", n(sum(r.get("forks_count", 0) for r in repos)), AMBER),
    ]
    tw = (W - PAD * 2 - 18 * 3) / 4
    body = ""
    for i, (label, val, col) in enumerate(tiles):
        x = PAD + i * (tw + 18)
        dd, s = slab(f"o{i}", x, PAD, tw, H - PAD - 34, col, depth=10, rx=18)
        d += dd
        body += f'<g class="rise" style="animation-delay:{i * .1:.2f}s">' + s
        body += f'<rect x="{x + 20}" y="{PAD + 18}" width="4" height="{H - PAD - 34 - 36}" rx="2" fill="{col}" opacity=".8"/>'
        body += (f'<text class="m" x="{x + 34}" y="{PAD + 42}" font-size="10.5" letter-spacing="2" '
                 f'fill="{MUTED}" font-weight="700">{esc(label)}</text>')
        body += f'<text x="{x + 34}" y="{PAD + 92}" font-size="40" font-weight="800" fill="#fff">{esc(val)}</text>'
        body += "</g>"
    d += grad("obar", [(0, CYAN), (1, VIOLET)], 0, 0, 1, 0)
    body += f'<rect x="{PAD}" y="{H - 22}" width="{W - PAD * 2}" height="3" rx="1.5" fill="#1e2547"/>'
    filled = min(1.0, len(repos) / 30)
    body += (f'<rect x="{PAD}" y="{H - 22}" width="{(W - PAD * 2) * filled:.0f}" height="3" rx="1.5" '
             f'fill="url(#obar)" class="glow"/>')
    save("overview.svg", svg(W, H, "Account overview: repositories, followers, stars and forks",
                             body, d, desc="Live account overview from the GitHub API."))


def build_langs(repos):
    agg: dict[str, int] = {}
    for r in repos:
        if r.get("fork") or not r.get("language"):
            continue
        agg[r["language"]] = agg.get(r["language"], 0) + 1
    top = sorted(agg.items(), key=lambda kv: -kv[1])[:8]
    if not top:
        return
    ROW_H = 46
    W, H, PAD, ROW = 880, 150 + len(top) * ROW_H, 34, ROW_H
    d, b = slab("lg", 8, 8, W - 16, H - 30, CYAN, depth=14, rx=22)
    d, b = heading(d, b, PAD, PAD + 6, "// CODE COMPOSITION", "FORGED IN WHAT", CYAN)
    total = sum(v for _, v in top) or 1
    maxv = top[0][1]
    for i, (lang, v) in enumerate(top):
        y = PAD + 86 + i * ROW
        share = v / total
        d += grad(f"lb{i}", [(0, light(mix(CYAN, PINK, i / max(len(top) - 1, 1)), .1)),
                             (1, mix(CYAN, PINK, i / max(len(top) - 1, 1)))], 0, 0, 1, 0)
        b += f'<text x="{PAD}" y="{y + 15}" font-size="14.5" fill="{TEXT}" font-weight="600">{esc(lang)}</text>'
        b += f'<text x="{W - PAD}" y="{y + 15}" font-size="12" fill="{MUTED}" text-anchor="end" class="m">{v} repos · {share * 100:.0f}%</text>'
        bx, bw = PAD, W - PAD * 2
        b += f'<rect x="{bx}" y="{y + 24}" width="{bw}" height="10" rx="5" fill="#1a2142"/>'
        b += f'<rect class="grow" x="{bx}" y="{y + 24}" width="{bw * (v / maxv):.1f}" height="10" rx="5" fill="url(#lb{i})"/>'
        b += f'<rect x="{bx + 2}" y="{y + 26}" width="{max(0, bw * (v / maxv) - 4):.1f}" height="3" rx="1.5" fill="#fff" opacity=".28"/>'
    save("languages.svg", svg(W, H, "Language composition across owned repositories",
                             b, d, desc="Repository count and share per language, from the GitHub API."))


def build_activity(events):
    """Rolling 90-day activity as an isometric skyline."""
    day = 86400
    today = dt.date.today()
    days = [(today - dt.timedelta(days=i)) for i in range(89, -1, -1)]
    counts = {e.get("created_at", "")[:10]: 0 for e in events}
    for e in events:
        d_ = e.get("created_at", "")[:10]
        counts[d_] = counts.get(d_, 0) + 1
    series = [counts.get(d_.isoformat(), 0) for d_ in days]
    peak = max(series) or 1
    active = sum(1 for v in series if v)

    W, PAD, BASE = 880, 40, 232
    H = BASE + 96
    d = FILTERS
    dd, b = slab("ac", 8, 8, W - 16, H - 30, VIOLET, depth=14, rx=22)
    d += dd
    d, b = heading(d, b, PAD, PAD, "// ROLLING 90 DAYS", "THE PULSE", VIOLET)
    for i in range(4):
        d += grad(f"ab{i}", [(0, light(mix(CYAN, VIOLET, i / 3), .25)), (1, dark(mix(CYAN, VIOLET, i / 3), .45))],
                  0, 0, 0, 1)
    floor = BASE
    # back-to-front rows for depth
    ROWS = 3
    per_row = len(series) // ROWS
    for row in range(ROWS):
        scale = 1 - row * 0.13
        yb = floor - row * 13
        bw = 4.6
        gap = 1.6
        inner_w = W - PAD * 2 - 60
        step = inner_w / per_row
        bw = step - gap
        x0 = PAD + 30 + row * 30
        for c in range(per_row):
            idx = row * per_row + c
            v = series[idx] if idx < len(series) else 0
            hh = (v / peak) * 92 * scale
            x = x0 + c * step
            col = mix(CYAN, VIOLET, c / max(per_row - 1, 1))
            if v == 0:
                b += f'<rect x="{x:.1f}" y="{yb - 3:.1f}" width="{bw:.1f}" height="3" rx="1.5" fill="#243055"/>'
            else:
                b += (f'<rect x="{x:.1f}" y="{yb - hh - 2:.1f}" width="{bw:.1f}" height="3" rx="1.5" '
                      f'fill="{dark(col, .3)}"/>')
                b += f'<rect x="{x:.1f}" y="{yb - hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="1.5" fill="url(#ab{row})"/>'
                b += (f'<rect x="{x:.1f}" y="{yb - hh:.1f}" width="{bw:.1f}" height="2" rx="1" fill="#fff" '
                      f'opacity=".55"/>')
    # floor glow
    d += grad("afloor", [(0, VIOLET, .55), (1, CYAN, .05)], 0, 0, 1, 0)
    b += f'<rect x="{PAD}" y="{floor - 2}" width="{W - PAD * 2}" height="2" rx="1" fill="url(#afloor)"/>'
    b += f'<rect class="sw" x="{PAD}" y="{floor - 2}" width="150" height="2" fill="#fff" opacity=".35"/>'
    # footer readouts
    fy = floor + 30
    reads = [("EVENTS LOGGED", str(sum(series)), CYAN), ("ACTIVE DAYS", f"{active}/90", GREEN),
             ("PEAK DAY", str(peak), PINK), ("AVG / ACTIVE DAY", f"{sum(series) / max(active, 1):.1f}", AMBER)]
    colw = (W - PAD * 2) / 4
    for i, (lab, val, col) in enumerate(reads):
        x = PAD + i * colw
        b += f'<text class="m" x="{x:.0f}" y="{fy}" font-size="10" letter-spacing="1.8" fill="{MUTED}" font-weight="700">{esc(lab)}</text>'
        b += f'<text x="{x:.0f}" y="{fy + 30}" font-size="26" font-weight="800" fill="{light(col, .35)}">{esc(val)}</text>'
    save("activity.svg", svg(W, H, "Rolling 90 day activity skyline",
                            b, d, desc=f"{sum(series)} events across {active} active days, peak {peak}."))


def build_streak(events):
    streak = 0
    today = dt.date.today()
    dates = {e.get("created_at", "")[:10] for e in events}
    for i in range(0, 400):
        if (today - dt.timedelta(days=i)).isoformat() in dates:
            streak += 1
        elif i > 0 or (today - dt.timedelta(days=i)).isoformat() not in dates:
            if i == 0:
                continue
            break
    W, H, PAD = 880, 236, 34
    d, b = slab("st", 8, 8, W - 16, H - 30, AMBER, depth=14, rx=22)
    d += grad("stbar", [(0, AMBER), (.45, "#fbbf24"), (1, PINK)], 0, 0, 1, 0)
    d, b = heading(d, b, PAD, PAD, "// CONSISTENCY", "THE STREAK", AMBER)
    b += (f'<text x="{PAD}" y="{PAD + 76}" font-size="14" fill="{TEXT}">'
          f'Consecutive days with at least one public event</text>')
    digits = len(str(streak))
    b += f'<text x="{PAD}" y="{H - 44}" font-size="56" font-weight="800" fill="url(#stbar)">{streak}</text>'
    b += f'<text x="{PAD + digits * 33 + 10}" y="{H - 44}" font-size="18" fill="{MUTED}">days</text>'
    # right side: last 14 day pips, vertically centred against the headline
    RX = W - PAD
    b += (f'<text class="m" x="{RX}" y="{PAD + 24}" font-size="10" letter-spacing="2" '
          f'text-anchor="end" fill="{MUTED}" font-weight="700">LAST 14 DAYS</text>')
    pw, pg = 30, 9
    px0 = RX - (14 * pw + 13 * pg)
    py = PAD + 42
    for i in range(14):
        day = today - dt.timedelta(days=13 - i)
        hit = day.isoformat() in dates
        x = px0 + i * (pw + pg)
        if hit:
            b += f'<rect x="{x}" y="{py + 34}" width="{pw}" height="6" rx="3" fill="{dark(AMBER, .38)}"/>'
            b += f'<rect x="{x}" y="{py}" width="{pw}" height="38" rx="9" fill="{AMBER}"/>'
            b += f'<rect x="{x + 3}" y="{py + 3}" width="{pw - 6}" height="10" rx="5" fill="#fff" opacity=".3"/>'
        else:
            b += f'<rect x="{x}" y="{py + 26}" width="{pw}" height="12" rx="6" fill="#1e2547"/>'
        b += (f'<text class="m" x="{x + pw / 2:.0f}" y="{py + 58}" font-size="8.5" text-anchor="middle" '
              f'fill="{MUTED}">{day.strftime("%d")}</text>')
    save("streak.svg", svg(W, H, f"Current activity streak: {streak} days", b, d,
                           desc=f"{streak} consecutive days with at least one event, plus the last 14 days."))


def build_offline(name, title, accent):
    W, H = 880, 150
    d, b = slab(f"of{name}", 8, 8, W - 16, H - 30, accent, depth=12, rx=20)
    b += f'<text x="34" y="70" font-size="22" font-weight="800" fill="{light(accent, .3)}">{esc(title)}</text>'
    b += f'<text x="34" y="98" font-size="14" fill="{MUTED}">Signal lost — data will return on the next sweep.</text>'
    b += f'<rect class="sw" x="34" y="{H - 62}" width="180" height="3" rx="1.5" fill="{accent}"/>'
    save(name, svg(W, H, title, b, d))


def main() -> int:
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("USERNAME", "omarmetman")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        user = fetch(f"/users/{login}", token)
        repos = fetch(f"/users/{login}/repos?per_page=100&sort=updated", token)
        followers = fetch(f"/users/{login}/followers?per_page=1", token)
        # count via Link header trick is overkill; paginate shallow
        followers_n = len(followers)
        page = 2
        while len(followers) == 100 and page <= 12:
            followers_n += len(fetch(f"/users/{login}/followers?per_page=100&page={page}", token))
            page += 1
        events = []
        for kind in ("PushEvent", "IssuesEvent", "PullRequestEvent", "CreateEvent"):
            try:
                events += fetch(f"/users/{login}/events/public?per_page=100", token)
            except Exception:
                break
        build_overview(user, repos, followers_n, token)
        build_langs(repos)
        build_activity(events)
        build_streak(events)
        return 0
    except urllib.error.HTTPError as e:
        print(f"[telemetry] HTTP {e.code}: {e.reason}")
    except Exception as e:  # noqa: BLE001 - degrade, never break the workflow
        print(f"[telemetry] failed: {e}")
    for name, title, col in (("overview.svg", "ACCOUNT OVERVIEW", VIOLET),
                             ("languages.svg", "CODE COMPOSITION", CYAN),
                             ("activity.svg", "THE PULSE", VIOLET),
                             ("streak.svg", "CURRENT STREAK", AMBER)):
        if not os.path.exists(os.path.join(OUT, name)):
            build_offline(name, title, col)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())