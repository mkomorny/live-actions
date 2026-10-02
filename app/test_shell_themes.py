"""The shell's eleven design kits: every theme file is complete, offline, and leaves the shell's own CSS token-only.

These are the guards `capture_matrix.js` was for the previews, run against the REAL files in app/web (v1.0.64).
Pure file checks -- no browser. The pixel proof per kit is `python -m shell_dev.capture_shell --theme <slug>`.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shell_prefs  # noqa: E402

WEB = Path(__file__).resolve().parent / "web"
THEMES = WEB / "css" / "themes"
FONTS = WEB / "fonts"
SLUGS = [t["slug"] for t in shell_prefs.KNOWN_THEMES]
MAX_FONT_BYTES = 64 * 1024

FACE_RE = re.compile(r'@font-face\s*\{\s*font-family:\s*"([^"]+)";[^}]*?font-weight:\s*(\d+);[^}]*?src:\s*url\("([^"]+)"\)\s*format\("woff2"\)\s*;\s*\}')


def theme_text(slug: str) -> str:
    return (THEMES / (slug + ".css")).read_text(encoding="utf-8")


def faces(slug: str) -> list[tuple[str, int, str]]:
    return [(m.group(1), int(m.group(2)), m.group(3)) for m in FACE_RE.finditer(theme_text(slug))]


def font_families(slug: str) -> set[str]:
    """Every family named first in a --kit-font-* stack, e.g. 'Alfa Slab One' from `'Alfa Slab One',Georgia,serif`."""
    return {m.group(1) for m in re.finditer(r"--kit-font-(?:display|body|mono):\s*['\"]([^'\"]+)['\"]", theme_text(slug))}


class ThemeFiles(unittest.TestCase):
    def test_every_known_kit_has_a_file_and_every_file_is_a_known_kit(self):
        on_disk = {p.stem for p in THEMES.glob("*.css")}
        self.assertEqual(on_disk, set(SLUGS))
        self.assertEqual(len(SLUGS), 11)
        self.assertEqual(shell_prefs.DEFAULT_THEME, "risograph-art-studio")

    def test_the_preferences_picker_offers_all_of_them(self):
        svc = shell_prefs.PrefsService.__new__(shell_prefs.PrefsService)
        svc._themes_dir = THEMES
        self.assertEqual([t["slug"] for t in svc.themes()], SLUGS)

    def test_no_kit_needs_the_network(self):
        for slug in SLUGS:
            with self.subTest(kit=slug):
                text = re.sub(r"/\*.*?\*/", "", theme_text(slug), flags=re.S)      # the header comment says "@import" in words
                self.assertNotIn("@import", text)
                self.assertNotRegex(text, r"https?://")
                self.assertNotIn("googleapis", text)

    def test_every_kit_defines_every_token_the_contract_requires(self):
        # Required = read by the contract with NO fallback: var(--kit-x) rather than var(--kit-x, default).
        body = (WEB / "css" / "contract.css").read_text(encoding="utf-8").split("*/", 1)[1]
        required = sorted(set(re.findall(r"var\((--kit-[a-z0-9-]+)\)", body)))
        self.assertEqual(len(required), 17)      # bg, bg-subtle, surface, text, text-muted, border, accent, accent-text, 3 fonts, 4 radii, 2 shadows
        for slug in SLUGS:
            defined = set(re.findall(r"(--kit-[a-z0-9-]+)\s*:", theme_text(slug)))
            with self.subTest(kit=slug):
                self.assertEqual([t for t in required if t not in defined], [])


class ThemeFonts(unittest.TestCase):
    def test_every_font_face_points_at_a_real_woff2_inside_the_size_cap(self):
        seen = 0
        for slug in SLUGS:
            for family, weight, src in faces(slug):
                with self.subTest(kit=slug, face="%s %d" % (family, weight)):
                    self.assertTrue(src.startswith("../../fonts/"), src)
                    path = (THEMES / src).resolve()
                    self.assertTrue(path.is_file(), path)
                    data = path.read_bytes()
                    self.assertEqual(data[:4], b"wOF2")
                    self.assertLess(len(data), MAX_FONT_BYTES)
                    seen += 1
        self.assertGreater(seen, 40)

    def test_every_family_a_kit_names_has_a_face_for_400_and_700(self):
        for slug in SLUGS:
            declared: dict[str, set[int]] = {}
            for family, weight, _ in faces(slug):
                declared.setdefault(family, set()).add(weight)
            with self.subTest(kit=slug):
                self.assertTrue(font_families(slug), "the kit names no font at all")
                for family in font_families(slug):
                    want = {400} if family == "Alfa Slab One" else {400, 700}     # the kit's own request had no wght for this one
                    self.assertTrue(want <= declared.get(family, set()), "%s: %s has faces %s" % (slug, family, sorted(declared.get(family, []))))

    def test_every_bundled_family_has_its_licence_text(self):
        for family in {f for slug in SLUGS for f, _, _ in faces(slug)}:
            stem = family.replace(" ", "")
            have = list(FONTS.glob("OFL-%s.txt" % stem)) + list(FONTS.glob("LICENSE-%s.txt" % stem))
            with self.subTest(family=family):
                self.assertTrue(have, "no licence text for %s" % family)
                self.assertIn("SIL OPEN FONT LICENSE", have[0].read_text(encoding="utf-8", errors="replace").upper())

    def test_no_orphan_font_files(self):
        used = {Path(src).name for slug in SLUGS for _, _, src in faces(slug)}
        on_disk = {p.name for p in FONTS.glob("*.woff2")}
        self.assertEqual(on_disk - used, set())


class ShellStaysTokenOnly(unittest.TestCase):
    """A colour written into the shell's own files would look right in one kit and wrong in the other ten."""

    COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\b(?:white|black|red|green|blue|gray|grey|orange|yellow|pink|purple)\b(?!-)")

    def test_no_colour_literals_in_the_shell_css_or_page(self):
        for rel in ("css/components.css", "css/layout-a.css", "css/app.css", "css/contract.css", "index.html"):
            text = re.sub(r"/\*.*?\*/", "", (WEB / rel).read_text(encoding="utf-8"), flags=re.S)
            text = re.sub(r"var\([^)]*\)", "", text)           # a var() FALLBACK (contract.css --ad-* defaults) is a default, not a paint
            with self.subTest(file=rel):
                self.assertEqual(self.COLOUR.findall(text), [])

    def test_the_only_colour_in_the_page_scripts_is_the_tool_accent_fallback(self):
        found = []
        for p in sorted((WEB / "js").glob("*.js")):
            for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", p.read_text(encoding="utf-8")):
                found.append((p.name, m.group(0)))
        self.assertEqual(found, [("components.js", "#888")])      # `t.accent || "#888"`: a manifest without an accent


class ChatTextStaysSelectable(unittest.TestCase):
    """v1.0.69: pywebview's text_select=False blocks ALL selection; app.css must opt the reading surfaces back in."""

    CSS = re.sub(r"/\*.*?\*/", "", (WEB / "css" / "app.css").read_text(encoding="utf-8"), flags=re.S)

    def test_reading_surfaces_opt_back_in(self):
        rules = [m for m in re.finditer(r"([^{}]+)\{([^{}]*user-select:\s*text[^{}]*)\}", self.CSS)]
        selectors = " ".join(m.group(1) for m in rules)
        for cls in (".la-bubble", ".la-msg-text", ".la-sys", ".la-result", ".la-logline", ".la-note", ".la-code"):
            with self.subTest(cls=cls):
                self.assertIn(cls, selectors)

    def test_buttons_and_cards_are_not_opted_in(self):
        selectors = " ".join(m.group(1) for m in re.finditer(r"([^{}]+)\{[^{}]*user-select:\s*text[^{}]*\}", self.CSS))
        for cls in (".la-card", ".la-track", ".la-tab", ".la-row"):
            with self.subTest(cls=cls):
                self.assertNotIn(cls, selectors)


if __name__ == "__main__":
    unittest.main()
