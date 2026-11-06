#!/usr/bin/env python3
"""Start a graph file from a task line: the skeleton, not the content.

Usage: python3 scripts/graph_new.py "сериал про Мидуэй" --kind history --out graph.md

What it does and does not do. It writes the structure the format requires — metadata, five empty root
questions, the axis presets for the kind of work, an empty node table, an empty edge table, the plan
mapping table — so the first hour goes into answering questions instead of remembering headings. It does
**not** invent nodes: an invented node has no anchor, and a graph of guesses is worse than no graph.

Kinds and their default axes:
  history  — дипломатия · операция · экономика · технология · человек · память
  code     — входы · данные · отказы · контракты · поставка
  lecture  — тезисы · доказательства · возражения · примеры
  fiction  — мир · конфликт · персонажи · цена · финал
"""
from __future__ import annotations

import sys
from pathlib import Path

AXES = {
    "history": ["дипломатия", "операция", "экономика", "технология", "человек", "память"],
    "code": ["входы", "данные", "отказы", "контракты", "поставка"],
    "lecture": ["тезисы", "доказательства", "возражения", "примеры"],
    "fiction": ["мир", "конфликт", "персонажи", "цена", "финал"],
}
TEMPLATE = """# Граф «__TASK__»

## Метаданные
- задача: TODO — что за работа одной строкой
- бюджет узлов: TODO — 3–5 для разовой задачи, 40–60 на часть фильма
- части: TODO — сколько единиц крупного размера в работе

## Корневые вопросы
1. **TODO — вопрос, на который отвечает работа?**
2. **TODO — второй вопрос?**
3. **TODO — третий вопрос?**
4. **TODO — четвёртый вопрос (если нужен)?**
5. **TODO — пятый вопрос (если нужен)?**

Оси: __AXES__

## Мастер-граф

```mermaid
graph LR
  Q1{{"TODO первый вопрос?"}}
  Q2{{"TODO второй вопрос?"}}
  Q3{{"TODO третий вопрос?"}}
  Q4{{"TODO четвёртый вопрос?"}}
  Q5{{"TODO пятый вопрос?"}}
  N1["TODO первый узел"]
  Q1 -- answers --> N1
```

## Узлы

| id | что | ось | почему важно | подтверждено | когда |
|---|---|---|---|---|---|
| N1 | TODO | __FIRST_AXIS__ | TODO — ставка читателя | TODO — источник или архив | TODO — дата |

## Рёбра

| от | тип | к | что это значит |
|---|---|---|---|
| Q1 | answers | N1 | узел существует, чтобы ответить на этот вопрос |

## Переход в план

| часть | тема | узлы |
|---|---|---|
| 1 | TODO | N1 |
"""


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    task = argv[0]
    kind = "history"
    out: Path | None = None
    for index, arg in enumerate(argv):
        if arg == "--kind":
            kind = argv[index + 1]
        if arg == "--out":
            out = Path(argv[index + 1])
    if kind not in AXES:
        print(f"неизвестный вид работы: {kind}. Есть: {', '.join(AXES)}")
        return 2

    text = (
        TEMPLATE.replace("__TASK__", task)
        .replace("__AXES__", " · ".join(AXES[kind]))
        .replace("__FIRST_AXIS__", AXES[kind][0])
    )
    target = out or Path("graph.md")
    if target.exists():
        print(f"{target} уже существует — не перезаписываю. Возьмите другой путь.")
        return 1
    target.write_text(text, encoding="utf-8")
    print(f"написано {target}: вопросов пять (TODO), узлов один (TODO), осей {len(AXES[kind])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
