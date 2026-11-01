#!/usr/bin/env python3
"""Generate illocean's profile artwork.

Writes four self-contained SVGs into assets/:

  hero.svg     the banner: an ocean at dusk, the name standing on the horizon
  stack.svg    the toolset as a tide chart, one swell per category
  marquee.svg  a slow drift of the projects, never scrolling off the edge
  seal.svg     a round stamp: "still compiling" over the bio

House rules, because GitHub renders these through <img>:
  * no scripts, no external fonts, no external images
  * system font stacks only (Georgia italic, ui-monospace)
  * every animated element starts at its finished state, so a stripped-SMIL
    viewer still gets the complete poster
  * text that must not be lost is real <text>, never a mask

Stdlib only, deterministic.
"""
from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent / "assets"

INK = "#08181D"      # deep water
INK2 = "#102B31"     # the sky just above the horizon
MID = "#143137"      # the sea
GOLD = "#E9A13B"     # sun
WARM = "#F3C675"     # sun glow
MIST = "#A9C8C2"     # haze, small caps, contour lines
PAPER = "#F1EEE4"    # the name

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SERIF = "Georgia,'Times New Roman',serif"


# ---------------------------------------------------------------------------
# shared drawing helpers
# ---------------------------------------------------------------------------
def contour(y: float, amp: float, phase: float = 0.0, width: int = 1200,
            steps: int = 96, freq: float = 205.0) -> str:
    """A long swell sampled across the canvas, bleeding past both edges."""
    pts = []
    for k in range(steps + 1):
        x = -80 + k * (width + 160) / steps
        dy = amp * math.sin(x / freq + phase)
        dy += amp * 0.36 * math.sin(x / (freq * 0.34) - phase * 1.7)
        pts.append(f"{x:.0f},{y + dy:.1f}")
    return "M" + "L".join(pts)


def swell(y: float, amp: float, dur: float, opacity: float,
          stroke: str = MIST, weight: float = 1.2, delay: float = 0.0) -> str:
    """One animated contour line. The still frame is the first value."""
    d0 = contour(y, amp, 0.0)
    d1 = contour(y, amp, 1.15)
    offset = f' begin="{delay:.1f}s"' if delay else ""
    return (
        f'<path d="{d0}" fill="none" stroke="{stroke}" stroke-width="{weight:.3g}" '
        f'opacity="{opacity:.3g}"><animate attributeName="d" dur="{dur:.1f}s" '
        f'repeatCount="indefinite" values="{d0};{d1};{d0}"{offset}/></path>'
    )


def caps(text: str, x: float, y: float, size: float = 12, track: float = 5.5,
         fill: str = MIST, anchor: str = "middle", opacity: float = 0.85) -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="{size:g}" letter-spacing="{track:g}" fill="{fill}" '
        f'opacity="{opacity}">{escape(text)}</text>'
    )


def mono(text: str, x: float, y: float, size: float = 14, fill: str = MIST,
         anchor: str = "start", opacity: float = 1.0, weight: int = 400) -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="{size:g}" fill="{fill}" opacity="{opacity}" '
        f'font-weight="{weight}">{escape(text)}</text>'
    )


def svg_open(w: int, h: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
    )


# ---------------------------------------------------------------------------
# 1. hero
# ---------------------------------------------------------------------------
HERO_W, HERO_H = 1200, 600
HERO_CX = HERO_W / 2
HORIZON = 372
BASELINE = HORIZON - 44       # so the waterline wets the feet of the letters
SUN_R = 62
SUN_Y = HORIZON + 18          # centre sits under the line: half-sunk


