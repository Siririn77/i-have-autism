#!/usr/bin/env python3
"""The ultra mode: expand every node of a graph into a written description of what it contains.

The graph says what is connected to what. The expansion says what is inside each node: its
composition, its evidence, what follows from it, how it is shown, and what it deliberately leaves
out. One section per node, one line per edge mechanism, one section per axis.

Usage:
    python3 graph_expand.py graph.md --new expanded.md     # skeleton, every field TODO
    python3 graph_expand.py expanded.md --check            # exit 1 on a missing or empty field

Every node also carries a fidelity bar: the kind of check that proves it, what passes, and what only
looks like it passes. The bar is the node's own acceptance test, so the plan cannot be graded on prose.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_lib import check as check_cloud, parse as parse_cloud, parse_inline  # noqa: E402
from graph_lib import Graph, load  # noqa: E402

NODE_FIELDS = ("планка", "чем доказано", "что из этого следует", "чем показано", "что исключает")

# Планка достоверности: чем узел можно проверить и чем нельзя. Тип задаёт род проверки, и без рода
# проверки планка превращается в пожелание. Список закрыт: седьмой тип означал бы, что его придумали
# под конкретный узел, чтобы проверка прошла.
KPI_TYPES = {
    "тест": "код: названный тест, команда или свойство, которое падает, если реализация плоха",
    "цифра": "исследование: конкретное число из названной работы с годом",
    "цитата": "документ: дословная строка с местом, где она лежит",
    "воспроизведение": "опыт или расчёт: вход, команда и совпавший выход",
    "наблюдение": "история или эмпирика: названный случай, дата, место, которые можно сверить",
    "решение": "архитектура: названное решение, принятая им цена и случай, на котором оно ломается",
}
SOFT_WORDS = ("качественно", "оптимально", "красиво", "понятно", "аккуратно", "надёжно",
              "хорошо", "правильно", "грамотно", "эффективно")
KPI_GOOD_MIN = 40
KPI_BAD_MIN = 20
KPI = re.compile(r"^(?P<kind>[а-яё]+)\s*\|\s*годно:\s*(?P<good>.+?)\s*\|\s*не\s+годно:\s*(?P<bad>.+)$",
                 re.IGNORECASE | re.DOTALL)
CONCRETE = re.compile(r"\d|`[^`]+`|«[^»]+»|[\w-]+\.(?:py|md|json|ya?ml|sh)")
AXIS_FIELDS = ("что покрывает", "чего в ней нет")
STRUCTURAL_EDGES = ("answers",)
SECTION = re.compile(r"^##\s+(N\d+\s+«.+?»|Ось «.+?»|Ребро .+?)\s*$", re.MULTILINE)
FIELD = re.compile(r"^[-*]\s+(.+?):\s*(.*)$", re.MULTILINE)


def skeleton(graph: Graph) -> str:
    """Every node, every non-structural edge, every axis — with the fields empty and marked TODO."""
    lines = [f"# Расшифровка графа «{graph.title.removeprefix('Граф ').strip('«»')}»", ""]
    lines.append(
        "Каждый узел разложен на состав: что в него входит, чем это доказано, что из этого следует, "
        "чем это показано читателю и что узел намеренно исключает."
    )
    lines.append("")
    for node_id, node in graph.nodes.items():
        lines.append(f"## {node_id} «{node.label}»")
        lines.append("### Облако")
        lines.append("- ядро: TODO")
        lines.append("| элемент | связь | с чем |")
        lines.append("|---|---|---|")
        lines.append("| TODO | включает | TODO |")
        lines.append("")
        for field in NODE_FIELDS:
            if field == "планка":
                lines.append("- планка: тест | годно: TODO | не годно: TODO")
            else:
                lines.append(f"- {field}: TODO")
        lines.append("")
    for edge in graph.edges:
        if edge.kind in STRUCTURAL_EDGES:
            continue
        lines.append(f"## Ребро {edge.src} -{edge.kind}-> {edge.dst}")
        lines.append("- механизм: TODO")
        lines.append("")
    for axis in graph.axes():
        lines.append(f"## Ось «{axis}»")
        for field in AXIS_FIELDS:
            lines.append(f"- {field}: TODO")
        lines.append("")
    return "\n".join(lines)


def parse_expansion(text: str, graph: Graph | None = None) -> dict[str, dict[str, str]]:
    """Section title -> field -> value. A field written twice keeps the last one."""
    sections: dict[str, dict[str, str]] = {}
    matches = list(SECTION.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        fields = {name.strip().lower(): value.strip() for name, value in FIELD.findall(body)}
        sections[" ".join(match.group(1).split())] = fields
    return sections


def cloud_blocks(text: str) -> dict[str, str]:
    """Section title -> the text between `### Облако` and the next heading inside that section."""
    blocks: dict[str, str] = {}
    matches = list(SECTION.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        start = body.find("### Облако")
        if start < 0:
            blocks[match.group(1).strip()] = ""
            continue
        tail = body[start + len("### Облако") :]
        stop = tail.find("\n#")
        blocks[match.group(1).strip()] = tail if stop < 0 else tail[:stop]
    return blocks


def expected_sections(graph: Graph) -> dict[str, tuple[str, ...]]:
    expected: dict[str, tuple[str, ...]] = {}
    for node_id, node in graph.nodes.items():
        expected[f"{node_id} «{node.label}»"] = NODE_FIELDS
    for edge in graph.edges:
        if edge.kind in STRUCTURAL_EDGES:
            continue
        expected[f"Ребро {edge.src} -{edge.kind}-> {edge.dst}"] = ("механизм",)
    for axis in graph.axes():
        expected[f"Ось «{axis}»"] = AXIS_FIELDS
    return expected


def check_kpi(value: str, seen: dict[str, str], title: str) -> list[str]:
    """A bar names its kind of check, what passes it, and what only looks like it passes.

    The bar is high by construction: the passing half must point at something checkable — a test name,
    a number, a quoted line, an input — and the failing half must name the cheap substitute. A bar that
    says "качественно проработано" names neither, and would pass every review while checking nothing.
    """
    problems: list[str] = []
    match = KPI.match(value.strip())
    if not match:
        return [f"{title}: планка не разобрана — нужно «тип | годно: … | не годно: …»"]
    kind = match.group("kind").strip().lower()
    good = " ".join(match.group("good").split())
    bad = " ".join(match.group("bad").split())
    if kind not in KPI_TYPES:
        problems.append(f"{title}: тип планки «{kind}» не из списка {', '.join(KPI_TYPES)}")
    if not CONCRETE.search(good):
        problems.append(f"{title}: планка без предмета — в «годно» нет ни числа, ни имени, ни команды")
    if len(good) < KPI_GOOD_MIN:
        problems.append(f"{title}: планка короткая ({len(good)} < {KPI_GOOD_MIN}) — это лозунг, а не проверка")
    if len(bad) < KPI_BAD_MIN:
        problems.append(f"{title}: «не годно» короткое ({len(bad)} < {KPI_BAD_MIN}) — не названа дешёвая подделка")
    soft = [word for word in SOFT_WORDS if word in good.lower()]
    if soft and not CONCRETE.search(good):
        problems.append(f"{title}: мягкое слово «{soft[0]}» без единого проверяемого признака")
    if good in seen:
        problems.append(f"{title}: та же планка, что у {seen[good]} — значит она про раздел, а не про узел")
    else:
        seen[good] = title
    return problems


def check(graph: Graph, expansion_text: str) -> list[str]:
    """Every expected section exists, carries its fields, and none of them is empty or TODO."""
    problems: list[str] = []
    bars: dict[str, str] = {}
    sections = parse_expansion(expansion_text)
    clouds = cloud_blocks(expansion_text)
    for title, fields in expected_sections(graph).items():
        if title not in sections:
            problems.append(f"{title}: нет расшифровки")
            continue
        for field in fields:
            value = sections[title].get(field, "")
            if not value:
                problems.append(f"{title}: поле «{field}» пустое")
            elif value.strip().lower().startswith("todo"):
                problems.append(f"{title}: поле «{field}» не заполнено")
        if title.startswith("N"):
            for problem in check_kpi(sections[title].get("планка", ""), bars, title):
                problems.append(problem)
            block = clouds.get(title, "")
            cloud = parse_cloud(block)
            if not cloud.edges:
                # Свободная вёрстка: ядро и облако одной строкой. Смысл тот же, синтаксис другой.
                cloud = parse_inline(block)
            for problem in check_cloud(cloud):
                problems.append(f"{title}: {problem}")
    for title in sections:
        if title not in expected_sections(graph):
            problems.append(f"{title}: расшифровка есть, а в графе такого нет")
    return problems


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Expand a graph into a written description of its nodes.")
    parser.add_argument("--new", metavar="GRAPH", help="write a skeleton expansion for this graph")
    parser.add_argument("--check", metavar="GRAPH", help="check an expansion against this graph")
    parser.add_argument("-o", "--out", default="graph-expanded.md", help="where to write the skeleton")
    parser.add_argument("target", nargs="?", help="the expansion file to check")
    args = parser.parse_args(argv)

    if args.new:
        graph = load(Path(args.new))
        out = Path(args.out)
        out.write_text(skeleton(graph), encoding="utf-8")
        edges = sum(1 for edge in graph.edges if edge.kind not in STRUCTURAL_EDGES)
        print(f"написано {out}: узлов {len(graph.nodes)}, рёбер {edges}, осей {len(graph.axes())}")
        return 0

    if args.check:
        if not args.target:
            print("нужен файл расшифровки: --check graph.md expanded.md")
            return 2
        graph = load(Path(args.check))
        problems = check(graph, Path(args.target).read_text(encoding="utf-8"))
        if problems:
            print(f"дефектов: {len(problems)}")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("расшифровка полная: ИТОГ ЧИСТО")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
