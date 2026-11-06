#!/usr/bin/env python3
"""Check a graph file against the rules of D2a.

Usage: python3 scripts/check_graph.py graph.md [--quiet]

Exit 0 — clean, 1 — defects. The check never fixes anything; it names the node and the rule.

Rules, in the order they run:
  1. the file parses (six node columns, four edge columns, a Mermaid block);
  2. every declared field is filled — no anchor, no node;
  3. labels are unique (two nodes with one name cannot be told apart);
  4. an edge points at real nodes, carries a known type, is not a self-loop or a duplicate;
  5. a `causes` edge never closes a cycle — a loop means a missing node or a wrong direction;
  6. every node is reachable from a root question;
  7. every root question has at least three answers (one is an opinion, three is a case);
  8. every axis has at least three nodes (an axis with one node is a paragraph);
  9. the node count fits the declared budget.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_lib import EDGE_TYPES, Graph, ParseError, load  # noqa: E402

MIN_ANSWERS = 3
MIN_AXIS_NODES = 3


def find_cause_cycle(graph: Graph) -> list[str]:
    """Return the node ids of a cycle in `causes`, or an empty list."""
    causes = [(edge.src, edge.dst) for edge in graph.edges if edge.kind == "causes"]
    state: dict[str, int] = {}
    stack: list[str] = []

    def walk(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for src, dst in causes:
            if src != node:
                continue
            if state.get(dst) == 1:
                return stack[stack.index(dst):] + [dst]
            if state.get(dst, 0) == 0:
                found = walk(dst)
                if found:
                    return found
        state[node] = 2
        stack.pop()
        return None

    for node in graph.nodes:
        if state.get(node, 0) == 0:
            found = walk(node)
            if found:
                return found
    return []


def check(graph: Graph) -> list[str]:
    problems: list[str] = []

    for node_id, node in graph.nodes.items():
        for field_name, value in (
            ("что", node.what),
            ("ось", node.axis),
            ("почему важно", node.why),
            ("подтверждено", node.anchor),
            ("когда", node.when),
        ):
            if not value:
                problems.append(f"{node_id}: пустое поле «{field_name}»")

    labels: dict[str, str] = {}
    for node_id, node in graph.nodes.items():
        if node.label in labels:
            problems.append(f"{node_id}: подпись «{node.label}» уже занята узлом {labels[node.label]}")
        labels[node.label] = node_id

    seen_edges: set[tuple[str, str, str]] = set()
    for edge in graph.edges:
        if edge.kind not in EDGE_TYPES:
            problems.append(f"{edge.src}->{edge.dst}: тип «{edge.kind}» не из {', '.join(EDGE_TYPES)}")
        if edge.src == edge.dst:
            problems.append(f"{edge.src}: ребро в себя")
        key = (edge.src, edge.kind, edge.dst)
        if key in seen_edges:
            problems.append(f"{edge.src} -{edge.kind}-> {edge.dst}: дубль ребра")
        seen_edges.add(key)
        for endpoint in (edge.src, edge.dst):
            if endpoint not in graph.nodes and endpoint not in graph.questions:
                problems.append(f"{edge.src}->{edge.dst}: узла {endpoint} нет ни в таблице, ни в Mermaid")
        if edge.kind != "answers" and (edge.src in graph.questions or edge.dst in graph.questions):
            problems.append(f"{edge.src}->{edge.dst}: вопрос соединяется только через answers")

    # The Mermaid block and the tables must agree: a picture that drifts from the table is a lie the
    # reader cannot see.
    drawn_nodes = set(graph.mermaid_nodes)
    table_nodes = set(graph.nodes)
    for node_id in sorted(drawn_nodes - table_nodes):
        problems.append(f"{node_id}: нарисован, но строки в таблице узлов нет")
    for node_id in sorted(table_nodes - drawn_nodes):
        problems.append(f"{node_id}: есть в таблице, но не нарисован")
    for src, dst in graph.bare_edges:
        problems.append(f"{src}->{dst}: ребро без типа — у него нет смысла")

    drawn_edges = set(graph.mermaid_edges)
    table_edges = {(e.src, e.kind, e.dst) for e in graph.edges}
    for src, kind, dst in sorted(drawn_edges - table_edges):
        problems.append(f"{src} -{kind}-> {dst}: нарисовано, но нет в таблице рёбер")
    for src, kind, dst in sorted(table_edges - drawn_edges):
        problems.append(f"{src} -{kind}-> {dst}: есть в таблице, но не нарисовано")

    cycle = find_cause_cycle(graph)
    if cycle:
        problems.append("цикл в причинах: " + " -> ".join(cycle) + " — ищите пропущенный узел")

    reachable = graph.reachable_from_questions()
    for node_id in graph.nodes:
        if node_id not in reachable:
            problems.append(f"{node_id}: не достижим ни от одного корневого вопроса")

    for question in graph.questions:
        answers = graph.answers(question)
        if len(answers) < MIN_ANSWERS:
            problems.append(
                f"{question}: {len(answers)} ответ(ов) при норме {MIN_ANSWERS} — вопрос недоисследован"
            )

    for axis in graph.axes():
        count = len(graph.nodes_on(axis))
        if count < MIN_AXIS_NODES:
            problems.append(f"ось «{axis}»: {count} узл(ов) при норме {MIN_AXIS_NODES}")

    budget = graph.meta.get("бюджет узлов", "")
    if budget.isdigit() and len(graph.nodes) > int(budget):
        problems.append(f"узлов {len(graph.nodes)} при бюджете {budget} — граф не решён, а нарисован")
    return problems


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path = Path(argv[0])
    quiet = "--quiet" in argv
    try:
        graph = load(path)
    except ParseError as error:
        print(f"РАЗБОР НЕ ПРОШЁЛ: {error}")
        return 1

    problems = check(graph)
    if not quiet:
        print(
            f"узлов {len(graph.nodes)}, вопросов {len(graph.questions)}, рёбер {len(graph.edges)}, "
            f"осей {len(graph.axes())}, противоречий {len(graph.contradictions())}"
        )
    if problems:
        print(f"дефектов: {len(problems)}")
        for problem in problems:
            print("  -", problem)
        return 1
    if not quiet:
        print("ИТОГ: ЧИСТО")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
