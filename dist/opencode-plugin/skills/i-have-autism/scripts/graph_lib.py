"""Parse a graph file (format v1) into objects the other scripts can use.

The format is a Markdown file with a Mermaid block, a node table and an edge table; the contract
lives in references/graph-format.md. This module is the only place that knows the syntax — every
other script works on Graph objects, so a format change is one file, not seven.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

EDGE_TYPES = ("causes", "contrasts", "repeats", "contradicts", "answers")
# The table may be written in Russian; the graph keeps one canonical spelling so edges compare.
TYPE_ALIASES = {
    "причина": "causes",
    "контраст": "contrasts",
    "повтор": "repeats",
    "противоречие": "contradicts",
    "ответ": "answers",
    "отвечает": "answers",
}
NODE_FIELDS = ("what", "axis", "why", "anchor", "when")
NODE_FIELDS_RU = ("что", "ось", "почему важно", "подтверждено", "когда")

NODE_DECL = re.compile(r'^\s*(N\d+)\s*\["([^"]*)"\]\s*$', re.MULTILINE)
QUESTION_DECL = re.compile(r'^\s*(Q\d+)\s*\{\{"([^"]*)"\}\}\s*$', re.MULTILINE)
TYPED_EDGE = re.compile(r"^\s*([NQ]\d+)\s*--\s*([a-z]+)\s*-->\s*([NQ]\d+)\s*$", re.MULTILINE)
BARE_EDGE = re.compile(r"^\s*([NQ]\d+)\s*-->\s*([NQ]\d+)\s*$", re.MULTILINE)


class ParseError(ValueError):
    """The file does not follow the format; the message says which line and why."""


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    what: str
    axis: str
    why: str
    anchor: str
    when: str


@dataclass(frozen=True)
class Edge:
    src: str
    kind: str
    dst: str
    note: str


@dataclass
class Graph:
    title: str
    meta: dict[str, str] = field(default_factory=dict)
    questions: dict[str, str] = field(default_factory=dict)
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    mapping: list[tuple[str, str, list[str]]] = field(default_factory=list)
    # The same facts as drawn: compared against the tables by check_graph.py, never merged.
    stages: list[str] = field(default_factory=list)
    matrix: list[tuple[str, list[str]]] = field(default_factory=list)
    out_of_scope: list[tuple[str, str, str, str]] = field(default_factory=list)
    mermaid_nodes: dict[str, str] = field(default_factory=dict)
    mermaid_edges: list[tuple[str, str, str]] = field(default_factory=list)
    bare_edges: list[tuple[str, str]] = field(default_factory=list)

    # --- derived views -------------------------------------------------

    def answers(self, question: str) -> list[str]:
        return [e.dst for e in self.edges if e.kind == "answers" and e.src == question]

    def nodes_on(self, axis: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.axis == axis]

    def contradictions(self) -> list[Edge]:
        return [e for e in self.edges if e.kind == "contradicts"]

    def node_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if node_id in (e.src, e.dst)]

    def axes(self) -> list[str]:
        seen: list[str] = []
        for node in self.nodes.values():
            if node.axis and node.axis not in seen:
                seen.append(node.axis)
        return seen

    def reachable_from_questions(self) -> set[str]:
        """Nodes reachable from any question through answers + undirected graph edges."""
        adjacency: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge.kind == "answers":
                continue
            adjacency.setdefault(edge.src, set()).add(edge.dst)
            adjacency.setdefault(edge.dst, set()).add(edge.src)
        start = {n for q in self.questions for n in self.answers(q)}
        seen = set(start)
        frontier = list(start)
        while frontier:
            current = frontier.pop()
            for neighbour in adjacency.get(current, ()):  # type: ignore[arg-type]
                if neighbour not in seen:
                    seen.add(neighbour)
                    frontier.append(neighbour)
        return seen


def _sections(text: str, heading: str) -> str:
    """Все блоки с этим заголовком: план крупного графа разбит по сезонам на несколько таблиц."""
    return "\n".join(_section(text, heading, index=i) for i in range(len(_headings(text, heading))))


def _headings(text: str, heading: str) -> list[int]:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\b.*$", re.MULTILINE)
    return [m.start() for m in pattern.finditer(text)]


def _section(text: str, heading: str, index: int = 0) -> str:
    """Return the body of a `## heading` section, up to the next heading of the same level."""
    # Заголовок может иметь уточнение: «## Переход в план: первый сезон» — это тот же раздел.
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\b.*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    rest = text[match.end():]
    stop = re.search(r"^##\s+\S", rest, re.MULTILINE)
    return rest[: stop.start()] if stop else rest


REGISTER_STATUSES = ("в работе", "отдельная часть", "отдельный сезон", "отдельный проект", "не относится", "нет данных")
AGGRESSIVE_MARKER = "агрессивный"


def is_aggressive(graph: "Graph") -> bool:
    return AGGRESSIVE_MARKER in graph.meta.get("режим", "").lower()


def _matrix_block(text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Read the coverage matrix: header cells are stages, each row is an axis."""
    block = _section(text, "Матрица покрытия")
    rows = [line.strip() for line in block.splitlines() if line.strip().startswith("|")]
    if not rows:
        return [], []
    header = [cell.strip() for cell in rows[0].strip("|").split("|")][1:]
    matrix: list[tuple[str, list[str]]] = []
    for line in rows[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        matrix.append((cells[0], cells[1:]))
    return header, matrix


def _register(text: str) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    for row in _table_rows(_section(text, "Вне рамок")):
        if len(row) < 4:
            continue
        entries.append((row[0], row[1], row[2], row[3]))
    return entries


def _table_rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0].lower() in ("id", "от", "часть", "элемент", "ось", "этап"):
            continue
        rows.append(cells)
    return rows


