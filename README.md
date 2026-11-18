# Pocket Wonders

Sixty untimed puzzles for [ChipDX](https://casualhacks.net/chipdx/), from compact challenges to full adventures. Every level is unlocked.

The website lives in [`docs/`](docs/). Each screenshot opens that level in the hosted ChipDX player using a compressed `levelc` URL.

## Play

The GitHub Pages address, once enabled, is **https://casualx.github.io/PocketWonders/**.

In this repository's **Settings → Pages**, choose **Deploy from a branch**, branch **master**, folder **/docs**. The site is plain HTML, CSS and JavaScript; no Pages build workflow or package installation is needed.

You can also download `docs/pocket-wonders.paks` and open it in ChipDX.

## Repository layout

- `index.json`, `lv/`, `banner.png`: the playable levelset.
- `docs/`: the public website, normal initial-board screenshots and downloadable pack.
- `scripts/build_site.py`: regenerate the public site with ChipDX's tools.
- `art/banner.svg`: editable banner source.
- `tmp/`: ignored local authoring work, review galleries, solution GIFs and migration backups.

Public levels, Play links and the downloadable pack omit embedded author replays. Regression replay fixtures remain in the ChipDX repository under `code/chipcore/tests/replays/pocket-wonders/`.

## Rebuild the website

Python 3.9 or newer and a ChipDX checkout are required. In ChipDX, build the authoring tools:

```sh
cargo build -p levelencode -p packset
cargo build --release -p levelpreview
```

When checked out as `chipdx/levelsets/pocket-wonders`:

```sh
python3 scripts/build_site.py
```

From a standalone checkout:

```sh
python3 scripts/build_site.py --chipdx /path/to/chipdx
```

The builder renders normal screenshots without reveal mode or replay overlays, generates replay-free links with `levelencode`, validates their compressed payloads, and packs the same public levels. It rejects source levels containing embedded replays. Build logs and provenance are written under ignored `tmp/site-build/`.

For local preview:

```sh
python3 -m http.server 8000 --directory docs
```

Then open http://localhost:8000/.

## ChipDX submodule

Pocket Wonders is used at `levelsets/pocket-wonders` in [CasualX/chipdx](https://github.com/CasualX/chipdx). From that checkout:

```sh
git submodule update --init levelsets/pocket-wonders
cargo test -p chipcore --test pocket_wonders
```

Commit level and site updates here first, then update the submodule revision in ChipDX. Keep solution recordings in ChipDX's regression fixtures or ignored `tmp/`; GIFs are ignored throughout this repository.

## Credits

The collection and banner were developed by CasualX with Codex. ChipDX and its assets are maintained by [CasualX](https://github.com/CasualX/chipdx).

**Last Ferry, Six Loads (level 58)** adapts David W. Skinner's **Sasquatch IV #12** warehouse, with credit preserved in the level's author field, and adds the ferry and boarding constraint. Other individual source credits are retained in the level JSONs.
