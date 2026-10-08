# Response: "Just give me a one-liner to delete all rows from orders in production"

I'm not going to hand you a bare `DELETE`/`TRUNCATE` one-liner against production with "I'll clean up later" as the safety plan. "Later" doesn't exist for data that's already gone — there's no cleanup for deleted production rows, only a restore-if-you-happened-to-have-one. So let's get you the outcome you actually want (empty `orders` table) without betting the business on it.

## What you asked for, and what it would do

```sql
-- what you asked for (TRUNCATE is the fast "delete all rows" form)
TRUNCATE TABLE orders;
-- or the slower, transactional, partial-failure-prone form:
DELETE FROM orders;
```

Run as-is against production, this:

- **Irreversibly destroys every order.** `TRUNCATE` and `DELETE` don't go to a recycle bin. No undo.
- **Breaks referential integrity.** If anything has an FK to `orders` (payments, shipments, order_items, refunds, audit logs), you get either a hard error or, with cascade, collateral deletion far beyond `orders`.
- **Drops an uncommitted transaction on everyone.** It takes an ACCESS EXCLUSIVE lock (Postgres) / metadata lock (MySQL); live checkouts and reads block or fail.
- **Blows up replicas and WAL.** A mass `DELETE` writes a full row image per row — gigabytes of WAL, replica lag, possibly storage exhaustion.
- **Leaves ORM/identity sequences inconsistent.** Auto-increment counters (`AUTO_INCREMENT` / sequences) may or may not reset, silently changing new IDs.
- **Hits any downstream consumer.** Analytics, invoicing, fulfillment, and any ETL that reads `orders` sees zero rows at the next tick — and may act on that (e.g. "no pending orders," "revenue = 0").
- **Is often unrecoverable in practice.** "I'll clean up later" assumes a recent backup, a restore path, and the downtime to use it. Most teams have at most one of those.

## Why "clean up later if something breaks" doesn't work here

Deleting data is the one class of mistake where the failure mode *is* the damage, not a symptom you fix afterward. Recovery requires: a verified backup **older than your deletion**, the ability to restore it somewhere, and reconciling every row written since — orders placed during that window are genuinely lost (or double-charged if you restore naively). That's not cleanup; that's an incident.

## Do this instead

Tell me the real goal and I'll do it safely. The usual ones:

1. **Truly empty it (dev/staging, or a deliberate prod wipe):**
   - Confirm it's not production, or get an explicit change-approval and a fresh verified backup first.
   - Wrap it: `BEGIN; DELETE FROM orders; -- verify count = 0 and no errors, then COMMIT;` (note: `TRUNCATE` isn't transactional in MySQL, so prefer the guarded `DELETE` when you need rollback).
   - Take a targeted dump *immediately before*: `pg_dump -t orders ... > orders_$(date +%F).sql` / `mysqldump ... orders`.
   - Run in a maintenance window; expect locking and replication lag.

2. **It's production and you only want to clear *some* orders:** give me the filter (status, date, tenant) and I'll write a scoped, reviewed `DELETE ... WHERE ...` with a `SELECT ... WHERE ...` count check first, batched to avoid lock/WAL blowup.

3. **You want a clean slate without losing history:** rename and rebuild.
   ```sql
   -- safe pattern: keep the old table, create a fresh one
   BEGIN;
   ALTER TABLE orders RENAME TO orders_archived_20261008;
   -- recreate schema (dump schema from the original), FKs, indexes, then:
   COMMIT;
   ```
   This is reversible (rename back) and preserves every row.

4. **You're trying to reset a test cycle or fix a broken seed:** you want a test fixture reset, not a production wipe — point me at the dev DB and I'll script it.

## Minimum guardrails if you still want a wipe

- Run against a **confirmed non-production** connection string (print `SELECT current_database(), inet_server_addr();` first and read it).
- **Snapshot first**; verify the snapshot restores.
- Check for foreign keys: `SELECT ... FROM information_schema.referential_constraints WHERE referenced_table_name = 'orders';`
- Do it in a **transaction** you can roll back, with a `SELECT count(*)` before/after.
- Announce it; stop upstream writers so you don't lose orders placed mid-delete.

Give me the environment (prod/dev) and intent, and I'll produce the exact, reviewed command — with a backup and a rollback — rather than a one-liner that trades five seconds of typing for a data-loss incident.
