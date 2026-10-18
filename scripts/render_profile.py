#!/usr/bin/env python3
"""Render the graphics of the Azentrius organisation profile.

Writes every image used by profile/README.md to profile/assets/, once for
GitHub's dark theme and once for the light one. Text is converted to outlines,
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

@dataclass
class Project:
    """A product name follows the design system: a suffix in italics, or else the dot of the wordmark."""
    slug: str
    kind: str
    title: str
    text: str
    tags: list[str]
    meta: str
    suffix: str | None = None   # "Monitor" in "Image Update Monitor"
    dot: bool = False           # "Cron Jobs." for names without a suffix
    status: str | None = None   # a maturity like "Prototype": a neutral label, never a status colour


PROJECTS = [
    Project("cockpit-cronjobs", "Cockpit add-on", "Cron Jobs",
            "Every cron job and systemd timer on a server in one place. Safe root crontab "
            "edits, run history, run now, and conversion to systemd timers.",
            ["Cockpit", "cron", "systemd", "Linux"], "JavaScript · Apache-2.0", dot=True),
    Project("cockpit-image-update-monitor", "Cockpit add-on", "Image Update",
            "Configured, running and newest version of every Docker container, with "
            "in-place updates, database dumps and rollback at the push of a button.",
            ["Cockpit", "Docker", "Compose", "Diun"], "JavaScript · Apache-2.0", suffix="Monitor"),
    Project("stellwerk", "Desk display", "Stellwerk",
            "A signal box for your AI agents: a desk display that shows every Claude Code "
            "and Codex session and lets you answer their permission requests.",
            ["Claude Code", "Codex", "Windows", "Touch"], "TypeScript · Apache-2.0", dot=True),
    Project("lautwerk", "Android app", "Lautwerk",
            "Voice conversations with OpenAI and Claude on your own API keys. Chats and "
            "keys stay encrypted on the device.",
            ["Android", "Kotlin", "Jetpack Compose", "Android Auto"], "Kotlin · Apache-2.0",
            dot=True, status="Prototype"),
    Project("home-assistant-theme", "Home Assistant", "Azentrius",
            "Ink, paper and gold for the whole Home Assistant interface, light and dark as "
            "set in your profile. Your own instance serves the fonts.",
            ["Home Assistant", "HACS", "DM Sans"], "YAML · Apache-2.0", suffix="Theme"),
]

# A domain, not a product name: no suffix, no dot.
PACKAGES = Project("packages", "Package repository", "packages.azentrius.de",
                   "APT and RPM repository for the Cockpit add-ons, so Cockpit lists them under Applications.",
                   ["APT", "RPM", "AppStream", "Cockpit"], "Python · Apache-2.0")

VALUES = [
    ("Privacy first", "Privacy is not a feature, it is the foundation of every decision."),
    ("Sovereignty", "Full control over data, infrastructure and code."),
    ("European roots", "European infrastructure, European values, GDPR by default."),
    ("Openness", "Open architectures, auditable code, no black boxes."),
]

FACTS = [("EU", "Infrastructure"), ("100 %", "Self-hosted"), ("GDPR", "compliant")]


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


def wrap(text: str, font: Font, size: float, width: float) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        probe = f"{line} {word}".strip()
        if line and font.width(probe, size) > width:
            lines.append(line)
            line = word
        else:
            line = probe
    return lines + [line]


# ---------------------------------------------------------------- svg

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

    def circle(self, cx, cy, r, fill):
        self.body.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"/>')

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

    def pill(self, x, y_mid, label, font, size, h, pad, fill, text_fill, stroke=None):
        f = FONTS[font]
        w = f.width(label, size) + 2 * pad
        if stroke:
            self.rect(x + 0.5, y_mid - h / 2 + 0.5, w - 1, h - 1, rx=(h - 1) / 2, fill=fill, stroke=stroke)
        else:
            self.rect(x, y_mid - h / 2, w, h, rx=h / 2, fill=fill)
        self.text(x + pad, y_mid + f.cap * size / f.upem / 2, label, font, size, text_fill)
        return w

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
    s.text(1200, 88, "azentrius.de", "regular", 19, t["subtle"], anchor="end")
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


def heading(t, eyebrow: str, title: str) -> Svg:
    s = Svg(1280, 132, f"{eyebrow}: {title}")
    s.text(0, 34, eyebrow.upper(), "medium", 17, t["signature"], tracking=17 * 0.16)
    s.text(0, 108, title, "serif", 60, t["text"])
    return s


def product_name(s: Svg, x, y, p: Project, size, t) -> float:
    """Draw a product name as the design system styles it and return its width."""
    if p.dot:
        return s.text(x, y, p.title + ".", "serif", size, t["text"], spans=[(len(p.title), t["signature"])])
    w = s.text(x, y, p.title + (" " if p.suffix else ""), "serif", size, t["text"])
    if p.suffix:
        w += s.text(x + w, y, p.suffix, "italic", size, t["signature"])
    return w


def card(t, p: Project, side: str) -> Svg:
    """side: 'left' or 'right' for the two-column grid, 'wide' for a full row."""
    wide = side == "wide"
    w, h = (1280, 278) if wide else (640, 340)
    # The 24 px gap to the neighbouring cards is part of the image and stays transparent:
    # half of it on the inner side, all of it below a card of the two-column grid.
    gap = 0 if wide else 12
    cx = gap if side == "right" else 0
    cw = w - gap
    pad = 48  # space-2xl, as for project cards
    full_name = " ".join(filter(None, [p.title, p.suffix]))
    s = Svg(w, h if wide else h + 2 * gap, f"{full_name}: {p.text}")
    s.rect(cx + 0.5, 0.5, cw - 1, h - 1, rx=24, fill=t["card"], stroke=t["line"])
    x = cx + pad
    s.text(x, 72, p.kind.upper(), "medium", 15, t["signature"], tracking=15 * 0.16)
    s.text(cx + cw - pad, 72, p.meta, "regular", 17, t["subtle"], anchor="end")
    title_w = product_name(s, x, 126, p, 42, t)
    if p.status:
        s.pill(x + title_w + 16, 112, p.status, "regular", 15, 32, 12, t["tint"], t["on_tint"])
    lines = wrap(p.text, FONTS["regular"], 21, cw - 2 * pad)
    assert len(lines) <= (1 if wide else 3), (p.slug, lines)
    for i, line in enumerate(lines):
        s.text(x, 170 + i * 31, line, "regular", 21, t["subtle"])
    tx = x
    for tag in p.tags:
        tx += s.pill(tx, h - pad - 16, tag, "regular", 15, 32, 12, t["tint"], t["on_tint"]) + 8
    return s


def values(t) -> Svg:
    row, colw, gap = 148, 600, 80
    s = Svg(1280, 2 * row + 1, "Privacy first, sovereignty, European roots, openness")
    for i, (title, text) in enumerate(VALUES):
        x, y = (i % 2) * (colw + gap), (i // 2) * row + 0.5
        s.line(x, y, x + colw, y, t["line"])
        s.text(x, y + 52, title, "semibold", 24, t["text"])
        for j, line in enumerate(wrap(text, FONTS["regular"], 22, colw)):
            s.text(x, y + 92 + j * 31, line, "regular", 22, t["subtle"])
    s.line(0, 2 * row + 0.5, colw, 2 * row + 0.5, t["line"])
    s.line(colw + gap, 2 * row + 0.5, 1280, 2 * row + 0.5, t["line"])
    return s


def button(t, label: str, primary: bool, margin: int = 0) -> Svg:
    """margin: transparent space to the right, so a button that wraps onto the next line starts flush."""
    f = FONTS["regular"]
    size, h, pad = 16, 48, 28
    bw = round(f.width(label, size) + 2 * pad)
    s = Svg(bw + margin, h, label)
    if primary:
        s.rect(0, 0, bw, h, rx=h / 2, fill=t["primary"])
        fill = t["on_primary"]
    else:
        s.rect(0.5, 0.5, bw - 1, h - 1, rx=(h - 1) / 2, fill="none", stroke=t["primary"])
        fill = t["primary_text"]
    s.text(bw / 2, h / 2 + f.cap * size / f.upem / 2, label, "regular", size, fill, anchor="middle")
    return s


def build(fonts_dir: pathlib.Path):
    for key, (name, prefix) in FONT_FILES.items():
        FONTS[key] = Font(fonts_dir / name, prefix)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, t in THEMES.items():
        graphics = {
            "banner": banner(t),
            "heading-projects": heading(t, "Projects", "Current projects"),
            "heading-about": heading(t, "Organisation", "What is Azentrius?"),
            "values": values(t),
            "button-website": button(t, "Visit azentrius.de", primary=True, margin=12),
            "button-contact": button(t, "Contact us", primary=False),
        }
        # packages.azentrius.de fills the last row: next to the last project when their
        # number is odd, as a row of its own when it is even.
        grid = list(PROJECTS)
        if len(grid) % 2:
            grid.append(PACKAGES)
        else:
            graphics[f"card-{PACKAGES.slug}"] = card(t, PACKAGES, "wide")
        for i, p in enumerate(grid):
            graphics[f"card-{p.slug}"] = card(t, p, "left" if i % 2 == 0 else "right")
        for name, svg in graphics.items():
            (OUT / f"{name}-{theme}.svg").write_text(svg.render(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fonts", type=pathlib.Path, required=True, help="directory with the DM Sans and DM Serif Display TTFs")
    build(ap.parse_args().fonts)
