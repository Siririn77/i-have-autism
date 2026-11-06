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

from graph_lib import EDGE_TYPES, REGISTER_STATUSES, Graph, ParseError, is_aggressive, load  # noqa: E402

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


def check_aggressive(graph: Graph) -> list[str]:
    """Absolute coverage: every element of the topic is either a node in a unit, or a register entry
    with a status, a reason and a place. Nothing disappears into silence."""
    problems: list[str] = []
    mapped: set[str] = set()
    for _, _, node_ids in graph.mapping:
        mapped.update(node_ids)

    registered = {entry[0]: entry for entry in graph.out_of_scope}
    for node_id, node in graph.nodes.items():
        if node_id not in mapped and node.label not in registered and node.what not in registered:
            problems.append(
                f"{node_id} «{node.label}»: нет ни в единице плана, ни в реестре «Вне рамок» — "
                "в агрессивном режиме молчание запрещено"
            )

    for element, status, why, place in graph.out_of_scope:
        if not why.strip():
            problems.append(f"реестр «{element}»: нет причины — отказ без причины это забывание")
        if not place.strip():
            problems.append(f"реестр «{element}»: не указано, где это будет")
        if status.lower() not in REGISTER_STATUSES:
            problems.append(
                f"реестр «{element}»: статус «{status}» не из {', '.join(REGISTER_STATUSES)}"
            )
        if status.lower() == "в работе" and not any(
            node.label == element or node.what == element for node in graph.nodes.values()
        ):
            problems.append(f"реестр «{element}»: статус «в работе», но узла в графе нет")

    if not graph.stages:
        problems.append("нет матрицы покрытия: в агрессивном режиме оси × этапы обязательны")
    else:
        register_names = {element for element, _, _, _ in graph.out_of_scope}
        seen: set[str] = set()
        covered = 0
        refused = 0
        holes = 0
        for axis, cells in graph.matrix:
            if len(cells) != len(graph.stages):
                problems.append(f"матрица, ось «{axis}»: {len(cells)} клеток при {len(graph.stages)} этапах")
                continue
            for stage, cell in zip(graph.stages, cells):
                text = cell.strip()
                if text.lower().startswith("не относится"):
                    refused += 1
                    if f"{axis} × {stage}" not in register_names:
                        problems.append(
                            f"матрица, «{axis}» × «{stage}»: отказ без записи в реестре «{axis} × {stage}»"
                        )
                    continue
                ids = [part.strip() for part in text.replace(";", ",").split(",") if part.strip().startswith("N")]
                if not ids:
                    holes += 1
                    problems.append(f"матрица, «{axis}» × «{stage}»: пустая клетка — дыра в покрытии")
                    continue
                covered += 1
                for node_id in ids:
                    if node_id not in graph.nodes:
                        problems.append(f"матрица, «{axis}» × «{stage}»: узла {node_id} нет в графе")
                    seen.add(node_id)
        for node_id in graph.nodes:
            if node_id not in seen:
                problems.append(f"{node_id}: не попал ни в одну клетку матрицы")
        for axis in sorted(set(graph.axes()) - {axis for axis, _ in graph.matrix}):
            problems.append(f"матрица: оси «{axis}» нет в матрице")
    return problems


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

    aggressive = "--aggressive" in argv or is_aggressive(graph)
    problems = check(graph)
    if aggressive:
        problems += check_aggressive(graph)
        covered = refused = 0
        for _, cells in graph.matrix:
            for cell in cells:
                text = cell.strip()
                if text.lower().startswith("не относится"):
                    refused += 1
                elif any(part.strip().startswith("N") for part in text.replace(";", ",").split(",")):
                    covered += 1
        if not quiet:
            total = len(graph.stages) * len(graph.axes())
            print(f"матрица: покрыто {covered}, объяснено отказом {refused}, из {total} клеток")
    if not quiet:
        print(
            f"узлов {len(graph.nodes)}, вопросов {len(graph.questions)}, рёбер {len(graph.edges)}, "
            f"осей {len(graph.axes())}, противоречий {len(graph.contradictions())}, "
            f"режим {'агрессивный' if aggressive else 'обычный'}"
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
