# The JavaScript Event Loop, Explained for Junior Developers

JavaScript is famously *single-threaded*: at any moment, it runs exactly one piece of code. Yet web pages stay responsive while they fetch data, run timers, and react to clicks. The trick isn't multiple threads — it's a scheduling system called the **event loop**. This document explains the four pieces that make it work: the call stack, the task (macrotask) queue, the microtask queue, and how promises use them.

## 1. The Call Stack

The **call stack** is where JavaScript actually executes code. It's a stack (last in, first out) of *frames*, and each frame represents a running function call.

When you call a function, a new frame is pushed on top. When the function returns, its frame is popped off. The function currently on top is the one executing.

```js
function multiply(a, b) {
  return a * b;
}

function square(n) {
  return multiply(n, n);
}

console.log(square(5)); // 25
```

The stack grows like this:

1. `square(5)` is pushed.
2. Inside it, `multiply(5, 5)` is pushed on top.
3. `multiply` returns `25`, so its frame pops.
4. `square` returns `25`, so its frame pops.
5. The stack is empty again.

The key limitation: **while the stack is busy, nothing else runs.** If a function takes three seconds to finish, the browser cannot handle clicks, render, or run timers for those three seconds. This is why "blocking the main thread" is a real problem — a long synchronous loop freezes the page.

Functions like `setTimeout` and `fetch` do **not** run on the call stack. They hand work off to the browser/platform, and when that work is ready, the result is queued so the stack can pick it up *later*. That "later" is what the queues and the event loop coordinate.

## 2. The Task (Macrotask) Queue

The **task queue** — often called the **macrotask queue** — holds callbacks waiting to run on the main stack. Each item is a whole "task". Classic examples:

- `setTimeout(fn, delay)` / `setInterval`
- A DOM event firing (for example a `click` handler)
- An I/O completion callback
- `setImmediate` (Node.js)
- Message events (for example `postMessage`)

The rule is simple: when the call stack is **empty**, the event loop takes the *oldest* task from this queue and runs it to completion. Then it checks again.

```js
console.log('A');

setTimeout(() => {
  console.log('B');
}, 0);

console.log('C');
```

Output:

```
A
C
B
```

Even with a delay of `0`, `B` runs last. `setTimeout(fn, 0)` does not mean "run now" — it means "queue this callback as a task; run it once the stack is clear." The current synchronous code (`A`, then `C`) finishes first.

## 3. The Microtask Queue

The **microtask queue** is a second, higher-priority queue. Microtasks come from:

- `.then()`, `.catch()`, `.finally()` callbacks on promises
- `queueMicrotask(fn)`
- `await` resumptions (more on this below)
- `MutationObserver` callbacks

The crucial difference is *when* microtasks run. After **each** task (and after the initial synchronous script finishes), the event loop runs the **entire microtask queue to completion** — including any new microtasks that those microtasks add — *before* it moves to the next macrotask.

This gives a strict priority order:

1. Run the current synchronous code (the stack).
2. Drain the microtask queue completely.
3. Take one macrotask and run it.
4. Drain the microtask queue completely again.
5. Repeat.

Microtasks always beat the next macrotask. Compare these two:

```js
setTimeout(() => console.log('macrotask'), 0);

Promise.resolve().then(() => console.log('microtask'));

console.log('sync');
```

Output:

```
sync
microtask
macrotask
```

`sync` prints first because it's on the call stack. Then the microtask queue drains (`microtask`), and only then does the loop pick up the timer's macrotask.

A warning that bites juniors: because the microtask queue is drained *fully* every time, a microtask that keeps queuing more microtasks will **starve** the macrotask queue — timers and rendering will never get a turn. Keep microtasks finite.

## 4. Promises and the Event Loop

A promise represents a value that will exist later. When a promise *settles* (resolves or rejects), it does **not** call your `.then()` handler immediately. Instead, it schedules that handler as a **microtask**.

```js
const p = Promise.resolve(42);

p.then(value => console.log('in then:', value));

console.log('after then');
```

Output:

```
after then
in then: 42
```

Even though the promise is already resolved, the `.then()` handler is not run inline — it is queued as a microtask, so the code after it runs first.

### `async` / `await` is promises in disguise

`async` functions always return a promise, and `await` is essentially syntactic sugar for `.then()`. Everything *after* an `await` is scheduled as a microtask.

```js
async function run() {
  console.log('1');
  await null;            // pauses here; the rest becomes a microtask
  console.log('3');
}

console.log('start');
run();
console.log('end');
```

Output:

```
start
1
end
3
```

`run()` begins synchronously and prints `1`. Hitting `await` pauses the function and schedules the remainder as a microtask. Control returns to the caller, which prints `end`. Once the stack is clear, the microtask runs and prints `3`.

### Putting it all together

```js
console.log('script start');

setTimeout(() => console.log('timeout'), 0);

Promise.resolve()
  .then(() => console.log('promise 1'))
  .then(() => console.log('promise 2'));

console.log('script end');
```

Output:

```
script start
script end
promise 1
promise 2
timeout
```

Step by step:

1. `script start` and `script end` run on the call stack (synchronous).
2. The timer's callback sits in the macrotask queue.
3. The first `.then()` sits in the microtask queue.
4. Stack empties → drain microtasks: `promise 1` runs, which queues `promise 2` as another microtask, which also runs.
5. Microtask queue is empty → take the macrotask: `timeout`.

## The Mental Model

- **Call stack** — one thing runs at a time; everything else waits.
- **Microtask queue** — high priority. Emptied *completely* after every task.
- **Macrotask queue** — normal priority. One task taken each turn.
- **Event loop** — the referee: run the stack → drain microtasks → one macrotask → drain microtasks → repeat.

Memorize the ordering rule and most "why did this print in that order?" puzzles become easy:

> **Synchronous code first, then all microtasks, then one macrotask — over and over.**
