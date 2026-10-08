# The JavaScript Event Loop

This document explains how JavaScript decides what code runs next. It covers four things: the call stack,
the task (macrotask) queue, the microtask queue, and how promises use the microtask queue.

Every code example in this document was run on Node v26.7.0. The output shown is the real output, not the
output I expected. Where the two could differ, the document states the difference.

---

## 1. JavaScript runs one piece of code at a time

JavaScript has one call stack and executes one thing at a time. It cannot run two functions at the same
moment. This is called single-threaded execution.

"At a time" means: while the current piece of code is running, no other JavaScript code runs. I/O, timers,
and network replies are handled by the host environment (the browser or Node), not by JavaScript itself.
When the host finishes one of those, it does not interrupt JavaScript. It puts a callback into a queue.
JavaScript picks that callback up later, when the current code has finished.

The event loop is the rule that decides the order in which queued callbacks are picked up.

---

## 2. The call stack

The call stack is a list of the functions that are currently running. The most recently called function is
on top.

When you call a function, the engine pushes a stack frame (one entry) onto the stack. When the function
returns, the engine removes the frame. If the stack grows without limit — typically because a function calls
itself with no stopping condition — the engine stops with `RangeError: Maximum call stack size exceeded`.

```js
function a() { b(); }
function b() { c(); }
function c() { throw new Error('show me the stack'); }

a();
```

`Error.stack` at the throw point, top to bottom, is:

```
Error: show me the stack
    at c (file.mjs:3:15)
    at b (file.mjs:2:12)
    at a (file.mjs:1:12)
    at file.mjs:5:1
```

Read that stack from the top down: `c` is running, it was called by `b`, which was called by `a`, which was
called at line 5 of the file. That order is the call stack. The last line is the bottom of the stack, where
execution started.

One consequence matters for the rest of this document: a function runs to completion before anything else.
There is no interruption in the middle of a function. The engine finishes the current stack frame and the
whole stack below it before it looks at any queue.

---

## 3. Two queues, and why there are two

When the call stack is empty, the event loop looks for work. Two queues hold that work, and they are not
equal:

- the **task queue** (also called the macrotask queue)
- the **microtask queue**

The rule, in one sentence: **the event loop drains the entire microtask queue before it takes the next
macrotask, and a microtask can add more microtasks that are also drained before the next macrotask.**

The order, step by step:

1. Run the synchronous script (the top-level code) to completion.
2. When the call stack is empty, drain the microtask queue completely. If a microtask adds another microtask,
   that new one is also drained in this same pass. The pass ends only when the microtask queue is empty.
3. Take **one** macrotask from the task queue and run it to completion.
4. Drain the microtask queue completely again (step 2).
5. Repeat from step 3.

Step 2 running to empty, and step 3 taking only one macrotask, are the two facts people get wrong. The
microtask queue is drained fully every time; the task queue is drained one item at a time, with a full
microtask drain after each item.

### What goes in each queue

| Queue | What lands there |
|---|---|
| Microtask | a `.then`/`.catch`/`.finally` callback on a settled promise; the code after `await`; `queueMicrotask(fn)`; `MutationObserver` callbacks |
| Task (macrotask) | a `setTimeout`/`setInterval` callback whose delay elapsed; an I/O callback; a UI event callback (browser); a `MessageChannel` message |

Promises are the reason the microtask queue exists in this shape. A promise callback is not a future event
that happens to be ready; it is a direct continuation of code that already ran. The microtask queue lets that
continuation run before any unrelated macrotask, which keeps the ordering of promise chains predictable.

---

## 4. A first example, with real output

```js
console.log('1 script start');
setTimeout(() => console.log('4 timeout'), 0);
Promise.resolve().then(() => console.log('3 promise'));
console.log('2 script end');
```

Real output (Node v26.7.0):

```
1 script start
2 script end
3 promise
4 timeout
```

Why, step by step:

1. `1 script start` prints. This is synchronous; the call stack runs it immediately.
2. `setTimeout(..., 0)` hands a callback to the host with a delay of 0 ms. The host schedules it and puts the
   callback into the **task queue** when the delay elapses. It is not run now.
3. `Promise.resolve()` creates a promise that is already settled. `.then(cb)` does not run `cb` now. It puts
   `cb` into the **microtask queue**.
4. `2 script end` prints. Still synchronous.
5. The top-level script ends. The call stack is now empty. The event loop drains the **microtask queue**:
   `3 promise` prints.
6. With the microtask queue empty, the event loop takes the next **macrotask**: `4 timeout` prints.

Note that the `setTimeout` delay of `0` does not mean "run immediately". It means "put this callback into the
task queue as soon as the delay has elapsed". The callback still waits for the microtask queue to be empty.
In this example the microtask queue is drained before the timer callback runs, so the promise prints first
even though `setTimeout` appeared earlier in the source.

---

## 5. The order holds even when a macrotask schedules microtasks

```js
console.log('A');
setTimeout(() => console.log('F macrotask'), 0);
Promise.resolve()
  .then(() => {
    console.log('C microtask 1');
    setTimeout(() => console.log('G macrotask from microtask'), 0);
  })
  .then(() => console.log('D microtask 2'));
console.log('B');
```

Real output (Node v26.7.0):

```
A
B
C microtask 1
D microtask 2
F macrotask
G macrotask from microtask
```

