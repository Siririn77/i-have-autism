"""The cloud: the composition of one node, as a tiny graph whose edges carry the meaning.

A master graph answers "what is connected to what" across a whole work. A cloud answers "what is inside
this one node" — and it stays deliberately poorer than the graph: no axes, no anchors, no root questions.
The only thing an edge carries is a verb from a closed list, because an edge whose label is a sentence is
prose with an arrow drawn next to it.

    ### Облако
    - ядро: политика исключения
    | элемент | связь | с чем |
    |---|---|---|
    | политика исключения | предшествует | изоляция |
    | изоляция | предшествует | гетто |

Eight verbs, not more:

    включает          состав: часть внутри целого
    предшествует      порядок: одно раньше другого
    вызывает          причину, а не просто соседство
    усиливает         тот же эффект, но сильнее
    противопоставлен  контраст: два начала спорят
    цена              чем это оплачено
    пример            частный случай общего
    доказательство    чем это подтверждено
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

RELATIONS = (
    "включает",
    "предшествует",
    "вызывает",
    "усиливает",
    "противопоставлен",
    "цена",
    "пример",
    "доказательство",
)
MIN_ELEMENTS = 3
MAX_ELEMENTS = 9
CORE = re.compile(r"^[-*]\s*ядро:\s*(.+)$", re.MULTILINE)


@dataclass
class Cloud:
    core: str = ""
    elements: list[str] = field(default_factory=list)
    edges: list[tuple[str, str, str]] = field(default_factory=list)


def parse(block: str) -> Cloud:
    """Read the cloud block. Rows outside the four-column table are ignored."""
    cloud = Cloud()
    found = CORE.search(block)
    if found:
        cloud.core = found.group(1).strip()
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3 or cells[0].lower() in ("элемент",) or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    for source, relation, target in rows:
        cloud.edges.append((source, relation.lower(), target))
        for element in (source, target):
            if element and element not in cloud.elements:
                cloud.elements.append(element)
    if cloud.core and cloud.core not in cloud.elements:
        cloud.elements.insert(0, cloud.core)
    return cloud


INLINE_CORE = re.compile(r"\*\*Ядро:\*\*\s*(.+)", re.IGNORECASE)
INLINE_CLOUD = re.compile(r"\*\*Облако:\*\*\s*(.+)", re.IGNORECASE | re.DOTALL)
INLINE_ITEM = re.compile(r"(?:^|;)\s*(.+?)\s*[—-]\s*\*([а-яё]+)\*", re.IGNORECASE)


def parse_inline(block: str) -> Cloud:
    """The free-form variant a model writes by itself: `**Ядро:** X` and `**Облако:** a — *verb*; b — *verb*`.

    The meaning is the same; only the typography differs. A checker that rejects this rejects the best
    text in the set for the shape of its headings, which is not what a contract is for.
    """
    cloud = Cloud()
    core = INLINE_CORE.search(block)
    if core:
        cloud.core = core.group(1).strip().rstrip(".")
    body = INLINE_CLOUD.search(block)
    if not body:
        return cloud
    text = body.group(1).split("**")[0]
    items = INLINE_ITEM.findall(text)
    if not items:
        return cloud
    if not cloud.core:
        cloud.core = items[0][0]
    cloud.elements.append(cloud.core)
    # В свободной вёрстке глагол при элементе описывает его связь с самим узлом, а не с соседом:
    # «1,91 млн — *доказательство*» значит «это доказательство для узла». Отсюда звезда от ядра.
    for element, relation in items:
        element = element.strip()
        if element and element not in cloud.elements:
            cloud.elements.append(element)
        if element and element != cloud.core:
            cloud.edges.append((cloud.core, relation.strip().lower(), element))
    return cloud


def check(cloud: Cloud) -> list[str]:
    """A cloud is a single connected piece with a core, a known verb on every edge, and a readable size."""
    problems: list[str] = []
    if not cloud.core:
        problems.append("облако: не названо ядро")
    if not cloud.edges:
        problems.append("облако: ни одной связи")
        return problems
    if len(cloud.elements) < MIN_ELEMENTS:
        problems.append(f"облако: {len(cloud.elements)} элемента при норме {MIN_ELEMENTS} — это записка, а не облако")
    if len(cloud.elements) > MAX_ELEMENTS:
        problems.append(f"облако: {len(cloud.elements)} элементов при пределе {MAX_ELEMENTS} — читать невозможно")

    seen: set[tuple[str, str, str]] = set()
    for source, relation, target in cloud.edges:
        if relation not in RELATIONS:
            problems.append(f"облако: связь «{relation}» не из списка ({', '.join(RELATIONS)})")
        if source == target:
            problems.append(f"облако: {source} связан сам с собой")
        if (source, relation, target) in seen:
            problems.append(f"облако: повтор связи {source} —{relation}→ {target}")
        seen.add((source, relation, target))

    if cloud.core:
        neighbours: dict[str, set[str]] = {element: set() for element in cloud.elements}
        for source, _, target in cloud.edges:
            neighbours.setdefault(source, set()).add(target)
            neighbours.setdefault(target, set()).add(source)
        reached = {cloud.core}
        queue = [cloud.core]
        while queue:
            current = queue.pop()
            for neighbour in neighbours.get(current, set()):
                if neighbour not in reached:
                    reached.add(neighbour)
                    queue.append(neighbour)
        for element in cloud.elements:
            if element not in reached:
                problems.append(f"облако: «{element}» не соединён с ядром — остров")
    return problems


def stats(cloud: Cloud) -> dict[str, object]:
    by_relation: dict[str, int] = {}
    for _, relation, _ in cloud.edges:
        by_relation[relation] = by_relation.get(relation, 0) + 1
    return {
        "core": cloud.core,
        "elements": len(cloud.elements),
        "edges": len(cloud.edges),
        "relations": by_relation,
    }
