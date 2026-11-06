"""Reference implementation for the mini_db hard case.

Its only job is to prove the hidden suite is passable. If the reference cannot pass, the test is the
defect — not the model.
"""
import json
import os
import zlib


class ConflictError(Exception):
    """Запись, которую меняет транзакция, уже изменена после её начала."""


def _encode(record: dict) -> str:
    body = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return f"{zlib.crc32(body.encode('utf-8')):08x}\t{body}\n"


def _decode(line: str) -> dict | None:
    """None for a torn or corrupt line — the journal keeps everything before it."""
    checksum, _, body = line.partition("\t")
    body = body.rstrip("\n")
    if not body:
        return None
    if f"{zlib.crc32(body.encode('utf-8')):08x}" != checksum:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


class Database:
    def __init__(self, path: str | None = None):
        self.path = path
        self._rows: dict[str, dict[int, dict]] = {}
        self._versions: dict[int, int] = {}
        self._next_id = 1
        self._seq = 0
        self._closed = False
        if path and os.path.exists(path):
            self._replay()

    def _replay(self) -> None:
        assert self.path is not None
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.endswith("\n"):
                    break  # torn tail: everything after it is untrustworthy
                record = _decode(line)
                if record is None:
                    continue
                self._apply(record)

    def _apply(self, record: dict) -> None:
        if record["seq"] > self._seq:
            self._seq = record["seq"]
        for table, row_id, row in record.get("puts", []):
            self._rows.setdefault(table, {})[row_id] = row
            self._versions[row_id] = record["seq"]
            self._next_id = max(self._next_id, row_id + 1)
        for table, row_id in record.get("deletes", []):
            self._rows.get(table, {}).pop(row_id, None)
            self._versions[row_id] = record["seq"]

    def begin(self) -> "Transaction":
        if self._closed:
            raise RuntimeError("database is closed")
        snapshot = {
            table: {row_id: dict(row) for row_id, row in rows.items()}
            for table, rows in self._rows.items()
        }
        return Transaction(self, snapshot, self._seq)

    def _commit(self, transaction: "Transaction") -> None:
        for table, row_id, _ in transaction.puts:
            if row_id in transaction.snapshot.get(table, {}):
                if self._versions.get(row_id, 0) > transaction.base_seq:
                    raise ConflictError(f"row {row_id} in {table} changed after this transaction began")
        for table, row_id in transaction.deletes:
            if self._versions.get(row_id, 0) > transaction.base_seq:
                raise ConflictError(f"row {row_id} in {table} changed after this transaction began")

        seq = self._seq + 1
        record = {"seq": seq, "puts": transaction.puts, "deletes": transaction.deletes}
        if self.path:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(_encode(record))
                handle.flush()
                os.fsync(handle.fileno())
        self._apply(record)

    def close(self) -> None:
        self._closed = True


class Transaction:
    def __init__(self, database: Database, snapshot: dict, base_seq: int):
        self._db = database
        self.snapshot = snapshot
        self.base_seq = base_seq
        self.puts: list[list] = []
        self.deletes: list[list] = []
        self._dead = False
        self._pending: dict[str, dict[int, dict]] = {}

    def _check_alive(self) -> None:
        if self._dead:
            raise RuntimeError("transaction is finished")

    def _view(self, table: str) -> dict[int, dict]:
        view = dict(self.snapshot.get(table, {}))
        for pending_table, pending_id, row in self.puts:
            if pending_table == table:
                view[pending_id] = dict(row)
        for pending_table, pending_id in self.deletes:
            if pending_table == table:
                view.pop(pending_id, None)
        return view

    def insert(self, table: str, row: dict) -> int:
        self._check_alive()
        row_id = self._db._next_id
        self._db._next_id += 1
        stored = {key: value for key, value in row.items() if key != "_id"}
        stored["_id"] = row_id
        self.puts.append([table, row_id, stored])
        return row_id

    def select(self, table: str, where: dict | None = None) -> list[dict]:
        view = self._view(table)
        rows = [dict(row) for _, row in sorted(view.items())]
        if where:
            rows = [row for row in rows if all(row.get(key) == value for key, value in where.items())]
        return rows

    def update(self, table: str, where: dict, changes: dict) -> int:
        self._check_alive()
        if "_id" in changes:
            raise ValueError("_id cannot be changed")
        view = self._view(table)
        touched = [
            row_id
            for row_id, row in view.items()
            if all(row.get(key) == value for key, value in where.items())
        ]
        for row_id in touched:
            updated = dict(view[row_id])
            updated.update(changes)
            self.puts.append([table, row_id, updated])
        return len(touched)

    def delete(self, table: str, where: dict) -> int:
        self._check_alive()
        view = self._view(table)
        touched = [
            row_id
            for row_id, row in view.items()
            if all(row.get(key) == value for key, value in where.items())
        ]
        for row_id in touched:
            self.deletes.append([table, row_id])
        return len(touched)

    def commit(self) -> None:
        self._check_alive()
        self._db._commit(self)
        self._dead = True

    def rollback(self) -> None:
        self._check_alive()
        self._dead = True
