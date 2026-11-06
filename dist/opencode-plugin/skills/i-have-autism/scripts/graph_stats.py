#!/usr/bin/env python3
"""Coverage report for a graph: where it is thin, where it is thick, what is not yet in the plan.

Usage: python3 scripts/graph_stats.py graph.md [--json]

Reads only the graph. Prints per-question answers, per-axis nodes, the longest cause chain, the number
of contradictions (future fact gates), the budget use, and which nodes no plan unit cites.
Exit 0 always: a thin graph is information, not an error. `check_graph.py` is the gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_lib import Graph, is_aggressive, load  # noqa: E402


def longest_cause_chain(graph: Graph) -> list[str]:
    """Longest path over `causes`, ignoring cycles (check_graph reports those)."""
    causes: dict[str, list[str]] = {}
    for edge in graph.edges:
        if edge.kind == "causes":
            causes.setdefault(edge.src, []).append(edge.dst)
    best: list[str] = []

    def walk(node: str, path: list[str]) -> None:
        nonlocal best
        if len(path) > len(best):
            best = list(path)
        for nxt in causes.get(node, []):
            if nxt not in path:
                walk(nxt, path + [nxt])

    for node in graph.nodes:
        walk(node, [node])
    return best


class QuestionRow(TypedDict):
    id: str
    text: str
    answers: int


class AxisRow(TypedDict):
    name: str
    nodes: int


class Report(TypedDict):
    title: str
    nodes: int
    edges: int
    questions: list[QuestionRow]
    axes: list[AxisRow]
    contradictions: list[str]
    longest_cause_chain: list[str]
    budget: str
    units: int
    unmapped_nodes: list[str]
    aggressive: bool
    matrix_covered: int
    matrix_refused: int
    matrix_total: int
    register: int


def report(graph: Graph) -> Report:
    mapped: set[str] = set()
    for _, _, node_ids in graph.mapping:
        mapped.update(node_ids)
    chain = longest_cause_chain(graph)
    questions: list[QuestionRow] = [
        {"id": qid, "text": text, "answers": len(graph.answers(qid))}
        for qid, text in graph.questions.items()
    ]
    axes: list[AxisRow] = [{"name": axis, "nodes": len(graph.nodes_on(axis))} for axis in graph.axes()]
    covered = refused = 0
    for _, cells in graph.matrix:
        for cell in cells:
            text = cell.strip()
            if text.lower().startswith("не относится"):
                refused += 1
            elif any(part.strip().startswith("N") for part in text.replace(";", ",").split(",")):
                covered += 1
    total_cells = len(graph.stages) * len(graph.axes())
    return {
        "aggressive": is_aggressive(graph),
        "matrix_covered": covered,
        "matrix_refused": refused,
        "matrix_total": total_cells,
        "register": len(graph.out_of_scope),
        "title": graph.title,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "questions": questions,
        "axes": axes,
        "contradictions": [f"{e.src} ⊥ {e.dst}" for e in graph.contradictions()],
        "longest_cause_chain": chain,
        "budget": graph.meta.get("бюджет узлов", ""),
        "units": len(graph.mapping),
        "unmapped_nodes": sorted(set(graph.nodes) - mapped) if graph.mapping else [],
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    graph = load(Path(argv[0]))
    data = report(graph)
    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"# {data['title']}")
    print(f"узлов {data['nodes']}, рёбер {data['edges']}, единиц плана {data['units']}")
    budget = data["budget"]
    if budget.isdigit():
        used = len(graph.nodes) / int(budget) * 100
        print(f"бюджет: {data['nodes']} из {budget} ({used:.0f}%)")

    print("\nвопросы:")
    for item in data["questions"]:
        flag = "  ← тонко" if item["answers"] < 3 else ""
        print(f"  {item['id']}  {item['answers']} ответ(ов)  {item['text'][:60]}{flag}")

    print("\nоси:")
    for item in sorted(data["axes"], key=lambda row: row["nodes"]):
        flag = "  ← тонко" if item["nodes"] < 3 else ""
        print(f"  {item['nodes']:2}  {item['name']}{flag}")

    chain = data["longest_cause_chain"]
    print(f"\nсамая длинная цепь причин ({len(chain)}): " + " → ".join(chain))
    print(f"противоречий (гейтов факта): {len(data['contradictions'])}")
    if data["aggressive"] or data["matrix_total"]:
        print(
            f"матрица: покрыто {data['matrix_covered']}, объяснено отказом {data['matrix_refused']}, "
            f"из {data['matrix_total']} клеток; в реестре «Вне рамок» {data['register']} записей"
        )
    if data["unmapped_nodes"]:
        print("узлы без единицы плана: " + ", ".join(data["unmapped_nodes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
