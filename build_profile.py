#!/usr/bin/env python3
"""Generate the profile artwork.

Writes three self-contained SVGs into assets/:

  stack.svg    the techstack on an ink panel, one row per category
  marquee.svg  the toolset drifting past, never scrolling off the edge
  seal.svg     a round badge: "COMPILING ..." in hand-drawn bitmap letters

House rules, because GitHub renders these through <img>:
  * no scripts, no external fonts, no external images
  * system font stacks only (ui-monospace)
  * every animated element starts at its finished state, so a stripped-SMIL
    viewer still gets the complete poster
  * text that must not be lost is real <text>, never a mask
  * nothing personal: no name, no handle, no tagline, no project list

Stdlib only, deterministic.
"""
from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent / "assets"

CANVAS = "#121417"    # the window
PANEL = "#1A1E24"     # the raised panel
EDGE = "#2A3038"      # hairlines
DIM = "#7D8794"       # secondary text, rules
MIST = "#B9C2CE"      # body text
PAPER = "#EDF1F5"     # headings
CYAN = "#22D3C5"      # the accent bar and any lit word

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# the one place the content lives; edit here, regenerate, done.
# a "\n" wraps the row: long rows go over two lines instead of running
# under the panel's right edge
STACK = (
    ("LANGUAGES",
     "PHP \u00b7 Java \u00b7 Python \u00b7 C/C++ \u00b7 COBOL"),
    ("FRAMEWORKS & TOOLS",
     "Laravel \u00b7 Spring Boot \u00b7 Livewire \u00b7 Filament \u00b7 "
     "Alpine.js\nTailwind CSS \u00b7 Git/GitHub"),
    ("DATABASES",
     "PostgreSQL \u00b7 MySQL \u00b7 SQLite"),
    ("WORKFLOW",
     "AI-assisted development \u00b7 agentic orchestration \u00b7 MCP servers\n"
     "prompt engineering \u00b7 skill-based tool chaining"),
)

# ---------------------------------------------------------------------------
# the 5x7 bitmap alphabet, drawn as rects -- no font can be trusted inside
# an <img>-served SVG, so the display type is geometry
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    " ": ("00000",) * 7,
}


def pixel_text(text: str, x: float, y: float, px: float, fill: str,
               gap: float = 1.0, opacity: float = 1.0) -> tuple[str, float]:
    """Draw text as a grid of squares. Returns (svg, width used).

    Every glyph is a fixed 5x7 cell, so the advance is per glyph, not per
    string: take the width of a row and the height of the grid from text[0]
    and let each character advance by that same width.
    """
    rows = len(GLYPHS[text[0]])
    cols = len(GLYPHS[text[0]][0])
    rects: list[str] = []
    cx = 0
    for ch in text:
        grid = GLYPHS[ch]
        for r, line in enumerate(grid):
            for c, bit in enumerate(line):
                if bit == "1":
                    rects.append(
                        f'<rect x="{x + (cx + c) * px:.2f}" '
                        f'y="{y + r * px:.2f}" width="{px:.2f}" '
                        f'height="{px:.2f}"/>'
                    )
        cx += cols + gap
    style = f' fill="{fill}"'
    if opacity != 1.0:
        style += f' opacity="{opacity:.3g}"'
    width = (cx - gap) * px
    return f"<g{style}>{''.join(rects)}</g>", width


# ---------------------------------------------------------------------------
# shared helpers for the flat, terminal-like panels
# ---------------------------------------------------------------------------
def svg_open(w: float, h: float, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" '
        f'height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
        f'aria-label="{escape(label)}">'
    )


