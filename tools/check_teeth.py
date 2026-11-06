#!/usr/bin/env python3
"""Prove that every check can fail.

A check that has only ever been run on good input is an assumption with a green light. Three times in
one day a stand reported a model failure that was really the stand's own: a drawn graph read as code, a
test suite taken for the solution, prose imported from an unlabelled fence. Each time the check was
green because it was checking the wrong thing.

So every check declares two inputs in `tools/checks.json`: one that must pass and one that must fail.
`check_teeth.py` runs both. If the bad input passes, the check has no teeth and the run stops.

    python3 tools/check_teeth.py          # run every declared pair
    python3 tools/check_teeth.py --list   # names only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "checks.json"


def run(command: list[str]) -> int:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True).returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run every check against an input that must fail.")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["checks"]
    if args.list:
        for entry in entries:
            print(entry["name"])
        return 0

    bad_toothless: list[str] = []
    for entry in entries:
        good, bad = run(entry["good"]), run(entry["bad"])
        teeth = good == 0 and bad != 0
        mark = "ok  " if teeth else "FAIL"
        print(f"  {mark} {entry['name']}: хороший вход {good}, плохой {bad}")
        if not teeth:
            bad_toothless.append(entry["name"])
            if good != 0:
                print("       хороший вход не проходит — дефект входа, а не проверки")
            if bad == 0:
                print(f"       плохой вход прошёл: проверка не проверяет ({entry['why']})")

    if bad_toothless:
        print(f"зубов нет у {len(bad_toothless)} проверок из {len(entries)}")
        return 1
    print(f"зубы на месте: {len(entries)} проверок, каждая падает на своём плохом входе")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
