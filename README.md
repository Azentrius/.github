# .github

The organisation profile of Azentrius, shown at [github.com/Azentrius](https://github.com/Azentrius).

| Path | Content |
|---|---|
| `profile/README.md` | The profile page itself |
| `profile/assets/` | Its graphics, each in a light and a dark version; GitHub shows the one that matches the viewer's theme |
| `scripts/render_profile.py` | Draws these graphics in the Azentrius design: ink, paper and gold, DM Serif Display and DM Sans |

## Changing the graphics

The texts of the banner, the project cards and the principles are at the top of `scripts/render_profile.py`, the colours of both themes right below. After a change, render all graphics again:

```sh
pip install fonttools uharfbuzz
python scripts/render_profile.py --fonts <design-system>/android/res/font
```

The fonts are the TTF files of the Azentrius design system. The script turns all text into outlines, because GitHub shows SVG files as images and images cannot load web fonts.

A new project needs an entry in `PROJECTS` and a card link in `profile/README.md`. Product names follow the design system: a name with a suffix sets it with `suffix="…"` (shown in italics, as in Image Update *Monitor*), a name without one sets `dot=True` (shown with the gold dot, as in Cron Jobs.). A maturity like "Prototype" goes in `status` and appears as a neutral label. Alt texts name the product in plain text. Cards in the two-column grid alternate between left and right, so a new card goes at the end of the list or the order in the README changes with it.

`profile/README.md` links the images by their absolute URLs on `main`. Changes show on the profile once they are on `main`.