def caps(text: str, x: float, y: float, *, size: float = 11,
         track: float = 2.4, fill: str = DIM, opacity: float = 1.0,
         anchor: str = "start", weight: str = "400") -> str:
    """Wide-tracked small caps: the label voice of the whole page."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" '
        f'font-size="{size:.1f}" font-weight="{weight}" '
        f'letter-spacing="{track:.2f}" fill="{fill}" '
        f'opacity="{opacity:.3g}" text-anchor="{anchor}">{escape(text)}</text>'
    )


def mono(text: str, x: float, y: float, *, size: float = 14,
         fill: str = MIST, opacity: float = 1.0) -> str:
    return caps(text, x, y, size=size, track=0, fill=fill, opacity=opacity)


def bar(x: float, y: float, w: float, h: float, fill: str,
        opacity: float = 1.0) -> str:
    """A filled rect with a sub-pixel-friendly edge, nothing else."""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="{fill}" opacity="{opacity:.3g}"/>')


# ---------------------------------------------------------------------------
# 1. stack: the techstack, as a terminal panel
# ---------------------------------------------------------------------------
STACK_W = 1200
HEAD_H = 96
FOOT_H = 70
LINE = 24                 # label baseline -> first byte line
LEAD = 26                 # between wrapped lines of a long row
GAP = 34                  # between rows
PAD = 24                  # body -> footer rule
MAX_CHARS = 74            # a wider mono line would run under the panel edge

# each row is (label, lines); a long category wraps instead of clipping
ROWS = tuple((label, tools.split("\n")) for label, tools in STACK)


def row_height(lines: list[str]) -> float:
    """From a row's top to the descender of its last line: the label sits
    LINE above that line, and LEAD separates lines. Both are counted here
    and in stack_svg(), so the two can never drift apart."""
    return LINE + LEAD * (len(lines) - 1)


BODY_H = sum(row_height(lines) for _, lines in ROWS)
BODY_H += GAP * (len(ROWS) - 1)
STACK_H = HEAD_H + BODY_H + PAD * 2 + FOOT_H


def stack_svg() -> str:
    parts = [svg_open(STACK_W, STACK_H, "Tech stack")]

    # the window: one flat canvas, one raised panel, one hairline border
    parts.append(bar(0, 0, STACK_W, STACK_H, CANVAS))
    parts.append(bar(24, 24, STACK_W - 48, STACK_H - 48, PANEL))
    parts.append(
        f'<rect x="24.5" y="24.5" width="{STACK_W - 49}" '
        f'height="{STACK_H - 49}" fill="none" stroke="{EDGE}" '
        f'stroke-width="1"/>'
    )

    # the accent: a short cyan bar hanging off the panel's top-left corner
    parts.append(bar(24, 24, 4, 44, CYAN))
    parts.append(caps("TECH STACK", 48, 56, size=13, track=4.2,
                      fill=PAPER, weight="600"))
    parts.append(caps("declared, not ranked", STACK_W - 48, 56, size=11,
                      track=2.2, fill=DIM, anchor="end", opacity=0.75))

    # a full-width rule closes the header
    parts.append(bar(48, HEAD_H - 22, STACK_W - 96, 1, EDGE, 0.9))

    y = HEAD_H
    for i, (label, lines) in enumerate(ROWS):
        h = row_height(lines)
        accent = CYAN if i % 2 == 0 else EDGE
        parts.append(bar(48, y + 4, 3, h - 4, accent, 0.85))
        parts.append(caps(label, 66, y + 14, size=10.5, track=3.0,
                          fill=DIM, weight="600"))
        for j, line in enumerate(lines):
            if len(line) > MAX_CHARS:
                raise ValueError(f"{label}: {len(line)} chars > {MAX_CHARS}")
            parts.append(mono(line, 66, y + 14 + LINE + j * LEAD,
                              size=14, fill=MIST))
        y += h + GAP

    # footer: the count, stated plainly
    chatty = [len(lines[0].split(" \u00b7 ")) if len(lines) == 1
              else len(" ".join(lines).split(" \u00b7 ")) for _, lines in ROWS]
    base = STACK_H - PAD - FOOT_H
    parts.append(bar(48, base, STACK_W - 96, 1, EDGE, 0.9))
    parts.append(caps(
        f"{chatty[0]} languages  \u00b7  {chatty[1]} frameworks & tools  "
        f"\u00b7  {chatty[2]} databases  \u00b7  {chatty[3]} workflow items",
        66, base + 40, size=11.5, track=1.6, fill=DIM, opacity=0.85))
    parts.append(caps("that is the whole list", STACK_W - 48, base + 40,
                      size=10.5, track=2.2, fill=DIM, opacity=0.5,
                      anchor="end"))

    parts.append("</svg>\n")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 2. marquee: the toolset drifting, never a bare edge
# ---------------------------------------------------------------------------
MARQ_W, MARQ_H = 1200, 72
TOOLS = (
    "PHP", "Java", "Python", "C/C++", "COBOL", "Laravel", "Spring Boot",
    "Livewire", "Filament", "Alpine.js", "Tailwind CSS", "Git/GitHub",
    "PostgreSQL", "MySQL", "SQLite", "MCP servers", "prompt engineering",
    "agentic orchestration", "skill-based tool chaining",
)


def marquee_svg() -> str:
    """A drifting list of tools -- but never a bare edge.

    The strip starts at x=0, so the still frame is always a complete,
    readable row. GitHub runs SMIL, so it also slides; the clip is wide
    enough for two copies and the slide is shorter than one copy.
    """
    item = "   /   ".join(TOOLS) + "   /   "
    text = escape(item)
    segment = 1560.0
    row = (
        f'<text x="0" y="44">{text}</text>'
        f'<text x="{segment:g}" y="44">{text}</text>'
        f'<text x="{2 * segment:g}" y="44">{text}</text>'
    )
    return (
        svg_open(MARQ_W, MARQ_H, "Tools and languages")
        + bar(0, 0, MARQ_W, MARQ_H, CANVAS)
        + f'<defs><clipPath id="band"><rect x="0" y="0" width="{MARQ_W}" '
        f'height="{MARQ_H}"/></clipPath>'
        f'<linearGradient id="lf" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CANVAS}"/><stop offset="1" '
        f'stop-color="{CANVAS}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="rf" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{CANVAS}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{CANVAS}"/></linearGradient></defs>'
        + bar(0, 0, 3, MARQ_H, CYAN, 0.9)
        + f'<g clip-path="url(#band)" font-family="{MONO}" font-size="15" '
        f'letter-spacing="1.6" fill="{MIST}" opacity="0.85">'
        + f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="-260 0" dur="46s" repeatCount="indefinite"/>'
        + row
        + "</g>"
        + bar(0, 0, 140, MARQ_H, "url(#lf)")
        + bar(MARQ_W - 140, 0, 140, MARQ_H, "url(#rf)")
        + "</svg>\n"
    )


# ---------------------------------------------------------------------------
# 3. seal: a small bitmap badge, no words about me
# ---------------------------------------------------------------------------
SEAL_TEXT = "COMPILING"
SEAL_PX = 7.0
SEAL_INSET = 16          # panel inset from the canvas edge
SEAL_GUTTER = 26         # text to panel edge
SEAL_H = 132
SEAL_INK_W = pixel_text(SEAL_TEXT, 0, 0, SEAL_PX, PAPER)[1]
SEAL_TEXT_X = round(SEAL_INSET + SEAL_GUTTER)
SEAL_W = round(SEAL_TEXT_X + SEAL_INK_W + SEAL_GUTTER + SEAL_INSET)


def seal_svg() -> str:
    px, x0 = SEAL_PX, SEAL_TEXT_X
    head, _ = pixel_text(SEAL_TEXT, x0, 30, px, PAPER)
    # three dots under the first two letters: each fades in turn, and the
    # last is lit, so a stripped-SMIL viewer still sees a finished badge
    dots = "".join(
        bar(x0 + k * 16, 96, 7, 7, CYAN, 1 if k == 2 else 0.22)
        + f'<animate attributeName="opacity" values="0.22;1;0.22" '
        f'dur="1.8s" begin="{k * 0.6:.1f}s" repeatCount="indefinite"/>'
        for k in range(3)
    )
    return (
        svg_open(SEAL_W, SEAL_H, "Compiling")
        + bar(0, 0, SEAL_W, SEAL_H, CANVAS)
        + bar(SEAL_INSET, SEAL_INSET, SEAL_W - SEAL_INSET * 2,
              SEAL_H - SEAL_INSET * 2, PANEL)
        + f'<rect x="{SEAL_INSET + 0.5}" y="{SEAL_INSET + 0.5}" '
        f'width="{SEAL_W - SEAL_INSET * 2 - 1}" '
        f'height="{SEAL_H - SEAL_INSET * 2 - 1}" fill="none" stroke="{EDGE}"/>'
        + bar(SEAL_INSET, SEAL_INSET, 4, 40, CYAN, 0.9)
        + head
        + dots
        + "</svg>\n"
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, text in (("stack.svg", stack_svg()),
                       ("marquee.svg", marquee_svg()),
                       ("seal.svg", seal_svg())):
        path = OUT / name
        path.write_text(text, encoding="utf-8")
        print(f"wrote {name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
