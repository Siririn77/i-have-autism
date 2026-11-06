#!/usr/bin/env python3
"""Compile a plan skeleton from a graph.

Usage: python3 scripts/graph_to_plan.py graph.md --out plan.md [--minutes 40]

The graph decides *what* exists; the plan decides *in what order* and *with what check*. This script does
the mechanical part:

  * one unit per row of the plan-mapping table, or per node when the table is absent;
  * the unit's node ids and their anchors, so a unit can be verified against its sources;
  * a gate for every `contradicts` edge, attached to the units that touch the disputed nodes;
  * an explicit out-of-scope list for nodes no unit cites;
  * an empty drift log — the rule is append-only, so it starts empty.

It writes a skeleton, not a finished plan: the checks and the estimates are placeholders a human or an
agent must replace. Placeholders are marked `TODO`, and a plan containing `TODO` is not a plan.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graph_lib import Graph, load  # noqa: E402


def disputed_by(graph: Graph) -> dict[str, list[str]]:
    """node id -> list of contradictions it takes part in."""
    out: dict[str, list[str]] = {}
    for edge in graph.contradictions():
        text = f"{edge.src} ⊥ {edge.dst}: {edge.note}"
        out.setdefault(edge.src, []).append(text)
        out.setdefault(edge.dst, []).append(text)
    return out


def build(graph: Graph, minutes: int) -> str:
    units: list[tuple[str, str, list[str]]] = graph.mapping or [
        (node.id, node.label, [node.id]) for node in graph.nodes.values()
    ]
    mapped: set[str] = {node_id for _, _, ids in units for node_id in ids}
    disputed = disputed_by(graph)

    lines: list[str] = []
    title = graph.title.removeprefix("Граф ").strip().strip("«»")
    lines.append(f"# План: {title}")
    lines.append("")
    lines.append(f"Собран из `graph.md` автоматически. Минут на единицу: {minutes}. TODO заменить на свои.")
    lines.append("")
    lines.append("## 1. Цель")
    lines.append(graph.meta.get("задача", "TODO: одна строка — что за работа."))
    lines.append("")
    lines.append("Готово, когда: TODO — наблюдаемый факт (файл, ссылка, команда, что видит читатель).")
    lines.append("")
    lines.append("## 2. Вне рамок")
    outside = sorted(set(graph.nodes) - mapped)
    if outside:
        for node_id in outside:
            lines.append(f"- {node_id} «{graph.nodes[node_id].label}» — узла нет ни в одной единице работы.")
    else:
        lines.append("- Все узлы графа распределены по единицам.")
    lines.append("")
    if graph.out_of_scope:
        lines.append("")
        lines.append("### Что не входит — и где это будет (реестр)")
        lines.append("| элемент | статус | почему | где |")
        lines.append("|---|---|---|---|")
        for element, status, why, place in graph.out_of_scope:
            lines.append(f"| {element} | {status} | {why} | {place} |")
    lines.append("")
    lines.append("## 3. Входы и окружение")
    lines.append("| вход | где | проверка |")
    lines.append("|---|---|---|")
    lines.append("| `graph.md` | рядом с планом | `python3 check_graph.py graph.md` → 0 |")
    lines.append("| TODO | TODO | TODO |")
    lines.append("")
    lines.append("## 4. Единицы работы")
    lines.append("| # | единица | узлы | проверка | мин | зависит от |")
    lines.append("|---|---|---|---|---|---|")
    for index, (unit_id, title, node_ids) in enumerate(units, start=1):
        check = "TODO: команда, счёт или файл"
        lines.append(f"| {index} | {title.strip()} | {', '.join(node_ids)} | {check} | {minutes} | — |")
    lines.append("")
    lines.append("## 5. Гейты факта")
    gates = [
        (node_id, text)
        for node_id, texts in sorted(disputed.items())
        for text in texts
        if node_id in mapped
        and any(node_id in ids for _, _, ids in units)
    ]
    if gates:
        for node_id, text in gates:
            lines.append(f"- {node_id}: нельзя идти дальше, пока расхождение не названо — {text}")
    else:
        lines.append("- Противоречий в графе нет; гейтов факта не требуется.")
    lines.append("")
    lines.append("## 6. Риски")
    lines.append("| риск | признак | реакция |")
    lines.append("|---|---|---|")
    lines.append("| источник недоступен | 403/429/таймаут | второй источник, переключение в журнал |")
    lines.append("")
    lines.append("## 7. Оценка")
    total = minutes * len(units)
    lines.append(f"Единиц {len(units)}, по {minutes} мин, итого около {total} мин.")
    lines.append("")
    lines.append("## 8. Неизвестные")
    lines.append("- [?] TODO: что ещё не выяснено и как это закрыть.")
    lines.append("")
    if graph.matrix:
        lines.append("## Матрица покрытия")
        header = "| ось | " + " | ".join(graph.stages) + " |"
        lines.append(header)
        lines.append("|" + "---|" * (len(graph.stages) + 1))
        for axis, cells in graph.matrix:
            lines.append("| " + axis + " | " + " | ".join(cells) + " |")
        lines.append("")
    lines.append("## 9. Журнал расхождений")
    lines.append("| дата | план говорил | что случилось | что меняем |")
    lines.append("|---|---|---|---|")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    graph = load(Path(argv[0]))
    minutes = 40
    out: Path | None = None
    for index, arg in enumerate(argv):
        if arg == "--minutes":
            minutes = int(argv[index + 1])
        if arg == "--out":
            out = Path(argv[index + 1])
    text = build(graph, minutes)
    if out:
        out.write_text(text, encoding="utf-8")
        print(f"написано {out} — {len(text.splitlines())} строк")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
