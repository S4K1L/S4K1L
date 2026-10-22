#!/usr/bin/env python3
"""Generates every SVG used by README.md.

    python3 scripts/generate_assets.py               # all assets
    python3 scripts/generate_assets.py --stats-only  # only assets/stats.svg (used by the daily workflow)

Colours follow GitHub's Primer palette and switch with the viewer's light/dark preference.
Stats come straight from the GitHub API (set GITHUB_TOKEN to avoid rate limits).
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
USER = os.environ.get("GITHUB_USER", "S4K1L")

# ---------------------------------------------------------------- theme tokens (CSS variables)
THEME_CSS = """
      :root { --bg:#0d1117; --panel:#161b22; --inset:#010409; --border:#30363d; --text:#e6edf3; --muted:#9198a1; --dim:#6e7681;
              --accent:#4493f8; --green:#3fb950;
              --kw:#ff7b72; --ty:#ffa657; --st:#a5d6ff; --fn:#d2a8ff; --an:#79c0ff; --pn:#9198a1; }
      @media (prefers-color-scheme: light) {
        :root { --bg:#ffffff; --panel:#f6f8fa; --inset:#eaeef2; --border:#d1d9e0; --text:#1f2328; --muted:#59636e; --dim:#818b98;
                --accent:#0969da; --green:#1a7f37;
                --kw:#cf222e; --ty:#953800; --st:#0a3069; --fn:#8250df; --an:#0550ae; --pn:#59636e; }
      }"""
V = lambda n: f"var(--{n})"
BG, PANEL, INSET, BORDER, TXT, MUTED, DIM, ACC, GRN = (V(n) for n in
    ("bg", "panel", "inset", "border", "text", "muted", "dim", "accent", "green"))
KW, TY, ST, FN, AN, PN = (V(n) for n in ("kw", "ty", "st", "fn", "an", "pn"))

# fixed palette for the phone mock-up (a device is dark in either theme)
P_BG, P_CARD, P_BORDER, P_TXT, P_MUT, P_ACC, P_GRN = "#0d1117", "#161b22", "#30363d", "#e6edf3", "#9198a1", "#4493f8", "#3fb950"

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
E = html.escape


# ---------------------------------------------------------------- helpers
def f(x):
    return f"{x:.5f}".rstrip("0").rstrip(".") or "0"


def _merge(default, events):
    pts = [(0.0, default)] + sorted(events, key=lambda e: e[0])
    out = []
    for t, v in pts:
        if out and abs(out[-1][0] - t) < 1e-9:
            out[-1] = (t, v)
        else:
            out.append((t, v))
    if out[-1][0] < 1:
        out.append((1.0, out[-1][1]))
    return out


def anim(attr, default, events, dur):
    """Discrete SMIL animation from (time_fraction, value) events."""
    m = _merge(default, events)
    return (f'<animate attributeName="{attr}" calcMode="discrete" values="{";".join(str(v) for _, v in m)}" '
            f'keyTimes="{";".join(f(t) for t, _ in m)}" dur="{dur}s" repeatCount="indefinite"/>')


def lin(attr, default, events, dur):
    """Linear (interpolated) SMIL animation from (time_fraction, value) events."""
    m = _merge(default, events)
    return (f'<animate attributeName="{attr}" values="{";".join(str(v) for _, v in m)}" '
            f'keyTimes="{";".join(f(t) for t, _ in m)}" dur="{dur}s" repeatCount="indefinite"/>')


def themed(s):
    """Move var(--x) colour attributes into style="" (presentation attributes don't reliably resolve var())."""
    def fix(m):
        decl = []

        def grab(mm):
            decl.append(f"{mm.group(1)}:{mm.group(2)}")
            return ""
        tag = re.sub(r'\s(fill|stroke|stop-color)="(var\(--[\w-]+\))"', grab, m.group(0))
        return re.sub(r'(/?>)$', f' style="{";".join(decl)}"\\1', tag) if decl else tag
    return re.sub(r'<[a-zA-Z][^<>]*>', fix, s)


def svg(w, h, body, defs="", label=""):
    doc = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}">
  <defs>
    <style>{THEME_CSS}
      .m {{ font-family: {MONO}; white-space: pre; }}
      .s {{ font-family: {SANS}; }}
    </style>
{defs}  </defs>
{body}
</svg>
'''
    return themed(doc)


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)


def frame(w, h, fill=None, r=14):
    return (f'<rect width="{w}" height="{h}" rx="{r}" fill="{fill or BG}"/>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" stroke="{BORDER}"/>')


# ---------------------------------------------------------------- hero
def hero():
    W, H, D = 900, 500, 20.0
    CW = 7.8  # 13px monospace advance
    X0, LH, Y1 = 84, 21, 208
    lines = [
        [("class ", KW), ("Shakil ", TY), ("extends ", KW), ("Engineer ", TY), ("{", PN)],
        [("  final ", KW), ("role    ", TXT), ("= ", PN), ("'Software Engineer'", ST), (";", PN)],
        [("  final ", KW), ("city    ", TXT), ("= ", PN), ("'Dhaka, Bangladesh'", ST), (";", PN)],
        [("  final ", KW), ("works   ", TXT), ("= ", PN), ("'OrpheusPLC'", ST), (";", PN)],
        [("  final ", KW), ("mobile  ", TXT), ("= ", PN), ("['Flutter', 'Dart']", ST), (";", PN)],
        [("  final ", KW), ("backend ", TXT), ("= ", PN), ("['Django', 'FastAPI']", ST), (";", PN)],
        [("  final ", KW), ("state   ", TXT), ("= ", PN), ("['BLoC', 'Provider', 'GetX']", ST), (";", PN)],
        [],
        [("  @override", AN)],
        [("  Widget ", TY), ("build", FN), ("(", PN), ("BuildContext ", TY), ("context", TXT), (") {", PN)],
        [("    return ", KW), ("Scaffold", TY), ("(body: ideas.", TXT), ("ship", FN), ("());", PN)],
        [("  }", PN)],
        [("}", PN)],
    ]
    defs, code, gutter, caret_x, caret_y = [], [], [], [], []
    t, DT = 0.02, 0.0019
    for k, toks in enumerate(lines):
        y = Y1 + k * LH
        gutter.append(f'<text class="m" x="64" y="{y}" font-size="12" fill="{DIM}" text-anchor="end">{k + 1}</text>')
        if not toks:
            t += 0.01
            continue
        full = "".join(s for s, _ in toks)
        n = len(full)
        steps = [(t + j * DT, CW * (j + 1)) for j in range(n)]
        defs.append(f'    <clipPath id="c{k}"><rect x="{X0}" y="{y - 15}" height="21" width="{CW * n:.1f}">{anim("width", 0, steps, D)}</rect></clipPath>')
        spans = "".join(f'<tspan fill="{c}">{E(s)}</tspan>' for s, c in toks)
        code.append(f'<g clip-path="url(#c{k})"><text class="m" x="{X0}" y="{y}" font-size="13">{spans}</text></g>')
        for j in range(n + 1):
            caret_x.append((t + j * DT, X0 + CW * j))
            caret_y.append((t + j * DT, y - 13))
        t += n * DT + 0.011
    caret = (f'<rect width="7" height="16" fill="{ACC}" x="{X0}" y="{Y1 - 13}">{anim("x", X0, caret_x, D)}{anim("y", Y1 - 13, caret_y, D)}'
             f'<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # ---- phone (dark device in both themes)
    PX, PY, PW, PH = 640, 30, 232, 440
    SX, SY, SW, SH = PX + 8, PY + 8, PW - 16, PH - 16
    cyc, seg = 4, 0.25

    def show(i):
        s, e = i * seg, (i + 1) * seg
        pts = []
        if i > 0:
            pts += [(s, 0), (s + 0.018, 1)]
        pts += [(e - 0.018, 1), (e, 0)] if i < cyc - 1 else [(e - 0.018, 1)]
        return lin("opacity", 1 if i == 0 else 0, pts, D)

    def status():
        return (f'<text class="s" x="22" y="26" font-size="11" font-weight="600" fill="{P_TXT}">9:41</text>'
                f'<rect x="{SW - 44}" y="17" width="22" height="10" rx="3" fill="none" stroke="{P_MUT}" stroke-width="1"/>'
                f'<rect x="{SW - 42}" y="19" width="15" height="6" rx="1.5" fill="{P_MUT}"/>')

    def head(title, sub):
        return (status() + f'<text class="s" x="20" y="68" font-size="20" font-weight="700" fill="{P_TXT}">{title}</text>'
                f'<text class="m" x="20" y="86" font-size="10" fill="{P_MUT}">{sub}</text>')

    s1 = [f'<rect width="{SW}" height="{SH}" fill="{P_BG}"/>', head("Checkout", "Universal POS")]
    for r, (nm, pr) in enumerate([("Sofa cover", "42.00"), ("Table lamp", "18.50"), ("Cushion x2", "24.00")]):
        y = 106 + r * 54
        s1.append(f'<rect x="16" y="{y}" width="{SW - 32}" height="44" rx="10" fill="{P_CARD}" stroke="{P_BORDER}"/>'
                  f'<rect x="26" y="{y + 10}" width="24" height="24" rx="6" fill="{P_BORDER}"/>'
                  f'<text class="s" x="60" y="{y + 20}" font-size="12.5" font-weight="600" fill="{P_TXT}">{nm}</text>'
                  f'<text class="m" x="60" y="{y + 34}" font-size="10" fill="{P_MUT}">in stock</text>'
                  f'<text class="m" x="{SW - 26}" y="{y + 27}" font-size="12" fill="{P_TXT}" text-anchor="end">${pr}</text>')
    s1 += [f'<line x1="16" y1="280" x2="{SW - 16}" y2="280" stroke="{P_BORDER}" stroke-dasharray="3 4"/>',
           f'<text class="s" x="20" y="312" font-size="12" fill="{P_MUT}">Total</text>',
           f'<text class="s" x="{SW - 20}" y="314" font-size="22" font-weight="700" fill="{P_TXT}" text-anchor="end">$84.50</text>',
           f'<rect x="16" y="340" width="{SW - 32}" height="46" rx="12" fill="{P_ACC}"/>',
           f'<text class="s" x="{SW / 2}" y="368" font-size="14" font-weight="600" fill="#ffffff" text-anchor="middle">Pay now</text>']

    s2 = [f'<rect width="{SW}" height="{SH}" fill="{P_BG}"/>', head("Breathe", "Kunchi Hidup")]
    for i in range(7):
        r = 78 - i * 10
        s2.append(f'<circle cx="{SW / 2}" cy="215" r="{r}" fill="none" stroke="{P_ACC}" stroke-width="3" opacity="{0.95 - i * 0.12:.2f}">'
                  f'<animate attributeName="r" values="{r};{r + 6};{r}" dur="4s" begin="{i * 0.12:.2f}s" repeatCount="indefinite"/></circle>')
    s2 += [f'<text class="s" x="{SW / 2}" y="215" font-size="13" font-weight="600" fill="{P_TXT}" text-anchor="middle" dominant-baseline="middle">'
           f'<animate attributeName="opacity" values="1;0.25;1" dur="4s" repeatCount="indefinite"/>in / out</text>',
           f'<rect x="16" y="340" width="{SW - 32}" height="46" rx="12" fill="{P_CARD}" stroke="{P_BORDER}"/>',
           f'<text class="s" x="{SW / 2}" y="368" font-size="13" font-weight="600" fill="{P_TXT}" text-anchor="middle">Begin session</text>']

    s3 = [f'<rect width="{SW}" height="{SH}" fill="{P_BG}"/>', head("Lesson 3", "TheClue / crypto"),
          f'<rect x="16" y="104" width="{SW - 32}" height="170" rx="12" fill="{P_CARD}" stroke="{P_BORDER}"/>',
          f'<polyline points="16,250 46,232 76,240 106,205 136,214 166,176 196,150" fill="none" stroke="{P_ACC}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" '
          f'stroke-dasharray="320" stroke-dashoffset="320"><animate attributeName="stroke-dashoffset" values="320;0;0;320" keyTimes="0;0.5;0.9;1" dur="5s" repeatCount="indefinite"/></polyline>']
    for i in range(16):
        x = 22 + i * 12.5
        hs = [10 + (i * 7) % 24, 30 - (i * 5) % 20, 14 + (i * 11) % 26, 8 + (i * 3) % 22, 10 + (i * 7) % 24]
        dur = f"{1.1 + (i % 4) * 0.15:.2f}"
        s3.append(f'<rect x="{x:.1f}" width="6" rx="3" fill="{P_ACC}" opacity="0.85">'
                  f'<animate attributeName="y" values="{";".join(f(310 - h / 2) for h in hs)}" dur="{dur}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="height" values="{";".join(f(h) for h in hs)}" dur="{dur}s" repeatCount="indefinite"/></rect>')
    s3 += [f'<circle cx="{SW / 2}" cy="368" r="20" fill="{P_ACC}"/>',
           f'<path d="M {SW / 2 - 5} 359 L {SW / 2 + 9} 368 L {SW / 2 - 5} 377 Z" fill="#ffffff"/>']

    s4 = [f'<rect width="{SW}" height="{SH}" fill="{P_BG}"/>', head("re:", "feed")]
    for r in range(2):
        y = 100 + r * 108
        s4.append(f'<rect x="16" y="{y}" width="{SW - 32}" height="98" rx="12" fill="{P_CARD}" stroke="{P_BORDER}"/>'
                  f'<circle cx="38" cy="{y + 24}" r="11" fill="{[P_ACC, P_BORDER][r]}"/>'
                  f'<rect x="58" y="{y + 15}" width="70" height="7" rx="3.5" fill="{P_BORDER}"/>'
                  f'<rect x="58" y="{y + 28}" width="44" height="6" rx="3" fill="{P_BORDER}" opacity="0.6"/>'
                  f'<rect x="28" y="{y + 50}" width="{SW - 56}" height="7" rx="3.5" fill="{P_BORDER}" opacity="0.8"/>'
                  f'<rect x="28" y="{y + 64}" width="{SW - 100}" height="7" rx="3.5" fill="{P_BORDER}" opacity="0.8"/>'
                  f'<circle cx="34" cy="{y + 86}" r="4" fill="none" stroke="{P_MUT}" stroke-width="1.5"/>')
    s4.append(f'<rect x="16" y="326" width="108" height="30" rx="15" fill="{P_CARD}" stroke="{P_BORDER}"/>')
    for i in range(3):
        s4.append(f'<circle cx="{42 + i * 16}" cy="341" r="3.5" fill="{P_ACC}"><animate attributeName="opacity" values="0.25;1;0.25" '
                  f'dur="1.2s" begin="{i * 0.2:.1f}s" repeatCount="indefinite"/></circle>')

    screens = "\n".join(f'<g transform="translate({SX},{SY})" clip-path="url(#scr)" opacity="{1 if i == 0 else 0}">{show(i)}{"".join(s)}</g>'
                        for i, s in enumerate([s1, s2, s3, s4]))
    defs.append(f'    <clipPath id="scr"><rect width="{SW}" height="{SH}" rx="30"/></clipPath>')
    defs.append('    <clipPath id="ed"><rect x="30" y="140" width="568" height="332" rx="10"/></clipPath>')

    dots = "".join(f'<circle cx="{50 + i * 16}" cy="158" r="4.5" fill="{DIM}" opacity="0.45"/>' for i in range(3))
    body = f'''  {frame(W, H, r=14)}
  <text class="m" x="30" y="46" font-size="12" fill="{DIM}">~/github/<tspan fill="{ACC}">S4K1L</tspan></text>
  <text class="s" x="30" y="92" font-size="40" font-weight="700" fill="{TXT}">Shakil Mahmud</text>
  <text class="m" x="30" y="120" font-size="14" fill="{MUTED}">Software Engineer  /  Dhaka  /  OrpheusPLC</text>

  <rect x="30" y="140" width="568" height="332" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <g clip-path="url(#ed)"><rect x="30" y="140" width="568" height="36" fill="{INSET}"/></g>
  <line x1="30" y1="176" x2="598" y2="176" stroke="{BORDER}"/>
  {dots}
  <text class="m" x="124" y="163" font-size="12" fill="{TXT}">shakil.dart</text>
  <rect x="118" y="174" width="92" height="2" fill="{ACC}"/>
  <line x1="74" y1="176" x2="74" y2="472" stroke="{BORDER}"/>
  {"".join(gutter)}
  {"".join(code)}
  {caret}

  <rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="38" fill="#010409" stroke="#30363d" stroke-width="2"/>
  {screens}
  <rect x="{PX + PW / 2 - 34}" y="{PY + 13}" width="68" height="17" rx="8.5" fill="#010409"/>'''
    write("hero.svg", svg(W, H, body, "\n".join(defs) + "\n", "Shakil Mahmud, Software Engineer: a Dart class describing him next to a phone cycling through POS, wellness, crypto and social apps"))


# ---------------------------------------------------------------- project cards
def ic(x, y, inner):
    return f'<g transform="translate({x},{y})" fill="none" stroke="{ACC}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{inner}</g>'


def icon_pos(x, y):
    return ic(x, y, f'<path d="M6 2 H46 V50 L40 46 L34 50 L28 46 L22 50 L16 46 L10 50 L6 48 Z"/>'
              f'<path d="M14 14 H38 M14 24 H30 M14 34 H34" stroke="{MUTED}"/>'
              f'<path d="M14 42 H22" stroke="{ACC}"><animate attributeName="d" values="M14 42 H18;M14 42 H34;M14 42 H18" dur="2.6s" repeatCount="indefinite"/></path>')


def icon_nexora(x, y):
    return ic(x, y, f'<rect x="3" y="30" width="22" height="20" rx="3"/><rect x="29" y="30" width="22" height="20" rx="3"/>'
              f'<rect x="16" y="6" width="22" height="20" rx="3" fill="{ACC}" fill-opacity="0.15"><animate attributeName="y" values="6;2;6" dur="2.4s" repeatCount="indefinite"/></rect>')


def icon_kunchi(x, y):
    rings = "".join(f'<circle cx="27" cy="27" r="{25 - i * 5}" opacity="{1 - i * 0.17:.2f}"><animate attributeName="r" values="{25 - i * 5};{27 - i * 5};{25 - i * 5}" dur="3s" begin="{i * 0.15:.2f}s" repeatCount="indefinite"/></circle>' for i in range(5))
    return ic(x, y, rings)


def icon_clue(x, y):
    return ic(x, y, f'<ellipse cx="27" cy="27" rx="24" ry="24"><animate attributeName="rx" values="24;4;24" dur="3s" repeatCount="indefinite"/></ellipse>'
              f'<path d="M33 20 A9 9 0 1 0 33 34" stroke-width="2.2"><animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="3s" repeatCount="indefinite"/></path>')


def icon_re(x, y):
    dots = "".join(f'<circle cx="{14 + i * 9}" cy="18" r="2.4" fill="{ACC}" stroke="none"><animate attributeName="opacity" values="0.25;1;0.25" dur="1.2s" begin="{i * 0.2:.1f}s" repeatCount="indefinite"/></circle>' for i in range(3))
    return ic(x, y, f'<rect x="2" y="4" width="40" height="28" rx="9"/><path d="M12 32 L10 44 L22 32"/>{dots}')


def icon_grid(x, y):
    sq = "".join(f'<rect x="{c * 19}" y="{r * 19}" width="14" height="14" rx="3" fill="{ACC}" fill-opacity="0.18"><animate attributeName="fill-opacity" values="0.1;0.5;0.1" dur="3.2s" begin="{(r * 3 + c) * 0.18:.2f}s" repeatCount="indefinite"/></rect>' for r in range(3) for c in range(3))
    return ic(x, y + 2, sq)


def card(fname, name, lines, tags, icon, cta, label):
    W, H = 440, 168
    desc = "".join(f'<text class="s" x="24" y="{68 + i * 18}" font-size="12.5" fill="{MUTED}">{E(l)}</text>' for i, l in enumerate(lines))
    px, pills = 24, ""
    for t in tags:
        w = len(t) * 6.9 + 20
        pills += (f'<rect x="{px:.0f}" y="124" width="{w:.0f}" height="24" rx="12" fill="none" stroke="{BORDER}"/>'
                  f'<text class="m" x="{px + w / 2:.0f}" y="140" font-size="11" fill="{MUTED}" text-anchor="middle">{E(t)}</text>')
        px += w + 8
    body = f'''  {frame(W, H, PANEL, 12)}
  <text class="s" x="24" y="40" font-size="20" font-weight="700" fill="{TXT}">{E(name)}</text>
  {desc}
  {pills}
  {icon(366, 24)}
  <text class="m" x="{W - 22}" y="140" font-size="11.5" fill="{ACC if cta != 'private' else DIM}" text-anchor="end">{E(cta)}</text>'''
    write(fname, svg(W, H, body, "", label))


# ---------------------------------------------------------------- BLoC diagram
def bloc():
    W, H, D = 900, 372, 12.0
    bw, bh, by = 170, 116, 92
    ux, bx, rx_ = 30, 365, 700
    yt, yb = 130, 184
    nodes = [("UI", ["Widgets"], ux), ("BLoC", ["events → states"], bx), ("Repository", ["Django · FastAPI", "Firebase · Supabase"], rx_)]
    body = [frame(W, H, PANEL, 14),
            f'<text class="m" x="30" y="42" font-size="12" fill="{DIM}">checkout flow, traced through the layers</text>']
    seg = [(ux + bw, bx, yt, "ScanItem(sku)", "event", 0.04, 0.20, ACC),
           (bx + bw, rx_, yt, "GET /products/42", "request", 0.24, 0.40, ACC),
           (rx_, bx + bw, yb, "Product(...)", "data", 0.44, 0.60, GRN),
           (bx, ux + bw, yb, "CartUpdated(total)", "state", 0.64, 0.80, GRN)]
    for i, (x1, x2, y, lab, sub, s, e, col) in enumerate(seg):
        body.append(f'<path id="p{i}" d="M {x1} {y} L {x2} {y}" fill="none" stroke="{BORDER}" stroke-width="2" stroke-dasharray="5 5"/>')
        a = x2 - 8 if x2 > x1 else x2 + 8
        body.append(f'<path d="M {a} {y - 5} L {x2} {y} L {a} {y + 5}" fill="none" stroke="{DIM}" stroke-width="2"/>')
        mid, ly = (x1 + x2) / 2, (y - 12 if y == yt else y + 24)
        body.append(f'<g opacity="0.4">{lin("opacity", 0.4, [(s, 0.4), (s + 0.02, 1), (e + 0.1, 1), (e + 0.14, 0.4)], D)}'
                    f'<text class="m" x="{mid}" y="{ly}" font-size="11.5" font-weight="700" fill="{col}" text-anchor="middle">{E(lab)}</text>'
                    f'<text class="m" x="{mid}" y="{ly + (-14 if y == yt else 14)}" font-size="9.5" fill="{DIM}" text-anchor="middle">{sub}</text></g>')
        body.append(f'<circle r="5.5" fill="{col}" opacity="0">'
                    f'<animateMotion dur="{D}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{f(s)};{f(e)};1" calcMode="linear"><mpath href="#p{i}"/></animateMotion>'
                    f'{anim("opacity", 0, [(s, 1), (e + 0.001, 0)], D)}</circle>')
    lights = {0: [(0.64, 0.86)], 1: [(0.04, 0.2), (0.44, 0.6)], 2: [(0.24, 0.4)]}
    for idx, (nm, subs, x) in enumerate(nodes):
        ev = []
        for s, e in lights[idx]:
            ev += [(s, 1), (e + 0.06, 0)]
        body.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>'
                    f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="none" stroke="{ACC}" stroke-width="2" opacity="0">{anim("opacity", 0, ev, D)}</rect>'
                    f'<text class="s" x="{x + bw / 2}" y="{by + 40}" font-size="20" font-weight="700" fill="{TXT}" text-anchor="middle">{nm}</text>')
        for j, sub in enumerate(subs):
            body.append(f'<text class="m" x="{x + bw / 2}" y="{by + 66 + j * 17}" font-size="10.5" fill="{MUTED}" text-anchor="middle">{E(sub)}</text>')
    for i, (n, t) in enumerate([("01", "the UI only sends events"), ("02", "the BLoC owns the logic"), ("03", "data stays behind a repository")]):
        x = 30 + i * 290
        body.append(f'<text class="m" x="{x}" y="296" font-size="12" font-weight="700" fill="{ACC}">{n}</text>'
                    f'<text class="s" x="{x + 28}" y="296" font-size="14" font-weight="600" fill="{TXT}">{E(t)}</text>')
    body.append(f'<text class="m" x="30" y="334" font-size="12" fill="{DIM}">events go in, immutable states come out. every screen is a function of the latest state.</text>')
    write("bloc.svg", svg(W, H, "\n".join(body), "", "BLoC data flow: the UI sends an event to the BLoC, which calls a repository, gets data back and emits a new state to the UI"))


# ---------------------------------------------------------------- widget tree
def tree():
    W, D = 900, 16.0
    rows = [("languages", ["Dart", "Python", "C", "C++"]),
            ("mobile", ["Flutter"]),
            ("state", ["BLoC", "Provider", "GetX"]),
            ("backend", ["Django", "FastAPI", "REST APIs"]),
            ("cloud", ["Firebase", "Supabase"]),
            ("design", ["Figma", "Material Design"]),
            ("fundamentals", ["Data Structures", "Algorithms", "OOP"]),
            ("tooling", ["VS Code", "Android Studio", "Git", "GitHub"])]
    RH, Y0 = 38, 100
    H = Y0 + len(rows) * RH + 22
    body = [frame(W, H, PANEL, 14),
            f'<text class="m" x="30" y="40" font-size="12" fill="{DIM}">widget inspector</text>',
            f'<line x1="0" y1="56" x2="{W}" y2="56" stroke="{BORDER}"/>',
            f'<rect x="30" y="71" width="13" height="13" rx="3" fill="{ACC}"/>',
            f'<text class="m" x="54" y="82" font-size="14" font-weight="700" fill="{TXT}">ShakilApp</text>'
            f'<text class="m" x="140" y="82" font-size="12" fill="{DIM}">( stack )</text>']
    last_y = Y0 + (len(rows) - 1) * RH + 6
    body.append(f'<line x1="37" y1="90" x2="37" y2="{last_y}" stroke="{BORDER}" stroke-width="1.5"/>')
    for i, (key, chips) in enumerate(rows):
        cy = Y0 + i * RH + 6
        t = 0.04 + i * 0.06
        g = [f'<line x1="37" y1="{cy}" x2="60" y2="{cy}" stroke="{BORDER}" stroke-width="1.5"/>',
             f'<rect x="64" y="{cy - 4}" width="8" height="8" rx="2" fill="{MUTED}"/>',
             f'<text class="m" x="84" y="{cy + 4}" font-size="13" font-weight="700" fill="{ACC}">{key}:</text>']
        x = 232
        for c in chips:
            w = len(c) * 7.4 + 24
            g.append(f'<rect x="{x:.0f}" y="{cy - 12}" width="{w:.0f}" height="24" rx="12" fill="{BG}" stroke="{BORDER}"/>'
                     f'<text class="m" x="{x + w / 2:.0f}" y="{cy + 4}" font-size="12" fill="{TXT}" text-anchor="middle">{E(c)}</text>')
            x += w + 10
        body.append(f'<g>{lin("opacity", 0, [(t, 0), (t + 0.03, 1), (0.94, 1), (0.98, 0)], D)}'
                    f'<animateTransform attributeName="transform" type="translate" calcMode="linear" values="-14 0;-14 0;0 0;0 0" '
                    f'keyTimes="0;{f(t)};{f(t + 0.03)};1" dur="{D}s" repeatCount="indefinite"/>{"".join(g)}</g>')
    write("tree.svg", svg(W, H, "\n".join(body), "", "Skill stack as a widget tree: languages, mobile, state management, backend, cloud, design, fundamentals, tooling"))


# ---------------------------------------------------------------- stats (live from GitHub API)
FALLBACK = {"repos": 66, "followers": 13, "stars": 11, "since": 2022,
            "langs": [("Dart", 46), ("C++", 7), ("Python", 3), ("TypeScript", 1), ("Java", 1)],
            "recent": [("Universal-POS", "Oct 2026"), ("Universal-POS-Backend", "Oct 2026"), ("Shakil-Portfolio", "Sep 2026"), ("Breath-App---Webview", "Aug 2026")]}
LANG_COL = {"Dart": "#00B4AB", "C++": "#f34b7d", "Python": "#3572A5", "Java": "#b07219", "TypeScript": "#3178c6",
            "C": "#8b949e", "Kotlin": "#A97BFF", "JavaScript": "#f1e05a"}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_stats():
    try:
        u = api(f"/users/{USER}")
        repos, page = [], 1
        while True:
            chunk = api(f"/users/{USER}/repos?per_page=100&page={page}&sort=pushed")
            repos += chunk
            if len(chunk) < 100:
                break
            page += 1
        own = [r for r in repos if not r["fork"]]
        counts = {}
        for r in own:
            if r["language"]:
                counts[r["language"]] = counts.get(r["language"], 0) + 1
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        recent = [(r["name"], f'{months[int(r["pushed_at"][5:7]) - 1]} {r["pushed_at"][:4]}') for r in own if r["name"] != USER][:4]
        return {"repos": u["public_repos"], "followers": u["followers"], "stars": sum(r["stargazers_count"] for r in own),
                "since": int(u["created_at"][:4]), "langs": sorted(counts.items(), key=lambda kv: -kv[1]), "recent": recent}
    except Exception as exc:  # network / rate limit: leave the previous file alone
        print("stats fetch failed:", exc, file=sys.stderr)
        return None


def stats(data):
    W, H = 900, 330
    langs = data["langs"][:5]
    other = sum(n for _, n in data["langs"][5:])
    if other:
        langs.append(("Other", other))
    total = sum(n for _, n in langs) or 1
    col = lambda n: LANG_COL.get(n, "#8b949e")
    tiles = [(str(data["repos"]), "public repos"), (str(data["stars"]), "stars earned"), (str(data["followers"]), "followers"),
             (f'{max(1, datetime.date.today().year - data["since"])} yrs', "building on GitHub")]
    body = [frame(W, H, PANEL, 14)]
    tw, gap = 201, 12
    for i, (v, l) in enumerate(tiles):
        x = 30 + i * (tw + gap)
        body.append(f'<rect x="{x}" y="28" width="{tw}" height="88" rx="10" fill="{BG}" stroke="{BORDER}"/>'
                    f'<text class="s" x="{x + 20}" y="74" font-size="32" font-weight="700" fill="{TXT}">{v}</text>'
                    f'<text class="m" x="{x + 20}" y="98" font-size="11" fill="{DIM}">{l}</text>')
    body.append(f'<text class="m" x="30" y="150" font-size="12" fill="{DIM}">primary language per repo</text>')
    x, bar = 30, ""
    for name, n in langs:
        w = 840 * n / total
        bar += f'<rect x="{x:.1f}" y="160" width="{max(w, 2):.1f}" height="12" fill="{col(name)}"/>'
        x += w
    defs = '    <clipPath id="wipe"><rect x="30" y="160" height="12" width="840" rx="6"><animate attributeName="width" from="0" to="840" dur="1.4s" fill="freeze"/></rect></clipPath>\n'
    body.append(f'<rect x="30" y="160" width="840" height="12" rx="6" fill="{BORDER}"/><g clip-path="url(#wipe)">{bar}</g>')
    lx = 30
    for name, n in langs:
        label = f"{name}  {round(100 * n / total)}%"
        body.append(f'<circle cx="{lx + 5}" cy="196" r="5" fill="{col(name)}"/><text class="m" x="{lx + 16}" y="200" font-size="11.5" fill="{MUTED}">{E(label)}</text>')
        lx += 16 + len(label) * 7 + 22
    body.append(f'<text class="m" x="30" y="242" font-size="12" fill="{DIM}">recently pushed</text>')
    for i, (nm, when) in enumerate(data["recent"]):
        x0, y0 = 30 + (i % 2) * 435, 254 + (i // 2) * 34
        nm_s = nm if len(nm) <= 30 else nm[:29] + "~"
        body.append(f'<circle cx="{x0 + 5}" cy="{y0 + 12}" r="3.5" fill="{GRN}"/>'
                    f'<text class="m" x="{x0 + 18}" y="{y0 + 16}" font-size="12.5" fill="{TXT}">{E(nm_s)}</text>'
                    f'<text class="m" x="{x0 + 410}" y="{y0 + 16}" font-size="11" fill="{DIM}" text-anchor="end">{when}</text>')
    write("stats.svg", svg(W, H, "\n".join(body), defs, f"GitHub numbers for {USER}: {data['repos']} repos, language mix and recent pushes"))


# ---------------------------------------------------------------- buttons
def button(fname, kind, label):
    W, H = 188, 44
    icons = {
        "globe": '<circle cx="0" cy="0" r="8"/><ellipse cx="0" cy="0" rx="3.4" ry="8"/><path d="M-8 0 H8"/>',
        "in": '<rect x="-8" y="-8" width="16" height="16" rx="3"/><path d="M-4 -1 V4 M-4 -4.5 V-4.4 M0 4 V-1 M0 1 C0 -2 5 -2 5 1 V4"/>',
        "doc": '<path d="M-6 -9 H3 L7 -5 V9 H-6 Z"/><path d="M3 -9 V-5 H7 M-3 0 H4 M-3 4 H4"/>',
        "mail": '<rect x="-9" y="-6.5" width="18" height="13" rx="2.5"/><path d="M-9 -5 L0 2 L9 -5"/>',
    }
    body = f'''  {frame(W, H, PANEL, 22)}
  <g transform="translate(28,22)" fill="none" stroke="{ACC}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icons[kind]}</g>
  <text class="s" x="52" y="27" font-size="14" font-weight="600" fill="{TXT}">{E(label)}</text>'''
    write(fname, svg(W, H, body, "", label))


# ---------------------------------------------------------------- main
def main():
    only_stats = "--stats-only" in sys.argv
    data = fetch_stats()
    if only_stats:
        if data:
            stats(data)
            print("stats.svg refreshed")
        return
    d = data or FALLBACK
    hero()
    card("card-pos.svg", "Universal POS", ["One point of sale for furniture, supershop,", "cosmetic and local stores. The business type", "decides which features switch on."],
         ["Flutter", "Python", "POS"], icon_pos, "repo →", "Universal POS")
    card("card-nexora.svg", "Nexora", ["Inventory and point-of-sale for small retail", "businesses. Stock in, sales out."],
         ["Flutter", "Inventory", "POS"], icon_nexora, "repo →", "Nexora")
    card("card-kunchi.svg", "Kunchi Hidup", ["A chakra-based emotional wellbeing app with", "an AI companion that helps steady your mood."],
         ["Flutter", "AI", "Wellbeing"], icon_kunchi, "repo →", "Kunchi Hidup")
    card("card-clue.svg", "TheClue", ["Crypto education app with an audio engine", "at its core."],
         ["Flutter", "Audio", "Education"], icon_clue, "repo →", "TheClue")
    card("card-re.svg", "re:", ["A social media app.", "Private repository."],
         ["Flutter", "Social"], icon_re, "private", "re: social media app")
    card("card-all.svg", f"All {d['repos']} repos", ["Mobile apps, IoT builds and C++ experiments,", "from RFID gates to robo-soccer."],
         ["Dart", "C++", "Python"], icon_grid, "browse →", "All repositories")
    bloc()
    tree()
    stats(d)
    button("btn-portfolio.svg", "globe", "Portfolio")
    button("btn-linkedin.svg", "in", "LinkedIn")
    button("btn-resume.svg", "doc", "Resume")
    button("btn-email.svg", "mail", "Email me")
    print("generated", len(os.listdir(OUT)), "files in", OUT)


if __name__ == "__main__":
    main()