def hero_defs() -> str:
    return (
        "<defs>"
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{INK}"/>'
        f'<stop offset="0.82" stop-color="#0D262C"/>'
        f'<stop offset="1" stop-color="{INK2}"/>'
        "</linearGradient>"
        '<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{MID}"/>'
        f'<stop offset="1" stop-color="{INK}"/>'
        "</linearGradient>"
        '<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{WARM}" stop-opacity="0.42"/>'
        f'<stop offset="0.42" stop-color="{WARM}" stop-opacity="0.14"/>'
        f'<stop offset="1" stop-color="{WARM}" stop-opacity="0"/>'
        "</radialGradient>"
        '<radialGradient id="glint" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{GOLD}" stop-opacity="0.34"/>'
        f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>'
        "</radialGradient>"
        f'<clipPath id="sky-cut"><rect x="0" y="0" width="{HERO_W}" '
        f'height="{HORIZON}"/></clipPath>'
        f'<clipPath id="sea-cut"><rect x="0" y="{HORIZON}" width="{HERO_W}" '
        f'height="{HERO_H - HORIZON}"/></clipPath>'
        "</defs>"
    )


def hero_sun() -> str:
    return (
        f'<circle cx="{HERO_CX:.0f}" cy="{SUN_Y}" r="190" fill="url(#glow)"/>'
        f'<circle cx="{HERO_CX:.0f}" cy="{SUN_Y}" r="{SUN_R}" fill="{GOLD}">'
        f'<animate attributeName="cy" dur="12s" repeatCount="indefinite" '
        f'values="{SUN_Y};{SUN_Y - 6};{SUN_Y}"/></circle>'
        # the reflection: a fat, soft ellipse that breathes with the swell
        f'<ellipse cx="{HERO_CX:.0f}" cy="{HORIZON + 40}" rx="86" ry="26" '
        f'fill="url(#glint)">'
        f'<animate attributeName="ry" dur="6.5s" repeatCount="indefinite" '
        f'values="26;34;26"/></ellipse>'
    )


def hero_sea() -> str:
    rows = [
        f'<rect x="0" y="{HORIZON}" width="{HERO_W}" height="{HERO_H - HORIZON}" '
        f'fill="url(#sea)"/>',
        # a bright seam right under the horizon, where light pools
        f'<rect x="0" y="{HORIZON}" width="{HERO_W}" height="2" '
        f'fill="{WARM}" opacity="0.28"/>',
    ]
    for i in range(7):
        rows.append(
            swell(HORIZON + 58 + i * 26, 2.0 + i * 2.1,
                  dur=9 + i * 1.8, opacity=0.30 - i * 0.035,
                  weight=1.3 - i * 0.09)
        )
    return "".join(rows)


def hero_name() -> str:
    """The name stands on the horizon; its lower half drowns in gold."""
    size, baseline, track = 168, BASELINE, -6
    common = (
        f'font-family="{SERIF}" font-size="{size}" font-style="italic" '
        f'letter-spacing="{track}" text-anchor="middle"'
    )
    return (
        f'<text x="{HERO_CX:.0f}" y="{baseline}" {common} fill="{PAPER}" '
        f'clip-path="url(#sky-cut)">illocean</text>'
        f'<text x="{HERO_CX:.0f}" y="{baseline}" {common} fill="{GOLD}" '
        f'opacity="0.42" clip-path="url(#sea-cut)">illocean</text>'
    )


def hero_svg() -> str:
    parts = [
        svg_open(HERO_W, HERO_H, "illocean — an ocean at dusk, paradox and oxymoron"),
        hero_defs(),
        f'<rect width="{HERO_W}" height="{HERO_H}" fill="url(#sky)"/>',
        hero_sun(),
        hero_sea(),
        hero_name(),
        # the bio, split by the same waterline it talks about
        caps("PARADOX", 92, HORIZON - 26, anchor="start", opacity=0.9),
        caps("OXYMORON", HERO_W - 92, HORIZON + 52, anchor="end", opacity=0.85),
        f'<line x1="92" y1="{HORIZON}" x2="{HERO_CX - 300}" y2="{HORIZON}" '
        f'stroke="{MIST}" stroke-width="1" opacity="0.35"/>',
        f'<line x1="{HERO_CX + 300}" y1="{HORIZON}" x2="{HERO_W - 92}" '
        f'y2="{HORIZON}" stroke="{MIST}" stroke-width="1" opacity="0.35"/>',
        # name plate, bottom left / right, small and quiet
        caps("KIM PHILLIP G. ANDADOR", 92, HERO_H - 42, anchor="start", opacity=0.6),
        caps("PARAÑAQUE · PH", HERO_W - 92, HERO_H - 42, anchor="end", opacity=0.6),
        "</svg>\n",
    ]
    return "".join(parts)


