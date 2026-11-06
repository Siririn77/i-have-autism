import copy
import hashlib
import json
import os


class ConflictError(Exception):
    """Raised when a transaction conflicts with a committed transaction."""


class Database:
    def __init__(self, path=None):
        self.path = os.fspath(path) if path is not None else None
        self.tables = {}
        self.versions = {}
        self.commit_seq = 0
        self.next_id = 1
        self._closed = False

        if self.path is not None:
            parent = os.path.dirname(os.path.abspath(self.path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._load()
            if not os.path.exists(self.path):
                with open(self.path, "ab"):
                    pass

    def _load(self):
        self.tables.clear()
        self.versions.clear()
        self.commit_seq = 0
        self.next_id = 1

        if self.path is None or not os.path.exists(self.path):
            return

        valid_end = 0

        with open(self.path, "rb") as f:
            while True:
                raw_line = f.readline()
                if not raw_line:
                    break

                try:
                    text = raw_line.decode("utf-8")
                except UnicodeDecodeError:
                    break

                stripped = text.strip()
                if not stripped:
                    break

                try:
                    record = json.loads(stripped)
                except (json.JSONDecodeError, TypeError):
                    break

                if not isinstance(record, dict):
                    break
                if "crc" not in record or "ops" not in record or "seq" not in record:
                    break

                crc = record.get("crc")
                payload = {k: v for k, v in record.items() if k != "crc"}

                try:
                    payload_str = json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                except (TypeError, ValueError):
                    break

                expected_crc = hashlib.sha256(
                    payload_str.encode("utf-8")
                ).hexdigest()

                if not isinstance(crc, str) or crc != expected_crc:
                    break

                seq = record.get("seq")
                ops = record.get("ops")

                if not isinstance(seq, int) or not isinstance(ops, list):
                    break

                valid = True
                for op in ops:
                    if not isinstance(op, dict):
                        valid = False
                        break
                    if op.get("op") not in ("insert", "update", "delete"):
                        valid = False
                        break
                    if "table" not in op or "id" not in op:
                        valid = False
                        break
                    if op.get("op") in ("insert", "update") and "row" not in op:
                        valid = False
                        break

                if not valid:
                    break

                for op in ops:
                    table = op["table"]
                    row_id = op["id"]
                    mode = op["op"]

                    if mode in ("insert", "update"):
                        self.tables.setdefault(table, {})[row_id] = copy.deepcopy(
                            op["row"]
                        )
                    else:
                        self.tables.get(table, {}).pop(row_id, None)

                    self.versions[(table, row_id)] = seq

                    if isinstance(row_id, int):
                        self.next_id = max(self.next_id, row_id + 1)

                self.commit_seq = max(self.commit_seq, seq)

                next_id = record.get("next_id")
                if isinstance(next_id, int):
                    self.next_id = max(self.next_id, next_id)

                valid_end = f.tell()

        # Remove a damaged tail so future commits remain readable.
        try:
            size = os.path.getsize(self.path)
        except OSError:
            size = 0

        if size > valid_end:
            with open(self.path, "r+b") as f:
                f.truncate(valid_end)

        # Make sure the next append starts on a fresh line.
        if valid_end > 0:
            with open(self.path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                last = f.read(1)
            if last != b"\n":
                with open(self.path, "ab") as f:
                    f.write(b"\n")

    def _append_record(self, record):
        if self.path is None:
            return

        line = (
            json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        data = line.encode("utf-8")

        size_before = os.path.getsize(self.path) if os.path.exists(self.path) else 0

        try:
            if size_before > 0:
                with open(self.path, "rb") as f:
                    f.seek(-1, os.SEEK_END)
                    last = f.read(1)
                if last != b"\n":
                    data = b"\n" + data

            with open(self.path, "ab") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            try:
                if os.path.exists(self.path):
                    with open(self.path, "r+b") as f:
                        f.truncate(size_before)
            except Exception:
                pass
            raise

    def _allocate_id(self):
        row_id = self.next_id
        self.next_id += 1
        return row_id

    def begin(self):
        return Transaction(self)

    def close(self):
        if self._closed:
            return
        self._closed = True


class Transaction:
    def __init__(self, db):
        self.db = db
        self.snapshot_seq = db.commit_seq
        self.snapshot = copy.deepcopy(db.tables)
        self.view = copy.deepcopy(self.snapshot)
        self.ops = []
        self.touched = set()
        self.dead = False

    def _check_alive(self):
        if self.dead:
            raise RuntimeError("transaction is already closed")

    def insert(self, table, row):
        self._check_alive()

        row_id = self.db._allocate_id()
        new_row = copy.deepcopy(row)
        new_row["_id"] = row_id

        self.view.setdefault(table, {})[row_id] = new_row

        self.ops.append(
            {
                "op": "insert",
                "table": table,
                "id": row_id,
                "row": copy.deepcopy(new_row),
            }
        )

        return row_id

    def select(self, table, where=None):
        if where is None:
            where = {}

        rows = self.view.get(table, {})
        result = []

        for row in rows.values():
            if all(k in row and row[k] == v for k, v in where.items()):
                result.append(copy.deepcopy(row))

        result.sort(key=lambda r: r["_id"])
        return result

    def update(self, table, where, changes):
        self._check_alive()

        if "_id" in changes:
            raise ValueError("cannot change _id")

        if where is None:
            where = {}

        if not changes:
            return 0

        rows = self.view.get(table)
        if not rows:
            return 0

        matched = []
        for row_id, row in rows.items():
            if all(k in row and row[k] == v for k, v in where.items()):
                matched.append(row_id)

        for row_id in matched:
            old_row = rows[row_id]
            new_row = copy.deepcopy(old_row)

            for key, value in changes.items():
                if key == "_id":
                    continue
                new_row[key] = copy.deepcopy(value)

            rows[row_id] = new_row

            self.ops.append(
                {
                    "op": "update",
                    "table": table,
                    "id": row_id,
                    "row": copy.deepcopy(new_row),
                }
            )
            self.touched.add((table, row_id))

        return len(matched)

    def delete(self, table, where):
        self._check_alive()

        if where is None:
            where = {}

        rows = self.view.get(table)
        if not rows:
            return 0

        matched = []
        for row_id, row in rows.items():
            if all(k in row and row[k] == v for k, v in where.items()):
                matched.append(row_id)

        for row_id in matched:
            del rows[row_id]
            self.ops.append(
                {
                    "op": "delete",
                    "table": table,
                    "id": row_id,
                }
            )
            self.touched.add((table, row_id))

        return len(matched)

    def commit(self):
        self._check_alive()

        if not self.ops:
            self.dead = True
            return

        for table, row_id in self.touched:
            if self.db.versions.get((table, row_id), 0) > self.snapshot_seq:
                raise ConflictError(
                    f"conflict on table {table!r}, _id {row_id!r}"
                )

        new_seq = self.db.commit_seq + 1

        record = {
            "seq": new_seq,
            "next_id": self.db.next_id,
            "ops": self.ops,
        }

        payload = {k: v for k, v in record.items() if k != "crc"}
        payload_str = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        record["crc"] = hashlib.sha256(
            payload_str.encode("utf-8")
        ).hexdigest()

        # Durability: journal first, memory second.
        self.db._append_record(record)

        for op in self.ops:
            table = op["table"]
            row_id = op["id"]
            mode = op["op"]

            if mode in ("insert", "update"):
                self.db.tables.setdefault(table, {})[row_id] = copy.deepcopy(
                    op["row"]
                )
            else:
                self.db.tables.get(table, {}).pop(row_id, None)

            self.db.versions[(table, row_id)] = new_seq

        self.db.commit_seq = new_seq
        self.dead = True

    def rollback(self):
        self._check_alive()
        self.dead = True
        self.view = self.snapshot
