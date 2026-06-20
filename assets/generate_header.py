#!/usr/bin/env python3
"""
Generate the animated profile banner + button SVGs for the GitHub landing page.

Why a generator instead of hand-written SVG:
  - The wave paths are math (sampled sine curves). Generating them keeps the art
    reproducible and tweakable: change N_LINES / AMP / palette here and re-run.
  - Output is self-contained SVG (no JS, no external service) so it renders inside
    a GitHub README (which strips <script> and CSS) and nothing phones home.

Animation technique:
  GitHub renders README SVGs via <img>, which runs SMIL/declarative animation but
  NOT JavaScript. So the flowing "line waves" (a la reactbits) are reproduced with
  SMIL <animateTransform>: each line is a sine path one wavelength wider than the
  frame, translated left by exactly one wavelength -> seamless infinite loop.

Run:  python3 assets/generate_header.py
"""

import math

# ----------------------------------------------------------------------------- config
W, H = 1200, 380                     # banner viewBox
N_LINES = 11                         # number of flowing wave lines
LAMBDA = 300                         # wavelength (px) -> translate distance for seamless loop
Y_TOP, Y_BOT = 70, 320               # vertical band the lines occupy
SAMPLE_STEP = 8                      # px between sampled points (smaller = smoother)

# blade-runner palette: near-black base, cyan -> magenta neon lines
BG_TOP, BG_BOT = "#05070a", "#0a0e16"
CYAN = (0, 229, 255)                 # #00e5ff
MAGENTA = (255, 45, 155)             # #ff2d9b
NAME = "DANIEL RESHETNIKOV"


def lerp(a, b, t):
    return a + (b - a) * t


def mix_hex(c1, c2, t):
    r = round(lerp(c1[0], c2[0], t))
    g = round(lerp(c1[1], c2[1], t))
    b = round(lerp(c1[2], c2[2], t))
    return f"#{r:02x}{g:02x}{b:02x}"


def sine_path(baseline, amp, phase):
    """One sine line spanning wider than the frame so it can slide seamlessly."""
    pts = []
    x = -LAMBDA - 100
    while x <= W + LAMBDA + 100:
        y = baseline + amp * math.sin(2 * math.pi * x / LAMBDA + phase)
        pts.append(f"{x:.1f},{y:.1f}")
        x += SAMPLE_STEP
    return "M " + " L ".join(pts)


def build_header():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{NAME}">',
        "<defs>",
        # vertical dark background gradient
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG_BOT}"/></linearGradient>',
        # neon bloom for the lines
        '<filter id="glow" x="-20%" y="-60%" width="140%" height="220%">'
        '<feGaussianBlur stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>',
        # softer/wider glow for the name
        '<filter id="textglow" x="-30%" y="-80%" width="160%" height="260%">'
        '<feGaussianBlur stdDeviation="3.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>',
        # radial vignette to deepen the corners
        '<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">'
        '<stop offset="0.55" stop-color="#000000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000000" stop-opacity="0.55"/></radialGradient>',
        # soft dark plate so the name reads over the neon lines
        '<radialGradient id="plate" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#05070a" stop-opacity="0.78"/>'
        '<stop offset="1" stop-color="#05070a" stop-opacity="0"/></radialGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
        '<g filter="url(#glow)">',
    ]

    for i in range(N_LINES):
        t = i / (N_LINES - 1)
        baseline = lerp(Y_TOP, Y_BOT, t)
        amp = 12 + 10 * math.sin(t * math.pi)          # fuller in the middle
        phase = t * 2.2                                 # phase offset -> drape ripple
        color = mix_hex(CYAN, MAGENTA, t)
        opacity = 0.45 + 0.4 * math.sin(t * math.pi)    # brighter mid-stack
        dur = 7.0 + 5.0 * (i % 4) / 3.0                 # varied speed
        d = sine_path(baseline, amp, phase)
        parts.append(
            f'<g>'
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="1.4" stroke-opacity="{opacity:.2f}" stroke-linecap="round"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 0" to="-{LAMBDA} 0" dur="{dur:.1f}s" '
            f'repeatCount="indefinite" additive="sum"/>'
            f'</g>'
        )

    parts.append("</g>")  # close glow group
    # vignette + name plate + name
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    parts.append(f'<ellipse cx="{W/2}" cy="{H/2-5}" rx="430" ry="120" fill="url(#plate)"/>')
    # Wide blade-runner tracking via the letter-spacing attribute. Chromium/Firefox/
    # Safari all honor it together with text-anchor="middle" (the centering glitch seen
    # in macOS Quick Look is a previewer bug, not how GitHub's browser renders it).
    parts.append(
        f'<text x="{W/2}" y="{H/2+8}" text-anchor="middle" '
        f'font-family="\'Helvetica Neue\', Helvetica, Arial, sans-serif" '
        f'font-size="34" font-weight="300" letter-spacing="12" '
        f'fill="#eaf7ff" filter="url(#textglow)">{NAME}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def build_button(label, accent, fname):
    """Small clickable pill image. Wrapped in a markdown link in the README."""
    bw, bh = 240, 56
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {bw} {bh}" width="{bw}" height="{bh}" role="img" aria-label="{label}">
<defs>
<filter id="g" x="-30%" y="-60%" width="160%" height="220%">
<feGaussianBlur stdDeviation="1.6" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>
<rect x="2" y="2" width="{bw-4}" height="{bh-4}" rx="12" fill="#0a0e16" stroke="{accent}" stroke-width="1.6" filter="url(#g)">
<animate attributeName="stroke-opacity" values="0.55;1;0.55" dur="3.2s" repeatCount="indefinite"/>
</rect>
<text x="{bw/2}" y="{bh/2+6}" text-anchor="middle" font-family="'Helvetica Neue', Helvetica, Arial, sans-serif" font-size="17" font-weight="400" letter-spacing="5" fill="{accent}">{label}</text>
</svg>'''
    with open(f"assets/{fname}", "w") as f:
        f.write(svg)


if __name__ == "__main__":
    with open("assets/header.svg", "w") as f:
        f.write(build_header())
    build_button("PORTFOLIO", "#00e5ff", "btn-portfolio.svg")
    build_button("EMAIL", "#ff2d9b", "btn-email.svg")
    print("wrote assets/header.svg, assets/btn-portfolio.svg, assets/btn-email.svg")
