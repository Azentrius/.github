# .github

The organisation profile of Azentrius, shown at [github.com/Azentrius](https://github.com/Azentrius).

| Path | Content |
|---|---|
| `profile/README.md` | The profile page itself, in Markdown |
| `profile/assets/` | The banner, in a light and a dark version; GitHub shows the one that matches the viewer's theme |
| `scripts/render_profile.py` | Draws the banner in the Azentrius design: ink, paper and gold, DM Serif Display and DM Sans |
| `CONTRIBUTING.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | Defaults for every repository of the organisation that has none of its own |

## Texts and the banner

Projects, headings and values are Markdown text in `profile/README.md`, so they stay readable on a phone and reach screen readers as text. A new project gets an entry there, with a link to its repository and its page on azentrius.com. Product names are written plainly; the styled form (Image Update *Monitor*, Cron Jobs.) belongs to graphics and web pages.

The banner is the only graphic. Its texts are at the top of `scripts/render_profile.py`, the colours of both themes right below. After a change, render it again:

```sh
pip install fonttools uharfbuzz
python scripts/render_profile.py --fonts <design-system>/android/res/font
```

The fonts are the TTF files of the Azentrius design system. The script turns all text into outlines, because GitHub shows SVG files as images and images cannot load web fonts. The banner's alt text in `profile/README.md` says everything the banner says.

`profile/README.md` links the banner by its absolute URL on `main`. Changes show on the profile once they are on `main`.
