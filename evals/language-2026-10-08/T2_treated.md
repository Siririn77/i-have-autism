# Atomic write (temp file + rename) vs. write with fsync

Two different problems, often confused because the correct file-replacement idiom uses both. Read the
two definitions first; they do not compete.

- **Atomic write (temp + rename):** guarantees *what a reader sees*. The target file is never a
  half-written mixture. A concurrent reader sees either the complete old file or the complete new file.
  This is about **visibility and consistency**, not durability.
- **fsync:** guarantees *what survives a crash*. It forces the data from the kernel's page cache onto the
  physical storage device. After a power loss, the synced bytes are still there. This is about
  **durability**, not visibility.

A rename without fsync is atomic but not durable. An fsync without rename is durable but not atomic. The
idiom that gives both is: write temp, fsync temp, rename, fsync directory.

---

## 1. Atomic write via temp file + rename

### Mechanism

1. Create a new file with a temporary name in the **same directory** as the target.
2. Write the full new contents into the temp file.
3. Close it.
4. Call `rename(temp, target)`.

The same-directory requirement is not stylistic. `rename()` is only atomic when source and destination
are on the same filesystem. A temp file on a different mount makes the operation a copy, which is not
atomic.

### What it guarantees

POSIX defines `rename()` as atomic with respect to other processes. At every instant, the name `target`
refers to exactly one inode: the old file or the new file. There is no moment at which `target` is missing,
partially written, or refers to both. A reader that opens `target` gets one complete version.

This is the reason the pattern exists. If a process dies mid-write, the damage is confined to the temp
file, which is discarded. The original `target` was never touched until the single atomic rename.

### What it does NOT guarantee

- **Not durability.** `rename()` updates in-memory directory metadata. It can return success while both the
  new file's data and the rename itself are still in the page cache, lost if power fails. On ext4 with
  delayed allocation, a rename-only "atomic write" with no fsync can leave a **zero-length file** at
  `target` after a crash: the metadata committed, the data never did. This was demonstrated by Pillai et
  al., *All File Systems Are Not Created Equal* (OSDI 2014).
- **Not crash safety for the directory entry.** Making the rename durable requires fsync-ing the directory,
  not the file. See section 3.
- **Not a protection for the old inode's data** if something else also holds it open. It guarantees name
  atomicity, not isolation of unrelated writers.

### When it matters

- A reader may read the file at any time, including during a write: config files read by a running daemon,
  files served over HTTP, files tailed by a log shipper.
- A partial write must never be observable: JSON/TOML/YAML config, a database index file, a serialized
  cache that is parsed on startup.
- Multiple writers race for the same path: the rename serializes the final step, so the last rename wins
  cleanly instead of interleaving bytes.
- The failure mode is "process crashed mid-write", not "the whole machine lost power".

---

## 2. A write with fsync

### Mechanism

1. Write the bytes (to an existing file, or to the temp file).
2. Call `fsync(fd)` on the file descriptor.

`fsync()` blocks until the device reports that the file's data and the metadata needed to retrieve it are
persisted. `fdatasync()` is the cheaper variant: it flushes data plus the metadata required to read the
data back (size, block pointers), but not unrelated metadata such as mtime.

### What it guarantees

After `fsync(fd)` returns, the file's contents have reached stable storage. A power loss or kernel panic
immediately afterward does not lose them. This is the only operation among the two that speaks about
surviving a crash.

### What it does NOT guarantee

- **Not atomicity.** fsync on a file that is being overwritten in place does not make the overwrite
  all-or-nothing. A crash during the write leaves the file partially updated. fsync only promises that
  whatever was written is now durable; it says nothing about the write being a single indivisible step.
- **Not ordering between the file and its directory entry.** fsync of the file does not flush the directory
  entry that names it. That is a separate fsync on the directory.
- **Not durability of the rename.** After `rename(temp, target)`, an fsync of `temp`'s or `target`'s file
  descriptor does not persist the directory entry change. You must fsync the **directory**.

