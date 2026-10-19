#!/usr/bin/env python3
"""Render the banner of the Azentrius organisation profile.

The banner is the profile's only graphic; projects, headings and values are
Markdown text in profile/README.md, so they stay readable on a phone and reach
screen readers as text. Writes profile/assets/banner-dark.svg and
banner-light.svg for GitHub's two themes. Text is converted to outlines,
because GitHub shows SVG files as images and images cannot load web fonts.

Usage:
    python scripts/render_profile.py --fonts <dir with the DM font TTFs>

The fonts are the TTF files of the Azentrius design system
(android/res/font/ in Azentrius/design-system). Needs fonttools and uharfbuzz.
"""

from __future__ import annotations

import argparse
import pathlib
from dataclasses import dataclass, field

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "profile" / "assets"

# Colours of the themes "Azentrius dunkel" and "Azentrius hell" (design system tokens).
THEMES = {
    "dark": {
        "page": "#0a0a0f", "card": "#14141c", "line": "#26262f",
        "text": "#e8e6e0", "subtle": "#8d8a82", "signature": "#c8a96e",
        "tint": "#26262f", "on_tint": "#e8e6e0",
        "primary": "#c8a96e", "on_primary": "#0a0a0f", "primary_text": "#c8a96e",
    },
    "light": {
        "page": "#f2f1ee", "card": "#ffffff", "line": "#e2dfd8",
        "text": "#0a0a0f", "subtle": "#57544d", "signature": "#7d5f22",
        "tint": "#e7e4dd", "on_tint": "#0a0a0f",
        "primary": "#0a0a0f", "on_primary": "#ffffff", "primary_text": "#0a0a0f",
    },
}

# key: (file, prefix of the glyph ids in <defs>)
FONT_FILES = {
    "serif": ("dm_serif_display_regular.ttf", "d"),
    "italic": ("dm_serif_display_italic.ttf", "i"),
    "regular": ("dm_sans_regular.ttf", "r"),
    "medium": ("dm_sans_medium.ttf", "m"),
    "semibold": ("dm_sans_semibold.ttf", "b"),
}


# ---------------------------------------------------------------- content

# The facts under the claim: what holds for every project (the same as on azentrius.com).
FACTS = [
    ("Apache-2.0", "Open source, every project"),
    ("EU", "Our servers and analytics"),
    ("Transparent", "Dependencies named per project"),
]


# ---------------------------------------------------------------- fonts

class Font:
    def __init__(self, path: pathlib.Path, prefix: str):
        self.prefix = prefix
        self.tt = TTFont(path)
        self.glyph_set = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.cap = self.tt["OS/2"].sCapHeight
        face = hb.Face(hb.Blob.from_file_path(str(path)))
        self.hb = hb.Font(face)
        self.hb.scale = (self.upem, self.upem)
        self._paths: dict[int, str] = {}

    def shape(self, text: str, liga: bool = True):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": liga})
        return [(i.codepoint, i.cluster, p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def path(self, gid: int) -> str:
        if gid not in self._paths:
            pen = SVGPathPen(self.glyph_set)
            self.glyph_set[self.order[gid]].draw(pen)
            self._paths[gid] = pen.getCommands()
        return self._paths[gid]

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        glyphs = self.shape(text, liga=tracking == 0)
        k = size / self.upem
        return sum(g[2] for g in glyphs) * k + tracking * max(len(glyphs) - 1, 0)


FONTS: dict[str, Font] = {}


def n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


@dataclass
class Svg:
    w: int
    h: int
    label: str
    body: list[str] = field(default_factory=list)
    used: dict[str, str] = field(default_factory=dict)

    def rect(self, x, y, w, h, rx=0, fill="none", stroke=None):
        s = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
        self.body.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}" fill="{fill}"{s}/>')

    def line(self, x1, y1, x2, y2, stroke):
        self.body.append(f'<path d="M{n(x1)} {n(y1)}H{n(x2)}" stroke="{stroke}" stroke-width="1" fill="none"/>'
                         if y1 == y2 else
                         f'<path d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}" stroke="{stroke}" stroke-width="1" fill="none"/>')

    def text(self, x, y, text, font: str, size, fill, anchor="start", tracking=0.0, spans=()):
        """Draw text with its baseline at y. spans: [(start index, fill)] recolour from that character on."""
        f = FONTS[font]
        k = size / f.upem
        width = f.width(text, size, tracking)
        if anchor == "end":
            x -= width
        elif anchor == "middle":
            x -= width / 2
        groups: dict[str, list[str]] = {}
        pen_x = x
        for gid, cluster, adv, xo, yo in f.shape(text, liga=tracking == 0):
            colour = fill
            for start, span_fill in spans:
                if cluster >= start:
                    colour = span_fill
            if f.path(gid):
                ref = f"{f.prefix}{gid}"
                self.used[ref] = f.path(gid)
                gx, gy = pen_x + xo * k, y - yo * k
                groups.setdefault(colour, []).append(
                    f'<use href="#{ref}" transform="translate({n(gx)} {n(gy)}) scale({k:.4f} -{k:.4f})"/>')
            pen_x += adv * k + tracking
        for colour, uses in groups.items():
            self.body.append(f'<g fill="{colour}">{"".join(uses)}</g>')
        return width

    def render(self) -> str:
        defs = "".join(f'<path id="{ref}" d="{d}"/>' for ref, d in sorted(self.used.items()))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{self.label}">'
                f'<defs>{defs}</defs>{"".join(self.body)}</svg>\n')


# ---------------------------------------------------------------- graphics

def banner(t) -> Svg:
    s = Svg(1280, 480, "Azentrius. Software you own.")
    s.rect(0.5, 0.5, 1279, 479, rx=24, fill=t["page"], stroke=t["line"])
    s.text(80, 92, "Azentrius.", "serif", 40, t["text"], spans=[(9, t["signature"])])
    s.text(1200, 88, "azentrius.com", "regular", 19, t["subtle"], anchor="end")
    s.line(0.5, 136, 1279.5, 136, t["line"])
    s.text(80, 204, "DIGITAL SOVEREIGNTY", "medium", 17, t["signature"], tracking=17 * 0.16)
    s.text(80, 300, "Software you own.", "serif", 96, t["text"], spans=[(16, t["signature"])])
    s.line(80, 348, 1200, 348, t["line"])
    col = (1200 - 80) / 3
    for i, (value, label) in enumerate(FACTS):
        x = 80 + i * col
        s.text(x, 406, value, "serif", 44, t["text"])
        s.text(x, 440, label, "regular", 19, t["subtle"])
    return s


def build(fonts_dir: pathlib.Path):
    for key, (name, prefix) in FONT_FILES.items():
        FONTS[key] = Font(fonts_dir / name, prefix)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, t in THEMES.items():
        (OUT / f"banner-{theme}.svg").write_text(banner(t).render(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fonts", type=pathlib.Path, required=True, help="directory with the DM Sans and DM Serif Display TTFs")
    build(ap.parse_args().fonts)
