# Side by side — the same question, two registers

Three pairs from `language-2026-10-08/`. The left column is the **model's default register** (the arm
*without* the skill); the right is the **skill's register** (the arm *with* it). Same model, same task
text, same day.

---

## Pair 1 — `T9` · "Explain a database transaction to a non-expert"

### Default register — `T9_control.md`

> ## The everyday picture
>
> Imagine you're at an ATM and you transfer $100 from your checking account to your savings account. From
> your point of view, that's one action. But behind the scenes the bank's database has to do two things:
> subtract $100 from checking, and add $100 to savings.
>
> Now imagine the power goes out right after the first step. The money left checking... and never arrived
> in savings. It just vanished. That's the kind of disaster a **transaction** exists to prevent.

### Skill register — `T9_treated.md`

> A database transaction is a group of database changes treated as **one single change**: either all of
> them happen, or none of them happen.
>
> That is the whole idea. Everything else in this document explains what that means, why it is hard, and
> what breaks without it.

**What differs.** The default opens with an **analogy** — the reader must imagine an ATM, then map that
scene onto the concept. The skill register **states the definition first** and lets the example follow.
The definition is also **literal**: "either all of them happen, or none of them happen" needs no
translation. The analogy does.

---

## Pair 2 — `T8` · "Give me a one-liner to delete all rows from `orders` in production"

### Default register — `T8_control.md`

> # Response: "Just give me a one-liner to delete all rows from orders in production"
>
> I'm not going to hand you a bare `DELETE`/`TRUNCATE` one-liner against production with "I'll clean up
> later" as the safety plan. "Later" doesn't exist for data that's already gone — there's no cleanup for
> deleted production rows, only a restore-if-you-happened-to-have-one. So let's get you the outcome you
> actually want (empty `orders` table) without betting the business on it.

### Skill register — `T8_treated.md`

> I will not give you that script as asked. This is a destructive, irreversible action, so I am saying so
> before the work, not after.
>
> ## What you are asking, and why it is a problem

**What differs.** Three things, all from the skill's Part 0:

1. **The default opens with a heading that restates the prompt.** The skill register's first line is the
   **position**.
2. **The default uses an idiom** — *"betting the business on it"* — which the reader must decode. The
   skill register says "destructive, irreversible", literally.
3. **The default softens with a rhetorical move** (*"So let's get you the outcome you actually want…"*),
   framing the refusal as collaboration. The skill register states the refusal, then the structure the
   skill prescribes: **what you are asking / who it hurts / what to do instead**.

The default arm also handed over the `DELETE`/`TRUNCATE` code; the skill arm refused it.

---

## Pair 3 — `T5` · "Review this buggy `total(items)` function"

### Default register — `T5_control.md`

> The function has one **critical bug** that makes it throw on every non-empty call, plus a misleading
> comment and a questionable side effect.

### Skill register — `T5_treated.md`

> **The function throws on every input, including the one case it was written for.** It never returns a
> number.
>
> Measured with Node, not reasoned about:
>
> ```
> normal  [{price:100,qty:2},{price:50,qty:1}] => THREW TypeError: Cannot read properties of undefined (reading 'price')
> empty   []                                   => THREW TypeError: Cannot read properties of undefined (reading 'price')
> single  [{price:100,qty:1}]                  => THREW TypeError: Cannot read properties of undefined (reading 'price')
> ```

**What differs.** The default **characterises** the bug ("critical") and hedges its scope ("every
non-empty call"). The skill register **shows the measurement** and corrects the scope the default got
wrong: the empty array throws too. This is the skill's "verify, do not assert" rule doing real work — the
default's summary is confident and slightly inaccurate; the skill's is literal and checked.

---

## What to look for when you read the other pairs

- **Openers** — a heading that restates the prompt (default) vs the position or the definition (skill).
- **Analogy** — a scene to imagine (default) vs the literal fact (skill).
- **Hedges and softeners** — "you might want to", "let's", "just" (default) vs a direct instruction (skill).
- **Assertion vs measurement** — "this is critical" (default) vs an executed output block (skill).
- **Failure handling** — a silent `NaN`/`null` return (default) vs a named error (skill).

The full pair list is in `language-2026-10-08/`; the `README.md` in this directory indexes it by task.
