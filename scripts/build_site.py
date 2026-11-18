#!/usr/bin/env python3
"""Build the screenshot-only GitHub Pages site using the ChipDX authoring tools."""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from urllib.parse import urlsplit, parse_qs
import zlib


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HOST = "https://casualhacks.net/chipdx/"


def tool(chipdx, name):
    for profile in ("release", "debug"):
        path = chipdx / "target" / profile / name
        if path.is_file():
            return path
    raise SystemExit(f"Missing {name}; build it in ChipDX with cargo build -p {name}.")


def decode_link(link):
    url = urlsplit(link)
    assert f"{url.scheme}://{url.netloc}{url.path}" == HOST, link
    params = parse_qs(url.fragment.removeprefix("?"))
    assert set(params) == {"levelc"}, "Play links must contain only the compressed level."
    encoded = params["levelc"][0]
    level = json.loads(zlib.decompress(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))))
    assert not level.get("replays"), "A public link contains an author replay."
    return level


def render(number, relative, preview, encoder):
    source = ROOT / relative
    level = json.loads(source.read_text())
    if "replays" in level:
        raise ValueError(f"{relative}: keep author replays in ChipDX's regression fixtures, not public levels.")
    target = DOCS / "screenshots" / f"level{number:02}.png"
    # Deliberately no --reveal or --replay: these are the normal initial boards.
    result = subprocess.run([str(preview), "--json", str(source), "-o", str(target)],
                            cwd=preview.parents[2], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Rendering {relative} failed:\n{result.stderr}")
    link = subprocess.check_output([str(encoder), "--json", str(source)],
                                   cwd=encoder.parents[2], text=True).strip()
    decoded = decode_link(link)
    assert decoded["name"] == level["name"]
    assert decoded["map"] == level["map"] and decoded["entities"] == level["entities"]
    raw = target.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", raw[16:24])
    return {"number": number, "title": level["name"], "link": link,
            "image": f"screenshots/{target.name}", "width": width, "height": height,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "image_sha256": hashlib.sha256(raw).hexdigest(),
            "render_log": result.stdout + result.stderr}


def card(item):
    number = item["number"]
    title = html.escape(item["title"])
    link = html.escape(item["link"], quote=True)
    search = html.escape(f"{number} {number:02} level{number} {item['title']}".casefold(), quote=True)
    credit = ('<p class="credit">Warehouse by David W. Skinner · ferry adaptation by Codex</p>'
              if number == 58 else "")
    return f'''<article class="level" id="level{number}" data-search="{search}">
  <a class="level-link" href="{link}" target="_blank" rel="noopener" aria-label="Play level {number}: {title}">
    <div class="level-heading"><span class="level-number">{number:02}</span><h3>{title}</h3><span class="launch" aria-hidden="true">↗</span></div>
    <div class="screenshot"><img src="{item['image']}" width="{item['width']}" height="{item['height']}" alt="Initial board of {title}" loading="lazy" decoding="async"></div>
    <div class="level-bottom"><span>Play in ChipDX</span><span aria-hidden="true">→</span></div>
  </a>{credit}
</article>'''


def page(items):
    count = len(items)
    cards = "\n".join(card(item) for item in items)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0b171b">
  <meta name="description" content="{count} untimed puzzles for ChipDX. Explore Pocket Wonders and play any level in your browser.">
  <meta property="og:title" content="Pocket Wonders">
  <meta property="og:description" content="{count} puzzles. Every level unlocked. Play in ChipDX.">
  <meta property="og:image" content="https://casualx.github.io/PocketWonders/assets/banner.png">
  <meta property="og:type" content="website">
  <title>Pocket Wonders — {count} puzzles for ChipDX</title>
  <link rel="canonical" href="https://casualx.github.io/PocketWonders/">
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/gallery.js" defer></script>
</head>
<body>
  <a class="skip" href="#levels">Skip to levels</a>
  <div class="page">
    <header class="hero">
      <div class="masthead"><span><i class="pixel" aria-hidden="true"></i> A CHIPDX LEVEL COLLECTION</span><a href="https://github.com/CasualX/PocketWonders">GitHub ↗</a></div>
      <h1 class="sr-only">Pocket Wonders</h1>
      <img class="banner" src="assets/banner.png" width="960" height="360" alt="Pocket Wonders, a pixel-art world of chips, keys and puzzles" fetchpriority="high">
      <div class="intro"><p>{count} untimed puzzles for ChipDX.</p><p>Every level is unlocked. Pick one and jump in.</p></div>
      <div class="hero-actions"><a class="button primary" href="#levels">Choose a level <span aria-hidden="true">↓</span></a><a class="button" href="pocket-wonders.paks" download>Download pack</a></div>
    </header>
    <main id="levels">
      <div class="gallery-heading"><div><p class="eyebrow">CHOOSE YOUR NEXT PUZZLE</p><h2>The collection <span>{count:02}</span></h2></div>
        <form class="search" role="search" hidden><label for="level-search">Find a level</label><div class="search-box"><input id="level-search" type="search" placeholder="Number or name" autocomplete="off"><button type="button" id="clear-search" hidden>Clear</button></div></form>
      </div>
      <p id="result-count" class="result-count" aria-live="polite">All {count} levels</p>
      <div class="levels">{cards}</div>
      <p class="empty" id="empty-state" hidden>No matching levels. Try another number or name.</p>
    </main>
    <footer><p>Made for <a href="{items[0]['link']}" target="_blank" rel="noopener">ChipDX</a>. Play links open in a new tab.</p><a href="https://github.com/CasualX/PocketWonders">Source &amp; credits ↗</a></footer>
  </div>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chipdx", type=Path, help="ChipDX checkout containing the compiled tools")
    args = parser.parse_args()
    chipdx = args.chipdx
    if chipdx is None and ROOT.parent.name == "levelsets":
        chipdx = ROOT.parents[1]
    if chipdx is None:
        parser.error("Pass --chipdx /path/to/chipdx when building outside its levelsets directory.")
    chipdx = chipdx.resolve()
    preview, encoder, packer = (tool(chipdx, n) for n in ("levelpreview", "levelencode", "packset"))
    manifest = json.loads((ROOT / "index.json").read_text())
    assert manifest["unlock_all_levels"] is True
    assert all(isinstance(p, str) and (ROOT / p).resolve().is_relative_to(ROOT)
               for p in manifest["levels"])
    for folder in (DOCS / "screenshots", DOCS / "assets", ROOT / "tmp" / "site-build"):
        folder.mkdir(parents=True, exist_ok=True)
    jobs = list(enumerate(manifest["levels"], 1))
    with ThreadPoolExecutor(max_workers=4) as pool:
        items = list(pool.map(lambda item: render(*item, preview, encoder), jobs))
    (DOCS / "index.html").write_text(page(items))
    (DOCS / ".nojekyll").touch()
    shutil.copyfile(ROOT / "banner.png", DOCS / "assets" / "banner.png")
    # packset follows only index.json's level references and splash asset.
    with tempfile.TemporaryDirectory(prefix="pack-", dir=ROOT / "tmp" / "site-build") as staging:
        packed = Path(staging) / "pocket-wonders.paks"
        result = subprocess.run([str(packer), str(ROOT), str(packed)],
                                capture_output=True, text=True, check=True)
        assert packed.stat().st_size > 0
        packed.replace(DOCS / "pocket-wonders.paks")
    (ROOT / "tmp" / "site-build" / "manifest.json").write_text(json.dumps(items, indent=2) + "\n")
    (ROOT / "tmp" / "site-build" / "pack.log").write_text(result.stdout + result.stderr)
    print(f"Built {len(items)} normal screenshots and replay-free ChipDX links in {DOCS}")


if __name__ == "__main__":
    main()
