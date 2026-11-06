#!/usr/bin/env python3
"""Diff two versions of a graph — for the drift log.

Usage: python3 scripts/graph_diff.py old.md new.md [--json]

Prints what was added, removed and retyped, per node, per edge, per question. A graph is edited every
time the work teaches something; the drift log wants the delta, not a rewritten file with no history.
Exit 0 when there is a difference, 1 when the graphs are identical — so a script can tell "nothing
changed" from "something changed" without parsing the text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_lib import Graph, load  # noqa: E402


def diff(old: Graph, new: Graph) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "nodes_added": sorted(set(new.nodes) - set(old.nodes)),
        "nodes_removed": sorted(set(old.nodes) - set(new.nodes)),
        "nodes_changed": [],
        "edges_added": [],
        "edges_removed": [],
        "questions_added": sorted(set(new.questions) - set(old.questions)),
        "questions_removed": sorted(set(old.questions) - set(new.questions)),
    }
    for node_id in sorted(set(old.nodes) & set(new.nodes)):
        before, after = old.nodes[node_id], new.nodes[node_id]
        changes = [
            f"{field}: {getattr(before, field)!r} → {getattr(after, field)!r}"
            for field in ("what", "axis", "why", "anchor", "when")
            if getattr(before, field) != getattr(after, field)
        ]
        if changes:
            result["nodes_changed"].append(f"{node_id}: " + "; ".join(changes))

    old_edges = {(e.src, e.kind, e.dst) for e in old.edges}
    new_edges = {(e.src, e.kind, e.dst) for e in new.edges}
    result["edges_added"] = [f"{s} -{k}-> {d}" for s, k, d in sorted(new_edges - old_edges)]
    result["edges_removed"] = [f"{s} -{k}-> {d}" for s, k, d in sorted(old_edges - new_edges)]
    return result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    old, new = load(Path(argv[0])), load(Path(argv[1]))
    result = diff(old, new)
    if "--json" in argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, values in result.items():
            print(f"{key}: {len(values)}")
            for value in values:
                print("  ", value)
    return 0 if any(result.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
