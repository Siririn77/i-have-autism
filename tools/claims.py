#!/usr/bin/env python3
"""The claims ledger: a number enters the text only with work, journal, year and status.

Why a checker and not a habit. Twice in one day a model attributed a paper to the wrong journal —
the figure was right, the journal was not — and every check that looked for words in the text passed,
because the words were there. The defect lives in the cell, not in the sentence, so it has to be caught
where the cell is: in the ledger, before the prose is written.

The table this reads has one row per claim:

    | утверждение | работа | журнал | год | статус | источник |

`год` is four digits, `статус` comes from a closed list, `источник` must look like a domain or a URL.
Anything else is a defect and the checker says which cell and why.

    python3 tools/claims.py ledger.md            # check
    python3 tools/claims.py --template ledger.md # write an empty table, do not overwrite
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

COLUMNS = ("утверждение", "работа", "журнал", "год", "статус", "источник")
STATUSES = ("установлено", "вероятно", "возможно", "не проверено", "не подтверждено", "опровергнуто")
YEAR = re.compile(r"^(1[89]\d\d|20\d\d)$")
SOURCE = re.compile(r"(https?://|[\w-]+\.(?:com|org|net|ru|io|co|uk|de|fr|edu|gov)\b)")
HEADER = "| " + " | ".join(COLUMNS) + " |\n|" + "---|" * len(COLUMNS) + "\n"
TEMPLATE = (
    "# Реестр утверждений\n\n"
    "Одна строка на утверждение. Цифра без строки в реестре в текст не попадает.\n\n"
    + HEADER
    + "| TODO | TODO | TODO | TODO | не проверено | TODO |\n"
)


def table_rows(text: str) -> list[list[str]]:
    """Every data row of the first table whose header has all six columns."""
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if not lines:
        return []
    header = [cell.strip().lower() for cell in lines[0].strip("|").split("|")]
    if [name for name in COLUMNS if name in header] != list(COLUMNS):
        return []
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(COLUMNS):
            rows.append(cells)
    return rows


def check(text: str) -> list[str]:
    """One defect per missing or malformed cell, named by row and column."""
    problems: list[str] = []
    rows = table_rows(text)
    if not rows:
        return ["таблицы реестра нет: нужны колонки " + ", ".join(COLUMNS)]
    for number, row in enumerate(rows, start=1):
        claim = row[0] or f"строка {number}"
        for column, value in zip(COLUMNS, row):
            if not value or value.lower() == "todo":
                problems.append(f"{claim}: пустая ячейка «{column}»")
        work, journal, year, status, source = row[1], row[2], row[3], row[4].lower(), row[5]
        if work and work.lower() != "todo" and len(work.split()) < 2:
            problems.append(f"{claim}: «работа» — одно слово, нужны автор и название")
        if journal and journal.lower() != "todo" and len(journal.split()) > 8:
            problems.append(f"{claim}: «журнал» похож на пересказ, а не на название")
        if year and year.lower() != "todo" and not YEAR.match(year):
            problems.append(f"{claim}: год «{year}» не четыре цифры")
        if status and status != "todo" and status not in STATUSES:
            problems.append(f"{claim}: статус «{status}» не из списка {', '.join(STATUSES)}")
        if source and source.lower() != "todo" and not SOURCE.search(source):
            problems.append(f"{claim}: источник «{source}» не похож на домен или ссылку")
    return problems


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--template":
        target = Path(argv[1]) if len(argv) > 1 else Path("ledger.md")
        if target.exists():
            print(f"{target} уже есть — не перезаписываю")
            return 1
        target.write_text(TEMPLATE, encoding="utf-8")
        print(f"написано {target}: пустая таблица, шесть колонок")
        return 0
    problems = check(Path(argv[0]).read_text(encoding="utf-8"))
    if problems:
        print(f"дефектов: {len(problems)}")
        for problem in problems:
            print("  -", problem)
        return 1
    print("реестр полный: ИТОГ ЧИСТО")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
