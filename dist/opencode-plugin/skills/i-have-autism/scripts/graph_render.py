#!/usr/bin/env python3
"""Render the Mermaid block of a graph file to PNG or SVG.

Usage: python3 scripts/graph_render.py graph.md [--out graph.png] [--width 2600]

Uses `npx @mermaid-js/mermaid-cli`, which needs Node and a Chromium build. Both are found
automatically: the CLI is fetched on first run, and the browser is taken from the puppeteer cache
(`~/.cache/puppeteer/chrome/*/chrome-linux64/chrome`) — the one this host already has.

A rendering failure is reported as a failure. It is never silently skipped: a graph file that cannot be
drawn is a broken Mermaid block, and that is worth knowing before a reader opens the page.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_lib import ParseError, mermaid_block  # noqa: E402

MERMAID_CLI = "@mermaid-js/mermaid-cli@11"


def find_chrome() -> Path | None:
    cache = Path.home() / ".cache" / "puppeteer" / "chrome"
    for candidate in sorted(cache.glob("*/chrome-linux64/chrome")):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    source = Path(argv[0])
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else source.with_suffix(".png")
    width = argv[argv.index("--width") + 1] if "--width" in argv else "2600"

    if not shutil.which("npx") and not shutil.which("npm"):
        print("нет npx: поставьте Node, иначе рендер невозможен")
        return 1
    try:
        mermaid = mermaid_block(source.read_text(encoding="utf-8"))
    except ParseError as error:
        print(f"РАЗБОР НЕ ПРОШЁЛ: {error}")
        return 1

    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        (work / "graph.mmd").write_text(mermaid, encoding="utf-8")
        config: dict[str, object] = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        chrome = find_chrome()
        if chrome:
            config["executablePath"] = str(chrome)
        (work / "puppeteer.json").write_text(json.dumps(config), encoding="utf-8")
        command = [
            "npx", "-y", MERMAID_CLI,
            "-i", str(work / "graph.mmd"),
            "-o", str(out.resolve()),
            "-w", width,
            "-b", "white",
            "-p", str(work / "puppeteer.json"),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            print("рендер не прошёл:")
            print((completed.stderr or completed.stdout).strip()[-800:])
            return 1

    if not out.exists():
        print(f"CLI сказал «готово», но файла нет: {out}")
        return 1
    print(f"нарисовано: {out} ({out.stat().st_size} байт)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