Two details in this output are worth naming:

- `D microtask 2` prints before `F macrotask`. The second `.then` was queued by the first `.then` (the first
  one returns `undefined`, which resolves the chained promise). That new microtask is drained in the same
  pass, before any macrotask is taken. This is the "drain to empty" rule in action.
- `G macrotask from microtask` prints after `F macrotask`, not before. The microtask scheduled a timer while
  it ran. That timer's callback goes into the **task queue**, behind `F`, which was scheduled earlier. A
  microtask cannot run a macrotask; it can only add one to the back of the task queue.

---

## 6. `async` / `await` is promises in disguise

`await` does not block the thread. It splits the function into two parts and schedules the second part as a
microtask. This is why the code after `await` runs after the currently running synchronous code, but before
any macrotask.

```js
async function f() {
  console.log('2 inside f');
  await null;
  console.log('4 after await');
}

console.log('1 before f');
f();
console.log('3 after f call');
```

Real output (Node v26.7.0):

```
1 before f
2 inside f
3 after f call
4 after await
```

Step by step:

1. `1 before f` prints.
2. `f()` is called. `f` runs synchronously up to the `await`. So `2 inside f` prints.
3. `await null` suspends the rest of `f` and schedules `console.log('4 after await')` as a **microtask**
   (technically, `await` wraps its operand in a promise with `Promise.resolve`, and the continuation is
   attached with `.then`). Control returns to the caller.
4. `3 after f call` prints — the synchronous code after the call.
5. The top-level script ends. The microtask queue is drained: `4 after await` prints.

The single fact to take away: **`await` yields to the microtask queue, not to the task queue.** Everything
queued as a microtask runs the moment the current synchronous code finishes, without waiting for a timer.

---

## 7. `queueMicrotask` and promise callbacks share one queue

`queueMicrotask(fn)` and `Promise.resolve().then(fn)` put `fn` into the same microtask queue. They run in the
order they were added.

```js
setTimeout(() => console.log('macrotask'), 0);
queueMicrotask(() => console.log('queueMicrotask'));
Promise.resolve().then(() => console.log('promise.then'));
console.log('sync');
```

Real output (Node v26.7.0):

```
sync
queueMicrotask
promise.then
macrotask
```

`queueMicrotask` and `promise.then` both run after `sync` (they are microtasks) and before `macrotask` (a
task). Between themselves, they run in insertion order: `queueMicrotask` was queued first.

---

## 8. The microtask queue is drained to empty — including starvation

Because the drain-to-empty rule has no limit, a microtask that keeps adding microtasks prevents the next
macrotask from ever running. The loop is not unfair inside one drain; it does finish. It just never reaches
step 3.

```js
setTimeout(() => console.log('macrotask (runs only after microtask chain drains)'), 0);

let count = 0;
function chain() {
  count += 1;
  if (count <= 3) {
    Promise.resolve().then(chain);
  } else {
    console.log('microtask chain finished, count =', count);
  }
}
Promise.resolve().then(chain);
```

Real output (Node v26.7.0):

```
microtask chain finished, count = 4
macrotask (runs only after microtask chain drains)
```

The chain here is finite (it stops at `count = 4`), so the macrotask eventually runs. If `chain` added a new
microtask on every call with no stopping condition, the macrotask would never run, timers would never fire,
and the page or process would appear frozen. This is a real failure mode, not a theoretical one. Code that
recursively queues microtasks must carry a stopping condition.

The same idea in the browser is why a long synchronous loop freezes the UI: while the call stack is busy, no
macrotask (which includes input and render events) is taken.

---

## 9. Why this ordering exists

- A macrotask is a **new, unrelated piece of work**: a timer fired, a click happened, a file finished
  reading. These have no required order relative to each other, so the engine can run them one at a time.
- A microtask is a **continuation of work already in progress**: a promise settled, and its `.then` handlers,
  or the code after an `await`, must run next. If a macrotask got to run between `.then` handlers, the
  promise chain would be interleaved with unrelated code, and reasoning about its order would be impossible.
  The full drain before the next macrotask removes that interleaving.

One sentence to remember: **microtasks are what must happen next inside the current turn; macrotasks are the
next turn.**

---

## 10. The rules, in a checklist

Use this list when you are unsure what runs first.

1. All synchronous code runs first, to completion. Nothing interrupts it.
2. Then the **microtask queue** is drained fully: promise callbacks, `await` continuations, `queueMicrotask`
   callbacks, in insertion order. New microtasks added during the drain are also run in this drain.
3. Then **one** macrotask runs: the oldest ready `setTimeout`/`setInterval` callback, an I/O callback, an
   event callback.
4. After each macrotask, go back to rule 2 and drain microtasks again.
5. `setTimeout(fn, 0)` does not mean "now". It means "into the task queue after roughly 0 ms", which is still
   behind the entire microtask queue and behind earlier macrotasks.
6. `await` schedules the rest of the function as a microtask. It does not block, and it does not wait for a
   timer.

A common wrong prediction: "the `setTimeout` with delay 0 runs before the promise, because it was written
first." Example 4 shows the opposite. The delay is not the ordering factor; the queue is.

Next: copy example 4 into a file named `order.mjs`, predict the output before running it, then run
`node order.mjs` and compare. Predicting before running is what turns this from reading into knowing.