# ---------------------------------------------------------------------------
# 2. stack: the tide chart
# ---------------------------------------------------------------------------
STACK_W, STACK_H = 1200, 470
LANE_X = 300            # where the swell for each row begins
TIDE_TOP = 96
TIDE_ROW = 74

STACK = (
    ("01", "languages", "PHP · Python · Java · C/C++ · COBOL"),
    ("02", "frameworks", "Laravel · Livewire · Spring Boot · Filament · "
                         "Alpine.js · Tailwind CSS · Git/GitHub"),
    ("03", "data", "PostgreSQL · MySQL · SQLite"),
    ("04", "workflow", "MCP servers · prompt engineering · "
                       "skill-based tool chaining · agentic orchestration"),
)


def stack_svg() -> str:
    parts = [
        svg_open(STACK_W, STACK_H, "illocean's toolset, drawn as a tide chart"),
        f'<rect width="{STACK_W}" height="{STACK_H}" fill="{INK}"/>',
        # the sea rising from the left: a slow gradient wash, not a card
        f'<defs><linearGradient id="sea-fade" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{MID}" stop-opacity="0.55"/>'
        f'<stop offset="0.6" stop-color="{INK}" stop-opacity="0"/>'
        f"</linearGradient></defs>"
        f'<rect x="0" y="0" width="{STACK_W}" height="{STACK_H}" fill="url(#sea-fade)"/>',
        caps("TIDE CHART", 92, 54, anchor="start", opacity=0.55),
        caps("declared, not ranked", STACK_W - 92, 54, anchor="end", opacity=0.4),
    ]
    for i, (num, label, tools) in enumerate(STACK):
        y = TIDE_TOP + i * TIDE_ROW
        parts.append(caps(num, 92, y + 5, size=11, track=2, opacity=0.45,
                          anchor="start"))
        parts.append(caps(label, 92, y + 27, size=15, track=4.5,
                          fill=PAPER, opacity=1, anchor="start"))
        # the swell: one line per row, calmer as it goes down the list
        parts.append(swell(y + 8, 5.5 - i * 0.8, dur=12 + i * 2,
                           opacity=0.5 - i * 0.06, weight=1.6 - i * 0.2))
        # the tools ride the swell
        parts.append(mono(tools, LANE_X, y + 13, size=14, fill=MIST,
                          opacity=0.92))
    parts.append(
        f'<line x1="92" y1="{STACK_H - 62}" x2="{STACK_W - 92}" y2="{STACK_H - 62}" '
        f'stroke="{MIST}" stroke-width="1" opacity="0.16"/>'
    )
    parts.append(mono("15 tools, 6 languages, one person still learning all of it",
                      92, STACK_H - 32, size=12, fill=MIST, opacity=0.5))
    parts.append("</svg>\n")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 3. marquee: what is being built, right now
# ---------------------------------------------------------------------------
MARQ_W, MARQ_H = 1200, 96
PROJECTS = (
    "gif-terminal", "lunar-mcp", "Bakunawa", "yslep-service-ledger",
    "birthday-greet", "Spicetify extensions", "HCI-Project",
    "Morphos PowerPoint", "COBOL inventory",
)