### When it matters

- The data must survive a crash: a write-ahead log, a database commit, a received payment, an audit record,
  a checkpoint you will reload after reboot.
- Ordering matters between two writes: fsync the file, then fsync the directory, so the data is on disk
  **before** the name that exposes it. A crash between the two leaves an orphaned-but-intact temp file,
  never a named-but-empty target.
- Compliance or correctness requirements make silent data loss unacceptable.

### The cost

fsync forces a device flush and is orders of magnitude slower than a buffered write (a disk seek plus
rotation, or a flash cache flush). Calling it on every small write collapses throughput. Batch, or use it
only at commit points.

---

## 3. Why the correct idiom needs both, in order

The full crash-safe replacement of a file is four steps, each addressing a distinct failure:

1. Write the new contents to `temp` in the same directory.
2. `fsync(temp_fd)` — makes the **contents** durable before anything points at them.
3. `rename(temp, target)` — swaps the name atomically.
4. `fsync(dir_fd)` — makes the **rename** durable.

Crash at each point:

| Crash after step | On-disk state after reboot | Correct? |
| --- | --- | --- |
| 2 (before rename) | `target` = old file; `temp` orphaned, full contents | yes, plus a litter file |
| 3 (before dir fsync) | `target` = old **or** new, non-deterministic; may be a zero-length `target` on ext4 | no |
| 4 | `target` = new file | yes |

Step 2 without step 4 is the classic half-correct idiom. It is atomic (readers never see a torn file) but
not crash-safe (the rename may not survive, or the new data may not). Most code in the wild stops at step 2
and believes it is safe; the ext4 zero-length case is the reason it is not.

### Reference implementation (Python)

```python
import os
import tempfile

def atomic_write(path: str, data: bytes) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    # Temp file lives in the target's directory: rename is only atomic within one filesystem.
    fd, temp_path = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "wb") as temp_file:
            temp_file.write(data)
            temp_file.flush()
            os.fsync(temp_file.fileno())      # contents durable before the name changes
        os.rename(temp_path, path)            # atomic swap of the name
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)                  # rename durable
        finally:
            os.close(dir_fd)
    except BaseException:
        # A crash inside the try leaves temp_path behind; discard it, never touch path.
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise
```

Node equivalent uses `fs.writeSync`, `fs.fsyncSync(fd)`, `fs.renameSync`, then opens the directory with
`fs.openSync(dir, 'r')` and `fs.fsyncSync(dirFd)`. On Windows, directory fsync is not supported and the
rename itself is the durable commit; the pattern differs.

---

## 4. Decision guide

- **Only a concurrent reader must never see a partial file** → temp + rename is enough. Skip the fsyncs if a
  crash-lost update is acceptable (for example, a regenerable cache).
- **Only the data must survive a crash, and the file is written once and never overwritten in place** →
  write + fsync. No rename needed.
- **Both: the file is replaced repeatedly and the newest version must survive a crash intact** → all four
  steps, in order. This is the only correct option. Examples: a config the system reloads after reboot, a
  database manifest, a checkpoint.
- **The write is idempotent and can be redone** → durability is optional; atomicity alone often suffices.

### Common mistakes

- Renaming across filesystems (`/tmp` temp file onto a target on `/var`): the operation becomes a
  non-atomic copy. Put the temp file in the target's directory.
- fsync-ing the file but not the directory: the rename can be lost. This is the most common bug.
- Assuming fsync makes an in-place rewrite atomic: it does not. Use rename.
- fsync-ing on every write in a hot loop: correct but cripplingly slow. Batch.
- Trusting `flush()` (Python) or a bare `write()` to reach disk: `flush()` only empties the process buffer
  into the kernel; the kernel page cache still needs `fsync`.

### One-line summary

Temp + rename buys **atomicity** (readers see one complete version); fsync buys **durability** (the bytes
survive a crash). To replace a file safely across a power loss you need both, and the directory fsync — not
the file fsync — is what makes the rename itself durable.
