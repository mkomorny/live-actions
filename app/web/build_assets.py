"""Generates app/web/css/* from the preview design files (the acceptance spec).

    python build_assets.py

The look is not re-drawn: contract.css and components.css are the preview's own
files, copied verbatim except that the preview-only chrome block at the bottom of
components.css (the "PREVIEW" layout/theme switcher) is cut. Every kit's theme is the
preview's generated theme file with its Google Fonts @import replaced by local
@font-face rules (HANDOFF §0b #5: a shipped desktop app must not need the network
to look right). The families and weights come from the kit's own @import line, so a
kit gets exactly the faces it asked Google for. Re-run after
`previews/redesign-round/tools/build_round.py` regenerates the themes, and after
`fetch_fonts.py` when a kit needs a family that is not bundled yet.

Layout A's own CSS (the <style> block in layout-a.html) is copied into
css/layout-a.css the same way, so the shell's structure is the preview's.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fetch_fonts import FAMILIES, WEIGHT_NAME, file_stem

HERE = Path(__file__).resolve().parent
ROUND = HERE.parent.parent / "previews" / "redesign-round"

# family -> {weight: file in web/fonts}. DM Sans and Space Mono (Riso) were fetched first, by hand (fonts/README.txt);
# the rest are the files fetch_fonts.py downloads. Variable DM Sans covers the 400 and 700 the kit asks for as two pinned faces.
FONT_FILES: dict[str, dict[int, str]] = {
    "DM Sans": {400: "DMSans-Variable.woff2", 700: "DMSans-Variable.woff2"},
    "Space Mono": {400: "SpaceMono-Regular.woff2", 700: "SpaceMono-Bold.woff2"},
}
for _family, _weights in FAMILIES.items():
    FONT_FILES[_family] = {w: "%s-%s.woff2" % (file_stem(_family), WEIGHT_NAME[w]) for w in _weights}

IMPORT_RE = re.compile(r"^@import url\(['\"]?([^'\")]*fonts\.googleapis\.com[^'\")]*)['\"]?\);\s*\n", re.M)

FACE_HEADER = """\
/* Bundled fonts (SIL OFL 1.1; licence texts in web/fonts) -- replaces the preview theme's Google Fonts @import. */
/* The kit asked Google for weights 400 and 700 only, so 500/600 text resolves to those two faces exactly as it did there. */
"""


def requested_faces(import_url: str) -> list[tuple[str, tuple[int, ...]]]:
    """[(family, weights)] in the order the kit's own @import lists them (no wght = the family's one weight, 400)."""
    out = []
    for spec in parse_qs(urlparse(import_url).query).get("family", []):
        name, _, axis = spec.partition(":")
        weights = tuple(int(w) for w in axis.split("@", 1)[1].split(";")) if "wght@" in axis else (400,)
        out.append((name, weights))
    return out


def font_faces(slug: str, import_url: str) -> str:
    lines = [FACE_HEADER.rstrip("\n")]
    for family, weights in requested_faces(import_url):
        files = FONT_FILES.get(family)
        if files is None:
            raise SystemExit("ERROR %s: family %r is not bundled -- add it to fetch_fonts.py, run it, then re-run this." % (slug, family))
        for w in weights:
            if w not in files:
                raise SystemExit("ERROR %s: %s has no bundled weight %d" % (slug, family, w))
            if not (HERE / "fonts" / files[w]).is_file():
                raise SystemExit("ERROR %s: fonts/%s is missing (run fetch_fonts.py)" % (slug, files[w]))
            lines.append('@font-face { font-family: "%s"; font-style: normal; font-weight: %d; font-display: block; src: url("../../fonts/%s") format("woff2"); }' % (family, w, files[w]))
    return "\n".join(lines) + "\n"


def main() -> int:
    css = HERE / "css"
    (css / "themes").mkdir(parents=True, exist_ok=True)

    (css / "contract.css").write_text((ROUND / "shared" / "contract.css").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    comp = (ROUND / "shared" / "components.css").read_text(encoding="utf-8")
    cut = comp.index("/* ---- preview chrome")
    (css / "components.css").write_text(comp[:cut].rstrip() + "\n", encoding="utf-8", newline="\n")

    layout = (ROUND / "layout-a.html").read_text(encoding="utf-8")
    block = re.search(r"<style>(.*?)</style>", layout, re.S).group(1)
    (css / "layout-a.css").write_text(block.strip() + "\n", encoding="utf-8", newline="\n")

    wrote = []
    for src in sorted((ROUND / "themes").glob("*.css")):
        slug = src.stem
        theme = src.read_text(encoding="utf-8")
        m = IMPORT_RE.search(theme)
        if m is None or len(IMPORT_RE.findall(theme)) != 1:
            print("ERROR: %s does not have exactly one Google Fonts @import to replace" % slug, file=sys.stderr)
            return 1
        faces = font_faces(slug, m.group(1))
        theme = theme[:m.start()] + theme[m.end():]
        if "googleapis" in theme or "@import" in theme:
            print("ERROR: %s still has a remote import after the replacement" % slug, file=sys.stderr)
            return 1
        (css / "themes" / (slug + ".css")).write_text(faces + "\n" + theme, encoding="utf-8", newline="\n")
        wrote.append(slug)
    print("wrote css/contract.css, css/components.css, css/layout-a.css and %d themes: %s" % (len(wrote), ", ".join(wrote)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
