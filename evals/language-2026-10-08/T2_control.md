# Atomic writes (temp-file + rename) vs. fsync

These two techniques solve **different** problems and are orthogonal — a correct durable
write usually needs *both*.

## 1. Atomicity: temp-file + rename

```
write to  /dir/.tmp-XXXX     (a new file in the SAME directory)
fsync(tmp)                   (optional here — see below)
rename(/dir/.tmp-XXXX, /dir/name)
```

`rename(2)` on a POSIX filesystem is atomic with respect to other processes: a concurrent
reader either sees the old file or the new file, never a mixture. Consequences:

- Readers never observe a *torn* or partially written file.
- A crash mid-write leaves either the old inode untouched or the new one fully linked;
  the temporary file is simply orphaned (garbage to clean up later).
- The temp file must live in the **same directory / same filesystem** as the target,
  otherwise `rename` degrades to copy+delete (not atomic) — a cross-device rename fails
  with `EXDEV` rather than silently falling back in most implementations.

**What it is NOT:** atomic rename does not guarantee the new contents are on stable
storage. It only guarantees *name-level* atomicity and ordering as seen by other
processes on that machine.

## 2. Durability: fsync

`fsync(fd)` (or `fdatasync`) flushes the file's data (and metadata for `fsync`) from the
kernel/page cache to the physical device, and blocks until the device reports it is
written. Without it, data can live in RAM-backed caches (page cache, the drive's own
volatile write cache) for seconds to minutes after `write()` returns.

- A power loss after `write()` but before `fsync()` can lose the write even though the
  process returned success.
- To make a `rename` durable you must also `fsync` the *directory* containing it: the
  rename itself is a directory-metadata change, and directories have their own ordering
  requirements. The classic robust sequence is:

```
fd = open(tmp, O_WRONLY|O_CREAT|O_EXCL)
write(fd, buf); fsync(fd); close(fd)
rename(tmp, target)
dirfd = open(dir, O_DIRECTORY)
fsync(dirfd); close(dirfd)
```

`O_EXCL` on the temp file also prevents two writers clobbering the same temp path.
(On Linux, `renameat2`/`RENAME_NOREPLACE` can add "don't overwrite an existing target".)

## 3. When each matters

| Scenario | temp+rename | fsync | Why |
|---|---|---|---|
| Config file rewritten by a daemon that reloads on change | ✅ needed | usually optional | Readers/tailers must never see half a file; losing the *latest* version on power loss is often acceptable |
| Crash-safe on-disk journal / database record | ✅ needed | ✅ needed | Both torn content and lost-but-acknowledged writes are unacceptable |
| Generated artifacts (cache, build output) | ✅ often | rarely | Reproducible; re-run on corruption; speed matters |
| Append-only log with a checksum | ❌ (no rename; append) | ✅ needed | Atomicity comes from record framing/CRC, not rename; durability from fsync |
| Trivial file written once, no concurrent reader | ❌ unnecessary | depends | No reader to protect; durability only if data must survive power loss |
| "I just want to reduce risk of a corrupt file on `Ctrl-C`" | ✅ enough | no | Process death does not flush caches, so data stays in page cache and lands anyway; atomicity is the whole win |

### Rules of thumb

- **Need atomicity** (safe concurrent readers, never-corrupt on crash): temp + rename.
- **Need durability** (survives power loss / kernel panic / `echo b > sysrq-trigger`):
  `fsync` the file, and `fsync` the parent directory after the rename.
- **Need both** (most robust file writes, e.g. save-then-commit): do all of it, in the
  order above.
- **Cost:** `fsync` is expensive (milliseconds, can be tens of ms on spinning disks and
  on some SSDs with a volatile cache). Do not `fsync` in a hot loop unless durability
  truly demands it; batching or `fdatasync` helps.

## 4. Common misconceptions

- *"`rename` makes it durable."* No — it makes it atomic. The bytes may still be in cache.
- *"`fsync` makes it atomic."* No — after `fsync` the file is durable, but a concurrent
  reader could still have seen the file mid-write during the `write()` calls.
- *"`write()` returning means the data is on disk."* No — only means the kernel accepted
  it into the page cache.
- *"`close()` implies `fsync()`."* No, not on POSIX. (Some filesystems / Windows
  semantics differ, but do not rely on it.)

In short: **temp+rename answers "will anyone ever see a broken file?"; fsync answers
"will the data survive a power cut?"** Real crash-safety needs both, plus a directory
fsync for the rename.