def marquee_svg() -> str:
    """A drifting list of projects -- but never a bare edge.

    The band starts at x=0, so the still frame is always a complete,
    readable row. GitHub runs SMIL, so it also slides; because the strip
    cannot overflow, the list simply wraps: the clip is wide enough for two
    copies and the animation only ever shifts by less than one copy.
    """
    item = "   ·   ".join(PROJECTS) + "   ·   "
    text = escape(item)
    segment = 1500.0
    label = "IN THE WATER   "
    row = (
        f'<text x="0" y="56">{label}{text}</text>'
        f'<text x="{segment:g}" y="56">{label}{text}</text>'
        f'<text x="{2 * segment:g}" y="56">{label}{text}</text>'
    )
    return (
        svg_open(MARQ_W, MARQ_H, "projects in progress: " + ", ".join(PROJECTS))
        + f'<rect width="{MARQ_W}" height="{MARQ_H}" fill="{INK}"/>'
        + f'<defs><clipPath id="band"><rect x="0" y="0" width="{MARQ_W}" '
        f'height="{MARQ_H}"/></clipPath>'
        f'<linearGradient id="lf" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset="1" '
        f'stop-color="{INK}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="rf" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{INK}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{INK}"/></linearGradient></defs>'
        + f'<g clip-path="url(#band)" font-family="{MONO}" font-size="15" '
        f'letter-spacing="3" fill="{MIST}" opacity="0.85">'
        + f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="-260 0" dur="40s" repeatCount="indefinite"/>'
        + row
        + "</g>"
        + f'<rect x="0" y="0" width="175" height="{MARQ_H}" fill="url(#lf)"/>'
        + f'<rect x="{MARQ_W - 175}" y="0" width="175" height="{MARQ_H}" '
        f'fill="url(#rf)"/>'
        "</svg>\n"
    )


# ---------------------------------------------------------------------------
# 4. seal
# ---------------------------------------------------------------------------
SEAL = 260


def seal_svg() -> str:
    r = SEAL / 2
    ring = []
    for k in range(72):                # tick marks, alternating long and short
        a = math.radians(k * 5)
        inner = r - (10 if k % 3 == 0 else 6)
        ring.append(
            f'M{r + math.cos(a) * inner:.1f} {r + math.sin(a) * inner:.1f}'
            f'L{r + math.cos(a) * (r - 3):.1f} {r + math.sin(a) * (r - 3):.1f}'
        )
    return (
        svg_open(SEAL, SEAL, "seal: paradox, oxymoron — still compiling")
        + f'<circle cx="{r}" cy="{r}" r="{r - 1}" fill="{INK}"/>'
        + f'<circle cx="{r}" cy="{r}" r="{r - 1}" fill="none" stroke="{GOLD}" '
        f'stroke-width="1.5" opacity="0.8"/>'
        + f'<circle cx="{r}" cy="{r}" r="{r - 16}" fill="none" stroke="{MIST}" '
        f'stroke-width="1" opacity="0.25"/>'
        + f'<path d="{"".join(ring)}" stroke="{MIST}" stroke-width="1" '
        f'opacity="0.35"/>'
        + f'<circle cx="{r}" cy="{r - 34}" r="13" fill="{GOLD}"/>'
        # the sun over the line
        + f'<line x1="{r - 52}" y1="{r - 20}" x2="{r + 52}" y2="{r - 20}" '
        f'stroke="{MIST}" stroke-width="1" opacity="0.4"/>'
        + caps("PARADOX · OXYMORON", r, r + 34, size=11, track=2.4,
               fill=PAPER, opacity=0.9)
        + caps("STILL COMPILING", r, r + 62, size=8.5, track=3,
               fill=MIST, opacity=0.6)
        + "</svg>\n"
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, text in (("hero.svg", hero_svg()), ("stack.svg", stack_svg()),
                       ("marquee.svg", marquee_svg()), ("seal.svg", seal_svg())):
        path = OUT / name
        path.write_text(text, encoding="utf-8")
        print(f"wrote {name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
