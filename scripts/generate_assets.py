#!/usr/bin/env python3
"""Generates every SVG used by README.md.

    python3 scripts/generate_assets.py               # all assets
    python3 scripts/generate_assets.py --stats-only  # only assets/stats.svg (used by the daily workflow)

Stats come straight from the GitHub API (set GITHUB_TOKEN to avoid rate limits).
No third-party image services are involved.
"""
import datetime
import html
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
USER = os.environ.get("GITHUB_USER", "S4K1L")

# ---------------------------------------------------------------- palette
BG, PANEL, PANEL2, BORDER = "#0B0F19", "#111827", "#0D1321", "#1F2937"
TXT, MUTED, DIM = "#E6EDF3", "#9CA3AF", "#6B7280"
VIOLET, BLUE, MINT = "#8C74FF", "#54C5F8", "#5EEAD4"
OK = "#3FB950"
KW, TY, ST, FN, PL, PN, AN = "#C792EA", "#FFCB6B", "#C3E88D", "#82AAFF", "#D6DEEB", "#89DDFF", "#F78C6C"
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


def anim(attr, default, events, dur, extra=""):
    """Discrete animation from (time_fraction, value) events."""
    m = _merge(default, events)
    return (f'<animate attributeName="{attr}" calcMode="discrete" values="{";".join(str(v) for _, v in m)}" '
            f'keyTimes="{";".join(f(t) for t, _ in m)}" dur="{dur}s" repeatCount="indefinite"{extra}/>')


def lin(attr, default, events, dur):
    """Linear (interpolated) animation from (time_fraction, value) events."""
    m = _merge(default, events)
    return (f'<animate attributeName="{attr}" values="{";".join(str(v) for _, v in m)}" '
            f'keyTimes="{";".join(f(t) for t, _ in m)}" dur="{dur}s" repeatCount="indefinite"/>')


