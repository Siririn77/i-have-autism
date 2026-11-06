import copy
import hashlib
import json
import os


class ConflictError(Exception):
    pass


def _matches(row, where):
    for key, value in where.items():
        if key not in row or row[key] != value:
            return False
    return True


class Database:
    def __init__(self, path=None):
        self._path = os.fspath(path) if path is not None else None
        self._tables = {}
        self._versions = {}
        self._version = 0
        self._next_id = 1
        self._closed = False

        if self._path is not None:
            parent = os.path.dirname(os.path.abspath(self._path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._load()

    def _load(self):
        if self._path is None or not os.path.exists(self._path):
            return

        with open(self._path, "rb") as f:
            data = f.read()

        offset = 0
        total = len(data)

        while offset < total:
            newline = data.find(b"\n", offset)
            if newline == -1:
                raw = data[offset:]
                next_offset = total
            else:
                raw = data[offset:newline]
                next_offset = newline + 1

            if raw.strip():
                try:
                    text = raw.decode("utf-8")
                    outer = json.loads(text)

                    if not isinstance(outer, dict):
                        raise ValueError

                    payload = outer.get("r")
                    digest = outer.get("h")

                    if not isinstance(payload, dict) or not isinstance(digest, str):
                        raise ValueError

                    body = json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )

                    if hashlib.sha256(body.encode("utf-8")).hexdigest() != digest:
                        raise ValueError

                    self._apply_record(payload)
                except Exception:
                    # Повреждённый хвост отбрасываем, чтобы следующие
                    # commit-ы можно было безопасно дописывать в файл.
                    self._truncate_to(offset)
                    break

            offset = next_offset

    def _truncate_to(self, offset):
        if self._path is None:
            return
        with open(self._path, "r+b") as f:
            f.truncate(offset)
            f.flush()
            os.fsync(f.fileno())

    def _apply_record(self, rec):
        kind = rec.get("t")

        if kind == "a":
            ident = rec.get("id")
            if not isinstance(ident, int) or isinstance(ident, bool) or ident < 1:
                raise ValueError
            if ident + 1 > self._next_id:
                self._next_id = ident + 1

        elif kind == "c":
            ops = rec.get("ops")
            if not isinstance(ops, list):
                raise ValueError

            version = self._version + 1
            for op in ops:
                self._apply_op(op, version, strict=True)
            self._version = version

        else:
            raise ValueError

    def _apply_op(self, op, version, strict=False):
        if not isinstance(op, dict):
            raise ValueError

        kind = op.get("o")
        table = op.get("table")
        ident = op.get("id")

        if not isinstance(table, str):
            raise ValueError
        if not isinstance(ident, int) or isinstance(ident, bool) or ident < 1:
            raise ValueError

        if kind in ("i", "u"):
            row = op.get("row")
            if not isinstance(row, dict):
                raise ValueError
            if row.get("_id") != ident:
                raise ValueError

            if strict and kind == "u":
                if table not in self._tables or ident not in self._tables[table]:
                    raise ValueError

            self._tables.setdefault(table, {})[ident] = copy.deepcopy(row)
            self._versions.setdefault(table, {})[ident] = version

            if kind == "i" and ident + 1 > self._next_id:
                self._next_id = ident + 1

        elif kind == "d":
            if strict:
                if table not in self._tables or ident not in self._tables[table]:
                    raise ValueError

            self._tables.get(table, {}).pop(ident, None)
            self._versions.get(table, {}).pop(ident, None)

        else:
            raise ValueError

    def _append_record(self, payload):
        if self._path is None:
            return
        if self._closed:
            raise RuntimeError("database is closed")

        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()

        outer = {"r": payload, "h": digest}
        line = json.dumps(
            outer,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ) + "\n"

        with open(self._path, "ab") as f:
            f.write(line.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())

    def _apply_commit_ops(self, ops, version):
        for op in ops:
            self._apply_op(op, version, strict=False)

    def _allocate_id(self):
        ident = self._next_id
        self._next_id += 1
        return ident

    def begin(self):
        if self._closed:
            raise RuntimeError("database is closed")
        return Transaction(self)

    def close(self):
        self._closed = True


class Transaction:
    def __init__(self, db):
        self.db = db
        self.begin_version = db._version

        self._snapshot_tables = copy.deepcopy(db._tables)
        self._tables = copy.deepcopy(self._snapshot_tables)

        self._inserted = set()
        self._touched = set()
        self._ops = []

        self._active = True
        self._terminated_tables = None

    def _ensure_active(self):
        if not self._active:
            raise RuntimeError("transaction is closed")

    def _view_tables(self):
        if self._active:
            return self._tables
        return self._terminated_tables if self._terminated_tables is not None else {}

    def insert(self, table, row):
        self._ensure_active()

        if not isinstance(table, str):
            raise TypeError("table must be a string")
        if not isinstance(row, dict):
            raise TypeError("row must be a dict")

        ident = self.db._allocate_id()

        if self.db._path is not None:
            self.db._append_record({"t": "a", "id": ident})

        stored = copy.deepcopy(row)
        stored["_id"] = ident

        self._tables.setdefault(table, {})[ident] = stored
        self._inserted.add((table, ident))
        self._ops.append({
            "o": "i",
            "table": table,
            "id": ident,
            "row": copy.deepcopy(stored),
        })

        return ident

    def select(self, table, where=None):
        if not isinstance(table, str):
            return []

        tables = self._view_tables()
        rows = tables.get(table)

        if not rows:
            return []

        where = where or {}
        result = []

        for ident in sorted(rows):
            row = rows[ident]
            if _matches(row, where):
                result.append(copy.deepcopy(row))

        return result

    def update(self, table, where, changes):
        self._ensure_active()

        if not isinstance(table, str):
            raise TypeError("table must be a string")
        if not isinstance(changes, dict):
            raise TypeError("changes must be a dict")
        if "_id" in changes:
            raise ValueError("_id cannot be changed")

        where = where or {}
        rows = self._tables.get(table)

        if not rows or not changes:
            return 0

        matched = sorted(
            ident for ident, row in rows.items()
            if _matches(row, where)
        )

        for ident in matched:
            if (table, ident) not in self._inserted:
                self._touched.add((table, ident))

            new_row = copy.deepcopy(rows[ident])
            new_row.update(copy.deepcopy(changes))
            new_row["_id"] = ident

            rows[ident] = new_row
            self._ops.append({
                "o": "u",
                "table": table,
                "id": ident,
                "row": copy.deepcopy(new_row),
            })

        return len(matched)

    def delete(self, table, where):
        self._ensure_active()

        if not isinstance(table, str):
            raise TypeError("table must be a string")

        where = where or {}
        rows = self._tables.get(table)

        if not rows:
            return 0

        matched = sorted(
            ident for ident, row in rows.items()
            if _matches(row, where)
        )

        for ident in matched:
            if (table, ident) in self._inserted:
                self._inserted.discard((table, ident))
            else:
                self._touched.add((table, ident))

            del rows[ident]
            self._ops.append({
                "o": "d",
                "table": table,
                "id": ident,
            })

        return len(matched)

    def _check_conflicts(self):
        for table, ident in self._touched:
            rows = self.db._tables.get(table)

            if rows is None or ident not in rows:
                raise ConflictError("row was deleted by another transaction")

            version = self.db._versions.get(table, {}).get(ident)

            if version is None or version > self.begin_version:
                raise ConflictError("row was modified by another transaction")

    def commit(self):
        self._ensure_active()

        ops = self._ops

        if ops:
            self._check_conflicts()

            version = self.db._version + 1

            # Сначала журнал на диск, только потом применение к памяти.
            self.db._append_record({"t": "c", "ops": ops})
            self.db._apply_commit_ops(ops, version)
            self.db._version = version

        self._active = False
        self._terminated_tables = self._tables

    def rollback(self):
        self._ensure_active()
        self._active = False
        self._terminated_tables = self._snapshot_tables
