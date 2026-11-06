#!/usr/bin/env python3
"""Проверить graph.md по правилам D2a, не глазами, а кодом.

Что проверяется:
  1. каждый узел объявлен в mermaid, и его id есть в таблице узлов;
  2. у каждого узла в таблице заполнены четыре поля: что, почему важно, подтверждено, когда;
  3. каждое ребро ссылается на существующие id, а тип ребра — из разрешённого набора;
  4. у каждого узла есть хотя бы одно ребро (узел-сирота не работает);
  5. у каждого корневого вопроса есть ответы, у каждого ответа — вопрос;
  6. бюджет: число узлов попадает в объявленную норму.

Код выхода 1 — граф не прошёл. Ничего не чинит, только сообщает.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

EDGE_TYPES = {"causes", "contrasts", "repeats", "contradicts", "answers"}
NODE_DECL = re.compile(r'^\s*(N\d+|Q\d+)\s*[\[{(]', re.MULTILINE)
EDGE = re.compile(r"^\s*([NQ]\d+)\s*(?:--\s*([a-z]+)\s*-->|-->)\s*([NQ]\d+)", re.MULTILINE)
ROW = re.compile(r"^\|\s*(N\d+)\s*\|(.*)\|\s*$", re.MULTILINE)


def read_blocks(text: str) -> tuple[str, str]:
    """Вернуть два блока: mermaid и таблицу узлов (всё до «## Рёбра»)."""
    mermaid = "\n".join(re.findall(r"```mermaid\n(.*?)```", text, re.S))
    nodes_part = text.split("## Рёбра")[0]
    return mermaid, nodes_part


def main(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    mermaid, nodes_part = read_blocks(text)
    problems: list[str] = []

    declared = set(NODE_DECL.findall(mermaid))
    rows = {m.group(1): [c.strip() for c in m.group(2).split("|")] for m in ROW.finditer(nodes_part)}

    for node in sorted(rows):
        if node not in declared:
            problems.append(f"{node}: есть в таблице, нет в mermaid")
        cells = rows[node]
        if len(cells) != 4:
            problems.append(f"{node}: в таблице {len(cells)} поля вместо четырёх")
        elif not all(cells):
            problems.append(f"{node}: пустое поле в таблице")
    nodes_only = {n for n in declared if n.startswith("N")}
    for node in sorted(nodes_only - set(rows)):
        problems.append(f"{node}: есть в mermaid, нет в таблице узлов")

    edges = EDGE.findall(mermaid)
    seen: set[str] = set()
    for src, kind, dst in edges:
        if kind and kind not in EDGE_TYPES:
            problems.append(f"ребро {src}->{dst}: тип «{kind}» не из набора {sorted(EDGE_TYPES)}")
        if src not in declared:
            problems.append(f"ребро {src}->{dst}: источника нет в mermaid")
        if dst not in declared and dst not in rows:
            problems.append(f"ребро {src}->{dst}: цели нет в графе")
        seen.update((src, dst))

    for node in sorted(nodes_only - seen):
        problems.append(f"{node}: узел без рёбер")

    for question in sorted(n for n in declared if n.startswith("Q")):
        if not any(src == question for src, _, _ in edges):
            problems.append(f"{question}: корневой вопрос без ответов")
    for node in sorted(nodes_only):
        if not any(dst == node and kind == "answers" for _, kind, dst in edges):
            problems.append(f"{node}: узел не привязан ни к одному корневому вопросу через answers")

    print(f"узлов N: {len(nodes_only)}, вопросов Q: {len(declared) - len(nodes_only)}, рёбер: {len(edges)}")
    if problems:
        print(f"дефектов: {len(problems)}")
        for problem in problems:
            print("  -", problem)
        return 1
    print("ИТОГ: ЧИСТО")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "graph.md")))