def svg(w, h, body, defs="", label=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{VIOLET}"/><stop offset="55%" stop-color="{BLUE}"/><stop offset="100%" stop-color="{MINT}"/>
    </linearGradient>
    <linearGradient id="gv" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{VIOLET}"/><stop offset="100%" stop-color="{BLUE}"/>
    </linearGradient>
    <linearGradient id="comet" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{BLUE}" stop-opacity="0"/><stop offset="100%" stop-color="{BLUE}" stop-opacity="1"/>
    </linearGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#ffffff" stroke-opacity="0.035" stroke-width="1"/>
    </pattern>
    <style>
      .m {{ font-family: {MONO}; white-space: pre; }}
      .s {{ font-family: {SANS}; }}
    </style>
{defs}  </defs>
{body}
</svg>
'''


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------- hero
def hero():
    W, H, D = 900, 484, 20.0
    CW = 7.8  # 13px monospace advance
    X0, LH, Y1 = 84, 22, 200
    lines = [
        [("class ", KW), ("Shakil ", TY), ("extends ", KW), ("Developer ", TY), ("{", PN)],
        [("  final ", KW), ("role  ", PL), ("= ", PN), ("'Flutter Developer'", ST), (";", PN)],
        [("  final ", KW), ("city  ", PL), ("= ", PN), ("'Dhaka, Bangladesh'", ST), (";", PN)],
        [("  final ", KW), ("works ", PL), ("= ", PN), ("'OrpheusPLC'", ST), (";", PN)],
        [("  final ", KW), ("state ", PL), ("= ", PN), ("BLoC", TY), ("();", PN)],
        [("  final ", KW), ("loves ", PL), ("= ", PN), ("[", PN), ("'Dart'", ST), (", ", PN), ("'Python'", ST),
         (", ", PN), ("'C++'", ST), ("];", PN)],
        [],
        [("  @override", AN)],
        [("  Widget ", TY), ("build", FN), ("(", PN), ("BuildContext ", TY), ("context", PL), (") {", PN)],
        [("    return ", KW), ("Scaffold", TY), ("(body: ideas.", PL), ("ship", FN), ("());", PN)],
        [("  }", PN)],
        [("}", PN)],
    ]
    defs, code, gutter, caret_x, caret_y = [], [], [], [], []
    t = 0.02
    DT = 0.0021
    for k, toks in enumerate(lines):
        y = Y1 + k * LH
        gutter.append(f'<text class="m" x="64" y="{y}" font-size="12" fill="#3B4658" text-anchor="end">{k + 1}</text>')
        if not toks:
            t += 0.01
            continue
        full = "".join(s for s, _ in toks)
        indent = len(full) - len(full.lstrip(" "))
        n = len(full)
        steps = [(t + j * DT, CW * (j + 1)) for j in range(n)]
        defs.append(f'    <clipPath id="c{k}"><rect x="{X0}" y="{y - 16}" height="22" width="{CW * n:.1f}">{anim("width", 0, steps, D)}</rect></clipPath>')
        spans = []
        first = True
        for s, c in toks:
            spans.append(f'<tspan fill="{c}">{E(s)}</tspan>')
        code.append(f'<g clip-path="url(#c{k})"><text class="m" x="{X0}" y="{y}" font-size="13">{"".join(spans)}</text></g>')
        for j in range(n + 1):
            caret_x.append((t + j * DT, X0 + CW * j))
            caret_y.append((t + j * DT, y - 13))
        t += n * DT + 0.012
    caret = (f'<rect width="8" height="17" fill="{BLUE}" x="{X0}" y="{Y1 - 13}">{anim("x", X0, caret_x, D)}{anim("y", Y1 - 13, caret_y, D)}'
             f'<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # ---- phone
    PX, PY, PW, PH = 640, 22, 232, 440
    SX, SY, SW, SH = PX + 8, PY + 8, PW - 16, PH - 16
    cyc = 4
    seg = 1.0 / cyc

    def show(i):
        s, e = i * seg, (i + 1) * seg
        pts = []
        if i > 0:
            pts += [(s, 0), (s + 0.018, 1)]
        pts += [(e - 0.018, 1), (e, 0)] if i < cyc - 1 else [(e - 0.018, 1)]
        return lin("opacity", 1 if i == 0 else 0, pts, D)

    def status():
        return (f'<text class="s" x="22" y="26" font-size="11" font-weight="700" fill="{TXT}">9:41</text>'
                f'<rect x="{SW - 44}" y="17" width="22" height="10" rx="3" fill="none" stroke="{MUTED}" stroke-width="1"/>'
                f'<rect x="{SW - 42}" y="19" width="15" height="6" rx="1.5" fill="{OK}"/>')

    # screen 1: POS checkout
    rows = [("Sofa cover", "42.00"), ("Table lamp", "18.50"), ("Cushion x2", "24.00")]
    s1 = [f'<rect width="{SW}" height="{SH}" fill="#0F172A"/>', status(),
          f'<text class="s" x="20" y="66" font-size="19" font-weight="800" fill="{TXT}">Checkout</text>',
          f'<text class="m" x="20" y="84" font-size="10" fill="{DIM}">Universal POS</text>']
    for r, (nm, pr) in enumerate(rows):
        y = 104 + r * 52
        s1.append(f'<g><rect x="16" y="{y}" width="{SW - 32}" height="42" rx="10" fill="#172033"/>'
                  f'<rect x="26" y="{y + 9}" width="24" height="24" rx="6" fill="url(#gv)" opacity="0.85"/>'
                  f'<text class="s" x="60" y="{y + 20}" font-size="12.5" font-weight="600" fill="{TXT}">{nm}</text>'
                  f'<text class="m" x="60" y="{y + 34}" font-size="10" fill="{DIM}">in stock</text>'
                  f'<text class="m" x="{SW - 26}" y="{y + 26}" font-size="12" fill="{TXT}" text-anchor="end">${pr}</text></g>')
    s1 += [f'<line x1="16" y1="270" x2="{SW - 16}" y2="270" stroke="{BORDER}" stroke-dasharray="3 4"/>',
           f'<text class="s" x="20" y="302" font-size="12" fill="{MUTED}">Total</text>',
           f'<text class="s" x="{SW - 20}" y="304" font-size="22" font-weight="800" fill="{TXT}" text-anchor="end">$84.50</text>',
           f'<rect x="16" y="330" width="{SW - 32}" height="46" rx="14" fill="url(#g)">'
           f'<animate attributeName="opacity" values="1;0.75;1" dur="2s" repeatCount="indefinite"/></rect>',
           f'<text class="s" x="{SW / 2}" y="358" font-size="14" font-weight="800" fill="#06101C" text-anchor="middle">Pay now</text>',
           f'<rect x="16" y="98" width="{SW - 32}" height="2" fill="{BLUE}" opacity="0.7">'
           f'<animate attributeName="y" values="98;250;98" dur="3.2s" repeatCount="indefinite"/></rect>']

    # screen 2: wellness rings
    chakra = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#3B82F6", "#6366F1", "#A855F7"]
    s2 = [f'<rect width="{SW}" height="{SH}" fill="#140F2A"/>', status(),
          f'<text class="s" x="20" y="66" font-size="19" font-weight="800" fill="{TXT}">Breathe</text>',
          f'<text class="m" x="20" y="84" font-size="10" fill="{DIM}">Kunchi Hidup</text>']
    for i, c in enumerate(chakra):
        r = 78 - i * 10
        s2.append(f'<circle cx="{SW / 2}" cy="205" r="{r}" fill="none" stroke="{c}" stroke-width="5" opacity="0.9">'
                  f'<animate attributeName="r" values="{r};{r + 7};{r}" dur="4s" begin="{i * 0.12:.2f}s" repeatCount="indefinite"/></circle>')
    s2 += [f'<text class="s" x="{SW / 2}" y="205" font-size="13" font-weight="700" fill="{TXT}" text-anchor="middle" dominant-baseline="middle">'
           f'<animate attributeName="opacity" values="1;0.2;1" dur="4s" repeatCount="indefinite"/>in . out</text>',
           f'<rect x="16" y="330" width="{SW - 32}" height="46" rx="14" fill="#1E1740" stroke="#3B2F78"/>',
           f'<text class="s" x="{SW / 2}" y="358" font-size="13" font-weight="700" fill="#C4B5FD" text-anchor="middle">Begin session</text>']

    # screen 3: crypto lesson with waveform
    pts = "16,250 46,232 76,240 106,205 136,214 166,176 196,150"
    s3 = [f'<rect width="{SW}" height="{SH}" fill="#0A1120"/>', status(),
          f'<text class="s" x="20" y="66" font-size="19" font-weight="800" fill="{TXT}">Lesson 3</text>',
          f'<text class="m" x="20" y="84" font-size="10" fill="{DIM}">TheClue . crypto</text>',
          f'<rect x="16" y="100" width="{SW - 32}" height="170" rx="12" fill="#101A2E"/>',
          f'<polyline points="{pts}" fill="none" stroke="url(#g)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
          f'stroke-dasharray="320" stroke-dashoffset="320"><animate attributeName="stroke-dashoffset" values="320;0;0;320" '
          f'keyTimes="0;0.5;0.9;1" dur="5s" repeatCount="indefinite"/></polyline>',
          f'<circle cx="196" cy="150" r="5" fill="{MINT}"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.45;0.5;0.9;1" dur="5s" repeatCount="indefinite"/></circle>']
    for i in range(16):
        x = 22 + i * 12.5
        hs = [10 + (i * 7) % 24, 30 - (i * 5) % 20, 14 + (i * 11) % 26, 8 + (i * 3) % 22, 10 + (i * 7) % 24]
        ys = ";".join(f(300 - h / 2) for h in hs)
        hh = ";".join(f(h) for h in hs)
        s3.append(f'<rect x="{x:.1f}" width="6" rx="3" fill="{BLUE}" opacity="0.9">'
                  f'<animate attributeName="y" values="{ys}" dur="{1.1 + (i % 4) * 0.15:.2f}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="height" values="{hh}" dur="{1.1 + (i % 4) * 0.15:.2f}s" repeatCount="indefinite"/></rect>')
    s3 += [f'<circle cx="{SW / 2}" cy="358" r="22" fill="url(#g)"/>',
           f'<path d="M {SW / 2 - 6} 348 L {SW / 2 + 10} 358 L {SW / 2 - 6} 368 Z" fill="#06101C"/>']

    # screen 4: social feed
    s4 = [f'<rect width="{SW}" height="{SH}" fill="#0F172A"/>', status(),
          f'<text class="s" x="20" y="66" font-size="22" font-weight="800" fill="{TXT}">re:</text>']
    for r in range(2):
        y = 92 + r * 112
        s4.append(f'<rect x="16" y="{y}" width="{SW - 32}" height="100" rx="12" fill="#172033"/>'
                  f'<circle cx="38" cy="{y + 24}" r="12" fill="{[VIOLET, BLUE][r]}"/>'
                  f'<rect x="58" y="{y + 15}" width="70" height="7" rx="3.5" fill="#334155"/>'
                  f'<rect x="58" y="{y + 28}" width="44" height="6" rx="3" fill="#243049"/>'
                  f'<rect x="28" y="{y + 52}" width="{SW - 56}" height="7" rx="3.5" fill="#243049"/>'
                  f'<rect x="28" y="{y + 66}" width="{SW - 100}" height="7" rx="3.5" fill="#243049"/>'
                  f'<g transform="translate(36,{y + 84})"><path d="M0 5 C-8 -2 -10 -9 -5 -11 C-2 -12 0 -9 0 -8 C0 -9 2 -12 5 -11 C10 -9 8 -2 0 5 Z" fill="#F43F5E">'
                  f'<animateTransform attributeName="transform" type="scale" values="1;1.3;1" dur="1.6s" repeatCount="indefinite"/></path></g>')
    s4 += [f'<rect x="16" y="320" width="120" height="30" rx="15" fill="#1E293B"/>']
    for i in range(3):
        s4.append(f'<circle cx="{44 + i * 16}" cy="335" r="3.5" fill="{BLUE}"><animate attributeName="opacity" values="0.25;1;0.25" '
                  f'dur="1.2s" begin="{i * 0.2:.1f}s" repeatCount="indefinite"/></circle>')
    s4 += [f'<rect x="16" y="364" width="{SW - 32}" height="12" rx="6" fill="#172033"/>']

    screens = "\n".join(f'<g transform="translate({SX},{SY})" clip-path="url(#scr)" opacity="{1 if i == 0 else 0}">{show(i)}{"".join(s)}</g>'
                        for i, s in enumerate([s1, s2, s3, s4]))
    defs.append(f'    <clipPath id="scr"><rect width="{SW}" height="{SH}" rx="30"/></clipPath>')
    defs.append(f'    <clipPath id="edclip"><rect x="30" y="132" width="568" height="328" rx="12"/></clipPath>')
    defs.append(f'    <radialGradient id="glow1"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.35"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>')
    defs.append(f'    <radialGradient id="glow2"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.28"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>')
    defs.append(f'    <clipPath id="hero"><rect width="{W}" height="{H}" rx="16"/></clipPath>')

    dots = "".join(f'<circle cx="{50 + i * 18}" cy="150" r="5" fill="{c}"/>' for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]))
    body = f'''  <g clip-path="url(#hero)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <circle cx="120" cy="40" r="260" fill="url(#glow1)"/>
  <circle cx="800" cy="470" r="280" fill="url(#glow2)"/>
  <rect x="0" y="0" width="{W}" height="3" fill="url(#g)"/>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
  <text class="m" x="30" y="40" font-size="12" fill="{DIM}">~/github/<tspan fill="{BLUE}">S4K1L</tspan></text>
  <text class="s" x="30" y="86" font-size="46" font-weight="800" fill="url(#g)">Shakil Mahmud</text>
  <text class="m" x="30" y="114" font-size="14" fill="{MUTED}">Flutter Developer <tspan fill="{DIM}">/</tspan> Dhaka <tspan fill="{DIM}">/</tspan> OrpheusPLC</text>

  <rect x="30" y="132" width="568" height="328" rx="12" fill="{PANEL2}" stroke="{BORDER}"/>
  <rect x="30" y="132" width="568" height="36" fill="#0A0F1C" clip-path="url(#edclip)"/>
  <line x1="30" y1="168" x2="598" y2="168" stroke="{BORDER}"/>
  {dots}
  <rect x="124" y="140" width="112" height="28" rx="6" fill="{PANEL2}"/>
  <circle cx="140" cy="154" r="4" fill="{BLUE}"/>
  <text class="m" x="152" y="158" font-size="12" fill="{TXT}">shakil.dart</text>
  <rect x="124" y="166" width="112" height="2" fill="url(#g)"/>
  <line x1="74" y1="168" x2="74" y2="460" stroke="{BORDER}"/>
  {"".join(gutter)}
  {"".join(code)}
  {caret}

  <rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="38" fill="#05070D" stroke="#2A3347" stroke-width="3"/>
  {screens}
  <rect x="{PX + PW / 2 - 36}" y="{PY + 12}" width="72" height="18" rx="9" fill="#05070D"/>
  <rect x="{PX + PW / 2 - 44}" y="{PY + PH - 14}" width="88" height="4" rx="2" fill="#2A3347"/>'''
    write("hero.svg", svg(W, H, body, "\n".join(defs) + "\n", "Shakil Mahmud, Flutter Developer: a Dart class describing him next to a phone cycling through POS, wellness, crypto and social apps"))


# ---------------------------------------------------------------- section headers
def header(num, title, tag):
    W, H, D = 900, 56, 6.0
    body = f'''  <clipPath id="hc"><rect width="{W}" height="{H}"/></clipPath>
  <rect x="2" y="10" width="40" height="26" rx="7" fill="url(#g)"/>
  <text class="m" x="22" y="28" font-size="13" font-weight="800" fill="#06101C" text-anchor="middle">{num}</text>
  <text class="s" x="58" y="31" font-size="24" font-weight="800" fill="{TXT}">{E(title)}</text>
  <text class="m" x="{W - 2}" y="29" font-size="12" fill="{DIM}" text-anchor="end">// {E(tag)}</text>
  <rect x="0" y="46" width="{W}" height="1" fill="{BORDER}"/>
  <g clip-path="url(#hc)"><rect y="45" width="180" height="3" rx="1.5" fill="url(#comet)">
    <animate attributeName="x" values="-180;{W}" dur="{D}s" repeatCount="indefinite"/></rect></g>'''
    write(f"h-{num}.svg", svg(W, H, body, "", f"{num} {title}"))


# ---------------------------------------------------------------- project cards
def icon_pos(x, y):
    return (f'<g transform="translate({x},{y})"><path d="M6 2 H50 V50 L44 46 L38 50 L32 46 L26 50 L20 46 L14 50 L8 46 L6 50 Z" fill="#172033" stroke="{BLUE}" stroke-width="1.5"/>'
            f'<rect x="14" y="12" width="28" height="4" rx="2" fill="{MUTED}"/><rect x="14" y="22" width="20" height="4" rx="2" fill="{DIM}"/>'
            f'<rect x="14" y="32" width="24" height="4" rx="2" fill="{DIM}"/>'
            f'<rect x="14" y="40" width="10" height="3" rx="1.5" fill="{MINT}"><animate attributeName="width" values="4;26;4" dur="2.4s" repeatCount="indefinite"/></rect></g>')


def icon_nexora(x, y):
    return (f'<g transform="translate({x},{y})"><rect x="4" y="30" width="22" height="20" rx="4" fill="#172033" stroke="{BLUE}" stroke-width="1.5"/>'
            f'<rect x="30" y="30" width="22" height="20" rx="4" fill="#172033" stroke="{BLUE}" stroke-width="1.5"/>'
            f'<rect x="17" y="6" width="22" height="20" rx="4" fill="url(#gv)"><animate attributeName="y" values="6;2;6" dur="2s" repeatCount="indefinite"/></rect></g>')


def icon_kunchi(x, y):
    cols = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#3B82F6", "#A855F7"]
    s = "".join(f'<circle cx="28" cy="28" r="{26 - i * 4}" fill="none" stroke="{c}" stroke-width="2.4">'
                f'<animate attributeName="r" values="{26 - i * 4};{29 - i * 4};{26 - i * 4}" dur="3s" begin="{i * 0.15:.2f}s" repeatCount="indefinite"/></circle>'
                for i, c in enumerate(cols))
    return f'<g transform="translate({x},{y})">{s}</g>'


def icon_clue(x, y):
    return (f'<g transform="translate({x},{y})"><ellipse cx="28" cy="28" rx="24" ry="24" fill="#172033" stroke="{BLUE}" stroke-width="2">'
            f'<animate attributeName="rx" values="24;3;24" dur="2.6s" repeatCount="indefinite"/></ellipse>'
            f'<text class="s" x="28" y="36" font-size="22" font-weight="800" fill="{MINT}" text-anchor="middle">C'
            f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="2.6s" repeatCount="indefinite"/></text></g>')


def icon_re(x, y):
    return (f'<g transform="translate({x},{y})"><rect x="2" y="4" width="40" height="28" rx="10" fill="#172033" stroke="{BLUE}" stroke-width="1.5"/>'
            f'<path d="M12 32 L10 44 L22 32 Z" fill="#172033" stroke="{BLUE}" stroke-width="1.5" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{14 + i * 9}" cy="18" r="2.8" fill="{BLUE}"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.2s" begin="{i * 0.2:.1f}s" repeatCount="indefinite"/></circle>' for i in range(3))
            + f'<rect x="18" y="30" width="36" height="22" rx="8" fill="url(#gv)" opacity="0.9"/></g>')


def icon_grid(x, y):
    s = ""
    for r in range(3):
        for c in range(3):
            i = r * 3 + c
            s += (f'<rect x="{c * 19}" y="{r * 19}" width="14" height="14" rx="4" fill="{BLUE}" opacity="0.25">'
                  f'<animate attributeName="opacity" values="0.2;1;0.2" dur="3s" begin="{i * 0.18:.2f}s" repeatCount="indefinite"/></rect>')
    return f'<g transform="translate({x},{y + 2})">{s}</g>'


def card(fname, name, lines, tags, icon, cta, label):
    W, H, D = 440, 168, 6.0
    desc = "".join(f'<text class="s" x="26" y="{68 + i * 18}" font-size="12.5" fill="{MUTED}">{E(l)}</text>' for i, l in enumerate(lines))
    px, pills = 26, ""
    for t in tags:
        w = len(t) * 6.9 + 20
        pills += (f'<rect x="{px:.0f}" y="124" width="{w:.0f}" height="24" rx="12" fill="#172033" stroke="{BORDER}"/>'
                  f'<text class="m" x="{px + w / 2:.0f}" y="140" font-size="11" fill="{BLUE}" text-anchor="middle">{E(t)}</text>')
        px += w + 8
    body = f'''  <clipPath id="cc"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <rect width="{W}" height="{H}" rx="14" fill="{PANEL}"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#grid)"/>
  <g clip-path="url(#cc)">
    <rect x="0" y="0" width="5" height="{H}" fill="url(#gv)"/>
    <rect y="0" width="160" height="2" fill="url(#comet)"><animate attributeName="x" values="-160;{W}" dur="{D}s" repeatCount="indefinite"/></rect>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{BORDER}"/>
  <text class="s" x="26" y="40" font-size="21" font-weight="800" fill="{TXT}">{E(name)}</text>
  {desc}
  {pills}
  {icon(364, 22)}
  <text class="m" x="{W - 22}" y="140" font-size="11.5" fill="{BLUE if cta != 'private' else DIM}" text-anchor="end">{E(cta)}</text>'''
    write(fname, svg(W, H, body, "", label))


# ---------------------------------------------------------------- BLoC diagram
def bloc():
    W, H, D = 900, 372, 12.0
    bw, bh, by = 170, 112, 96
    ux, bx, rx_ = 30, 365, 700
    yt, yb = 132, 176  # top lane (outbound) / bottom lane (inbound)
    nodes = [("UI", "Widgets", ux), ("BLoC", "events -> states", bx), ("Repository", "Firebase . Supabase . REST", rx_)]
    body = [f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL}"/><rect width="{W}" height="{H}" rx="16" fill="url(#grid)"/>',
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>',
            f'<text class="m" x="30" y="40" font-size="12" fill="{DIM}">checkout flow . one tap, traced through the layers</text>']
    seg = [  # (x1, x2, lane y, label, sublabel, node index lit, start, end)
        (ux + bw, bx, yt, "ScanItem(sku)", "event", 1, 0.04, 0.20),
        (bx + bw, rx_, yt, "GET /products/42", "request", 2, 0.24, 0.40),
        (rx_, bx + bw, yb, "Product(...)", "data", 1, 0.44, 0.60),
        (bx, ux + bw, yb, "CartUpdated(total)", "state", 0, 0.64, 0.80),
    ]
    for i, (x1, x2, y, lab, sub, lit, s, e) in enumerate(seg):
        d = f"M {x1} {y} L {x2} {y}"
        body.append(f'<path id="p{i}" d="{d}" fill="none" stroke="{BORDER}" stroke-width="2" stroke-dasharray="5 5"/>')
        arrow = (x2 - 8, x2) if x2 > x1 else (x2 + 8, x2)
        body.append(f'<path d="M {arrow[0]} {y - 5} L {arrow[1]} {y} L {arrow[0]} {y + 5}" fill="none" stroke="{DIM}" stroke-width="2"/>')
        mid = (x1 + x2) / 2
        ly = y - 12 if y == yt else y + 22
        body.append(f'<g opacity="0.35">{lin("opacity", 0.35, [(s, 0.35), (s + 0.02, 1), (e + 0.1, 1), (e + 0.14, 0.35)], D)}'
                    f'<text class="m" x="{mid}" y="{ly}" font-size="11.5" font-weight="700" fill="{BLUE}" text-anchor="middle">{E(lab)}</text>'
                    f'<text class="m" x="{mid}" y="{ly + (-13 if y == yt else 14)}" font-size="9.5" fill="{DIM}" text-anchor="middle">{sub}</text></g>')
        body.append(f'<circle r="6" fill="{MINT if y == yb else BLUE}" opacity="0">'
                    f'<animateMotion dur="{D}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{f(s)};{f(e)};1" calcMode="linear"><mpath href="#p{i}"/></animateMotion>'
                    f'{anim("opacity", 0, [(s, 1), (e + 0.001, 0)], D)}</circle>')
    lights = {0: [(0.64, 0.86)], 1: [(0.04, 0.2), (0.44, 0.6)], 2: [(0.24, 0.4)]}
    for idx, (nm, sub, x) in enumerate(nodes):
        ev = []
        for s, e in lights[idx]:
            ev += [(s, BLUE), (e + 0.06, BORDER)]
        big = idx == 1
        body.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="#0F172A" stroke="{BORDER}" stroke-width="2">{anim("stroke", BORDER, ev, D)}</rect>')
        body.append(f'<text class="s" x="{x + bw / 2}" y="{by + 38}" font-size="{22 if big else 20}" font-weight="800" fill="{TXT}" text-anchor="middle">{nm}</text>')
        body.append(f'<text class="m" x="{x + bw / 2}" y="{by + 62}" font-size="10.5" fill="{MUTED}" text-anchor="middle">{E(sub)}</text>')
        body.append(f'<rect x="{x + 26}" y="{by + 78}" width="{bw - 52}" height="4" rx="2" fill="url(#g)" opacity="0.6"/>')
    rules = [("01", "the UI only sends events"), ("02", "the BLoC owns the logic"), ("03", "data stays behind a repository")]
    for i, (n, t) in enumerate(rules):
        x = 30 + i * 290
        body.append(f'<text class="m" x="{x}" y="294" font-size="12" font-weight="800" fill="{BLUE}">{n}</text>'
                    f'<text class="s" x="{x + 28}" y="294" font-size="14" font-weight="600" fill="{TXT}">{E(t)}</text>')
    body.append(f'<text class="m" x="30" y="332" font-size="12" fill="{DIM}">events go in, immutable states come out. every screen is just a function of the latest state.</text>')
    write("bloc.svg", svg(W, H, "\n".join(body), "", "BLoC data flow: UI sends an event to the BLoC, which calls a repository, gets data back and emits a new state to the UI"))


# ---------------------------------------------------------------- widget tree
def tree():
    W, D = 900, 16.0
    rows = [
        ("languages", TY, ["Dart", "Python", "C", "C++"]),
        ("framework", BLUE, ["Flutter"]),
        ("state", KW, ["BLoC"]),
        ("backend", ST, ["Firebase", "Supabase", "REST APIs"]),
        ("design", AN, ["Figma", "Material Design"]),
        ("cs", FN, ["Data Structures", "Algorithms", "OOP"]),
        ("tooling", PN, ["VS Code", "Android Studio", "Git", "GitHub"]),
    ]
    RH, Y0 = 40, 98
    H = Y0 + len(rows) * RH + 30
    body = [f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL2}"/><rect width="{W}" height="{H}" rx="16" fill="url(#grid)"/>',
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>',
            f'<text class="m" x="30" y="40" font-size="12" fill="{DIM}">widget inspector</text>',
            f'<rect x="0" y="56" width="{W}" height="1" fill="{BORDER}"/>',
            f'<rect x="30" y="70" width="14" height="14" rx="4" fill="url(#gv)"/>',
            f'<text class="m" x="54" y="82" font-size="14" font-weight="800" fill="{TXT}">ShakilApp</text>'
            f'<text class="m" x="140" y="82" font-size="12" fill="{DIM}">( stack: dependencies )</text>']
    last_y = Y0 + (len(rows) - 1) * RH + 6
    body.append(f'<line x1="37" y1="88" x2="37" y2="{last_y}" stroke="{BORDER}" stroke-width="1.5"/>')
    for i, (key, col, chips) in enumerate(rows):
        cy = Y0 + i * RH + 6
        t = 0.04 + i * 0.07
        g = [f'<line x1="37" y1="{cy}" x2="62" y2="{cy}" stroke="{BORDER}" stroke-width="1.5"/>',
             f'<rect x="66" y="{cy - 5}" width="10" height="10" rx="3" fill="{col}"/>',
             f'<text class="m" x="88" y="{cy + 4}" font-size="13" font-weight="800" fill="{col}">{key}:</text>']
        x = 232
        for c in chips:
            w = len(c) * 7.4 + 24
            g.append(f'<rect x="{x:.0f}" y="{cy - 12}" width="{w:.0f}" height="24" rx="12" fill="{col}" fill-opacity="0.1" stroke="{col}" stroke-opacity="0.45"/>'
                     f'<text class="m" x="{x + w / 2:.0f}" y="{cy + 4}" font-size="12" fill="{TXT}" text-anchor="middle">{E(c)}</text>')
            x += w + 10
        body.append(f'<g>{lin("opacity", 0, [(t, 0), (t + 0.03, 1), (0.94, 1), (0.98, 0)], D)}'
                    f'<animateTransform attributeName="transform" type="translate" calcMode="linear" values="-16 0;-16 0;0 0;0 0" '
                    f'keyTimes="0;{f(t)};{f(t + 0.03)};1" dur="{D}s" repeatCount="indefinite"/>{"".join(g)}</g>')
    write("tree.svg", svg(W, H, "\n".join(body), "", "Skill stack as a widget tree: languages, framework, state, backend, design, computer science, tooling"))


# ---------------------------------------------------------------- stats (live from GitHub API)
FALLBACK = {"repos": 66, "followers": 13, "stars": 9, "since": 2022,
            "langs": [("Dart", 46), ("C++", 7), ("Python", 3), ("Java", 1), ("TypeScript", 1)],
            "recent": [("Universal-POS", "Oct 2026"), ("Universal-POS-Backend", "Oct 2026"), ("Shakil-Portfolio", "Oct 2026"), ("Inventory-POS-System---Nexora", "Oct 2026")]}
LANG_COL = {"Dart": BLUE, "C++": "#F34B7D", "Python": "#4B8BBE", "Java": "#E8A33D", "TypeScript": "#3178C6", "C": "#9CA3AF", "Kotlin": "#A97BFF", "JavaScript": "#F1E05A"}


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
        langs = sorted(counts.items(), key=lambda kv: -kv[1])
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        recent = [(r["name"], f'{months[int(r["pushed_at"][5:7]) - 1]} {r["pushed_at"][:4]}') for r in [r for r in own if r["name"] != USER][:4]]
        return {"repos": u["public_repos"], "followers": u["followers"], "stars": sum(r["stargazers_count"] for r in own),
                "since": int(u["created_at"][:4]), "langs": langs, "recent": recent}
    except Exception as exc:  # network/rate-limit: keep the previous file rather than overwrite with guesses
        print("stats fetch failed:", exc, file=sys.stderr)
        return None


def stats(data):
    W, H = 900, 330
    langs = data["langs"][:5]
    other = sum(n for _, n in data["langs"][5:])
    if other:
        langs.append(("Other", other))
    total = sum(n for _, n in langs) or 1
    tiles = [(str(data["repos"]), "public repos"), (str(data["stars"]), "stars earned"),
             (str(data["followers"]), "followers"), (str(max(1, datetime.date.today().year - data["since"])) + " yrs", "building on GitHub")]
    body = [f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL}"/><rect width="{W}" height="{H}" rx="16" fill="url(#grid)"/>',
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>']
    tw, gap = 201, 12
    for i, (v, l) in enumerate(tiles):
        x = 30 + i * (tw + gap)
        body.append(f'<rect x="{x}" y="28" width="{tw}" height="88" rx="12" fill="#0F172A" stroke="{BORDER}"/>'
                    f'<rect x="{x}" y="28" width="4" height="88" rx="2" fill="url(#gv)"/>'
                    f'<text class="s" x="{x + 22}" y="74" font-size="34" font-weight="800" fill="{TXT}">{v}</text>'
                    f'<text class="m" x="{x + 22}" y="98" font-size="11" fill="{DIM}">{l}</text>')
    body.append(f'<text class="m" x="30" y="150" font-size="12" fill="{DIM}">primary language per repo</text>')
    x, bar = 30, ""
    defs = f'    <clipPath id="wipe"><rect x="30" y="160" height="14" width="840" rx="7"><animate attributeName="width" from="0" to="840" dur="1.6s" fill="freeze"/></rect></clipPath>\n'
    for name, n in langs:
        w = 840 * n / total
        bar += f'<rect x="{x:.1f}" y="160" width="{max(w, 2):.1f}" height="14" fill="{LANG_COL.get(name, VIOLET if name == "Other" else MUTED)}"/>'
        x += w
    body.append(f'<rect x="30" y="160" width="840" height="14" rx="7" fill="#0F172A"/><g clip-path="url(#wipe)">{bar}</g>')
    lx = 30
    for name, n in langs:
        col = LANG_COL.get(name, VIOLET if name == "Other" else MUTED)
        label = f"{name}  {round(100 * n / total)}%"
        body.append(f'<circle cx="{lx + 5}" cy="198" r="5" fill="{col}"/><text class="m" x="{lx + 16}" y="202" font-size="11.5" fill="{MUTED}">{E(label)}</text>')
        lx += 16 + len(label) * 7 + 22
    body.append(f'<text class="m" x="30" y="242" font-size="12" fill="{DIM}">recently pushed</text>')
    for i, (nm, when) in enumerate(data["recent"]):
        x0 = 30 + (i % 2) * 435
        y0 = 254 + (i // 2) * 34
        nm_s = nm if len(nm) <= 30 else nm[:29] + "~"
        body.append(f'<circle cx="{x0 + 5}" cy="{y0 + 12}" r="4" fill="{OK}"><animate attributeName="opacity" values="1;0.35;1" dur="{2 + i * 0.4:.1f}s" repeatCount="indefinite"/></circle>'
                    f'<text class="m" x="{x0 + 18}" y="{y0 + 16}" font-size="12.5" fill="{TXT}">{E(nm_s)}</text>'
                    f'<text class="m" x="{x0 + 410}" y="{y0 + 16}" font-size="11" fill="{DIM}" text-anchor="end">{when}</text>')
    write("stats.svg", svg(W, H, "\n".join(body), defs, f"GitHub numbers for {USER}: {data['repos']} repos, language mix and recent pushes"))


# ---------------------------------------------------------------- buttons + footer
def button(fname, glyph, label, color):
    W, H, D = 212, 48, 5.0
    body = f'''  <clipPath id="bc"><rect width="{W}" height="{H}" rx="24"/></clipPath>
  <rect width="{W}" height="{H}" rx="24" fill="{PANEL}"/>
  <g clip-path="url(#bc)"><rect y="0" width="60" height="{H}" fill="#ffffff" opacity="0.07" transform="skewX(-20)"><animate attributeName="x" values="-90;260" dur="{D}s" repeatCount="indefinite"/></rect></g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="{color}" stroke-opacity="0.6"/>
  <circle cx="26" cy="24" r="14" fill="{color}" fill-opacity="0.16"/>
  <text class="m" x="26" y="29" font-size="14" font-weight="800" fill="{color}" text-anchor="middle">{E(glyph)}</text>
  <text class="s" x="52" y="30" font-size="15" font-weight="700" fill="{TXT}">{E(label)}</text>'''
    write(fname, svg(W, H, body, "", label))


def footer():
    W, H, D = 900, 132, 12.0
    L = [("Performing hot reload...", MUTED, 0.04), ("Reloaded 1 of 1 libraries in 187ms.", OK, 0.30), ("// thanks for stopping by. let's build something.", BLUE, 0.52)]
    defs, body = [], [f'<rect width="{W}" height="{H}" rx="14" fill="{PANEL2}"/><rect width="{W}" height="{H}" rx="14" fill="url(#grid)"/>',
                       f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{BORDER}"/>',
                       f'<rect x="0" y="0" width="{W}" height="3" rx="1.5" fill="url(#g)"/>']
    for i, (txt, col, t) in enumerate(L):
        y = 44 + i * 30
        n = len(txt)
        dt = 0.0035
        defs.append(f'    <clipPath id="f{i}"><rect x="56" y="{y - 16}" height="22" width="{8.4 * n:.1f}">{anim("width", 0, [(t + j * dt, 8.4 * (j + 1)) for j in range(n)], D)}</rect></clipPath>')
        mark = "&#10003;" if col == OK else ("&gt;" if i == 0 else "~")
        body.append(f'<text class="m" x="30" y="{y}" font-size="14" fill="{col}">{mark}</text>'
                    f'<g clip-path="url(#f{i})"><text class="m" x="56" y="{y}" font-size="14" fill="{TXT if col != MUTED else MUTED}">{E(txt)}</text></g>')
    write("footer.svg", svg(W, H, "\n".join(body), "\n".join(defs) + "\n", "Hot reload complete. Thanks for stopping by."))


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
    for num, title, tag in [("01", "About", "about.md"), ("02", "Shipped", "apps.dart"), ("03", "How I build", "architecture"),
                            ("04", "Stack", "pubspec.yaml"), ("05", "Numbers", "live from the GitHub API"), ("06", "Say hi", "contact")]:
        header(num, title, tag)
    card("card-pos.svg", "Universal POS", ["One point of sale for furniture, supershop,", "cosmetic and local stores. The business type", "decides which features switch on."],
         ["Flutter", "Python", "POS"], icon_pos, "repo ->", "Universal POS")
    card("card-nexora.svg", "Nexora", ["Inventory and point-of-sale for small retail", "businesses. Stock in, sales out."],
         ["Flutter", "Inventory", "POS"], icon_nexora, "repo ->", "Nexora")
    card("card-kunchi.svg", "Kunchi Hidup", ["A chakra-based emotional wellbeing app with", "an AI companion that helps steady your mood."],
         ["Flutter", "AI", "Wellbeing"], icon_kunchi, "repo ->", "Kunchi Hidup")
    card("card-clue.svg", "TheClue", ["Crypto education app with an audio engine", "at its core."],
         ["Flutter", "Audio", "Education"], icon_clue, "repo ->", "TheClue")
    card("card-re.svg", "re:", ["A social media app.", "Private repository."],
         ["Flutter", "Social"], icon_re, "private", "re: social media app")
    card("card-all.svg", f"All {d['repos']} repos", ["Flutter apps, IoT builds and C++ experiments,", "from RFID gates to robo-soccer."],
         ["Dart", "C++", "Python"], icon_grid, "browse ->", "All repositories")
    bloc()
    tree()
    stats(d)
    button("btn-portfolio.svg", "^", "Portfolio", BLUE)
    button("btn-linkedin.svg", "in", "LinkedIn", "#60A5FA")
    button("btn-resume.svg", "v", "Resume", MINT)
    button("btn-email.svg", "@", "Email me", VIOLET)
    footer()
    print("generated", len(os.listdir(OUT)), "files in", OUT)


if __name__ == "__main__":
    main()
