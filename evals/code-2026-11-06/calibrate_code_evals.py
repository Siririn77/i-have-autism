"""Calibration: a reference implementation must pass every hidden test.

A test suite no correct implementation can pass is a broken test, not a hard task. This runs the
reference against the same suites the models face.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_code_evals import run_tests  # noqa: E402

SLUGIFY = '''import re

WORD = re.compile(r"[^\\W_]+", re.UNICODE)


def slugify(text: str) -> str:
    words = WORD.findall(text.lower())
    result = ""
    for word in words:
        candidate = word if not result else result + "-" + word
        if len(candidate) > 60:
            if not result:
                return word[:60]
            break
        result = candidate
    return result
'''

CHUNKED = '''def chunked(items, size):
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError(f"size must be an int, got {size!r}")
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    chunks = []
    current = []
    for item in items:
        current.append(item)
        if len(current) == size:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks
'''

CSV_LINE = '''def parse_csv_line(line: str) -> list[str]:
    if line.startswith("\\ufeff"):
        line = line[1:]
    if line == "":
        return []
    fields = []
    field = []
    index = 0
    in_quotes = False
    closed = False
    while index < len(line):
        char = line[index]
        if in_quotes:
            if char == '"':
                if index + 1 < len(line) and line[index + 1] == '"':
                    field.append('"')
                    index += 2
                    continue
                in_quotes = False
                closed = True
                index += 1
                continue
            field.append(char)
            index += 1
            continue
        if char == '"':
            if field:
                raise ValueError(f"quote inside an unquoted field at position {index}")
            in_quotes = True
            closed = False
            index += 1
            continue
        if char == ",":
            if closed:
                closed = False
            fields.append("".join(field))
            field = []
            index += 1
            continue
        if closed:
            raise ValueError(f"unexpected character after a closing quote at position {index}")
        field.append(char)
        index += 1
    if in_quotes:
        raise ValueError("unclosed quote")
    fields.append("".join(field))
    return fields
'''

MERGE = '''def merge_intervals(intervals):
    pairs = []
    for item in intervals:
        start, end = item
        if start > end:
            raise ValueError(f"invalid interval: start {start} is greater than end {end}")
        pairs.append((start, end))
    pairs.sort()
    merged = []
    for start, end in pairs:
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged
'''

RATE_LIMITER = '''import threading
import time


class RateLimiter:
    def __init__(self, rate, per_seconds, clock=None):
        if isinstance(rate, bool) or not isinstance(rate, int) or rate <= 0:
            raise ValueError(f"rate must be a positive int, got {rate!r}")
        if per_seconds <= 0:
            raise ValueError(f"per_seconds must be positive, got {per_seconds!r}")
        self.rate = rate
        self.per_seconds = per_seconds
        self.clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._tokens = {}
        self._stamps = {}

    def _refill(self, key):
        now = self.clock()
        if key not in self._tokens:
            self._tokens[key] = float(self.rate)
            self._stamps[key] = now
            return
        elapsed = now - self._stamps[key]
        if elapsed > 0:
            self._tokens[key] = min(float(self.rate), self._tokens[key] + elapsed * self.rate / self.per_seconds)
            self._stamps[key] = now

    def allow(self, key, cost=1):
        if isinstance(cost, bool) or not isinstance(cost, int) or cost <= 0:
            raise ValueError(f"cost must be a positive int, got {cost!r}")
        if cost > self.rate:
            raise ValueError(f"cost {cost} exceeds capacity {self.rate}")
        with self._lock:
            self._refill(key)
            if self._tokens[key] >= cost:
                self._tokens[key] -= cost
                return True
            return False

    def state(self, key):
        with self._lock:
            self._refill(key)
            return {"tokens": round(self._tokens[key], 3), "capacity": self.rate}

    def reset(self, key):
        with self._lock:
            self._tokens[key] = float(self.rate)
            self._stamps[key] = self.clock()
'''

REFERENCES = {
    "rate_limiter": RATE_LIMITER,
    "slugify": SLUGIFY,
    "chunked": CHUNKED,
    "csv_line": CSV_LINE,
    "merge_intervals": MERGE,
}


def main() -> int:
    cases = {case["id"]: case for case in json.loads((Path(__file__).parent / "code_cases.json").read_text("utf-8"))}
    failures = 0
    for case_id, code in REFERENCES.items():
        result = run_tests(code, cases[case_id]["tests"])
        status = "OK" if result["passed"] else "FAIL"
        print(f"{case_id:16} {status:4} тестов {result['tests']}")
        if not result["passed"]:
            print(result["detail"])
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
