"""One-shot, re-runnable: bundle the fonts the other ten design kits need (HANDOFF §0b #5: no network at run time).

    python fetch_fonts.py

Fetches the Latin-subset WOFF2 files for weights 400 and 700 (the two the kits ask Google Fonts for) and each
package's licence text from the Fontsource npm packages on cdn.jsdelivr.net, pinned to one version. A file is kept
only if it starts with the WOFF2 signature and its size equals what the jsDelivr package index reports; anything
already on disk is left alone. Riso's DM Sans and Space Mono were fetched the same way earlier (fonts/README.txt).

The list below is the ONLY thing this script will download. Adding a kit = add its families here, re-run,
then re-run build_assets.py.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
VERSION = "5.3.0"
CDN = "https://cdn.jsdelivr.net/npm/@fontsource/%s@" + VERSION
INDEX = "https://data.jsdelivr.com/v1/package/npm/@fontsource/%s@" + VERSION + "/flat"

# family name (as the kits write it) -> weights the kits ask for. Alfa Slab One has a single weight (400).
FAMILIES: dict[str, tuple[int, ...]] = {
    "Alfa Slab One": (400,), "Figtree": (400, 700), "Caveat": (400, 700), "Plus Jakarta Sans": (400, 700),
    "JetBrains Mono": (400, 700), "Chakra Petch": (400, 700), "Outfit": (400, 700), "Archivo Narrow": (400, 700),
    "Rubik": (400, 700), "Inter": (400, 700), "Hanken Grotesk": (400, 700), "Arimo": (400, 700),
    "Inconsolata": (400, 700), "Oswald": (400, 700), "Public Sans": (400, 700), "Roboto Mono": (400, 700),
    "Sofia Sans Extra Condensed": (400, 700), "Manrope": (400, 700), "Red Hat Mono": (400, 700),
}
WEIGHT_NAME = {400: "Regular", 700: "Bold"}


def package(family: str) -> str:
    return family.lower().replace(" ", "-")


def file_stem(family: str) -> str:
    return family.replace(" ", "")


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main() -> int:
    FONTS.mkdir(exist_ok=True)
    kept = skipped = 0
    total = 0
    for family, weights in FAMILIES.items():
        pkg = package(family)
        sizes = {f["name"]: f["size"] for f in json.loads(get(INDEX % pkg))["files"]}
        for w in weights:
            remote = "/files/%s-latin-%d-normal.woff2" % (pkg, w)
            local = FONTS / ("%s-%s.woff2" % (file_stem(family), WEIGHT_NAME[w]))
            if local.exists():
                skipped += 1
                continue
            data = get(CDN % pkg + remote)
            if data[:4] != b"wOF2":
                print("REFUSED %s: not a WOFF2 file" % remote, file=sys.stderr)
                return 1
            if len(data) != sizes.get(remote):
                print("REFUSED %s: %d bytes, the package index says %s" % (remote, len(data), sizes.get(remote)), file=sys.stderr)
                return 1
            local.write_bytes(data)
            kept += 1
            total += len(data)
            print("%-44s %7d bytes" % (local.name, len(data)))
        lic = FONTS / ("LICENSE-%s.txt" % file_stem(family))
        if not lic.exists():
            text = get(CDN % pkg + "/LICENSE")
            lic.write_bytes(text)
            total += len(text)
            print("%-44s %7d bytes" % (lic.name, len(text)))
    print("kept %d font files (%d already present); %d bytes written" % (kept, skipped, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