def parse(text: str, source: str = "<graph>") -> Graph:
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    graph = Graph(title=title_match.group(1).strip() if title_match else source)

    for line in _section(text, "Метаданные").splitlines():
        stripped = line.strip().lstrip("-").strip()
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            graph.meta[key.strip().lower()] = value.strip()

    mermaid = "\n".join(re.findall(r"```mermaid\n(.*?)```", text, re.S))
    if not mermaid:
        raise ParseError(f"{source}: нет блока ```mermaid")

    for qid, label in QUESTION_DECL.findall(mermaid):
        graph.questions[qid] = label
    labels = dict(NODE_DECL.findall(mermaid))
    graph.mermaid_nodes = dict(labels)
    graph.mermaid_edges = [tuple(match) for match in TYPED_EDGE.findall(mermaid)]
    graph.bare_edges = [tuple(match) for match in BARE_EDGE.findall(mermaid)]

    for row in _table_rows(_section(text, "Узлы")):
        if len(row) != 6:
            raise ParseError(f"{source}: узел {row[0]} — {len(row)} колонок вместо шести: {row}")
        node_id, what, axis, why, anchor, when = row
        graph.nodes[node_id] = Node(
            id=node_id,
            label=labels.get(node_id, what),
            what=what,
            axis=axis,
            why=why,
            anchor=anchor,
            when=when,
        )

    for row in _table_rows(_section(text, "Рёбра")):
        if len(row) != 4:
            raise ParseError(f"{source}: ребро {row} — {len(row)} колонок вместо четырёх")
        kind = TYPE_ALIASES.get(row[1].strip().lower(), row[1].strip().lower())
        graph.edges.append(Edge(src=row[0], kind=kind, dst=row[2], note=row[3]))

    graph.stages, graph.matrix = _matrix_block(text)
    graph.out_of_scope = _register(text)

    for row in _table_rows(_sections(text, "Переход в план")):
        if len(row) < 3:
            continue
        node_ids = [part.strip() for part in row[-1].split(",") if part.strip()]
        graph.mapping.append((row[0], row[1], node_ids))
    return graph


def load(path: str | Path) -> Graph:
    path = Path(path)
    return parse(path.read_text(encoding="utf-8"), source=str(path))


def mermaid_block(text: str) -> str:
    """The raw Mermaid source, for the renderer."""
    blocks = re.findall(r"```mermaid\n(.*?)```", text, re.S)
    if not blocks:
        raise ParseError("нет блока ```mermaid")
    return "\n".join(blocks)
