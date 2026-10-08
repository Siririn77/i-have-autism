# Database transactions, explained plainly

A database transaction is a group of database changes treated as **one single change**: either all of them
happen, or none of them happen.

That is the whole idea. Everything else in this document explains what that means, why it is hard, and what
breaks without it.

## The problem it solves

Imagine a database table of bank accounts with two rows:

| account | balance |
|---------|---------|
| Alice   | 100     |
| Bob     | 50      |

You want to move 30 from Alice to Bob. That is two separate writes:

1. Subtract 30 from Alice. Alice now has 70.
2. Add 30 to Bob. Bob now has 80.

These two writes are separate steps. Between step 1 and step 2, anything can happen:

- The program crashes.
- The computer loses power.
- The network connection drops.
- Another program reads the data right now.

If step 1 finishes and step 2 never runs, the database now says Alice has 70 and Bob has 50. **30 units of
money have disappeared.** Alice was charged and Bob was never paid.

A transaction prevents this. You tell the database: "these two writes are one unit." The database guarantees:

- If the program crashes after step 1 but before step 2, the database **undoes step 1** on its own. When the
  program comes back, Alice still has 100 and Bob still has 50, as if nothing happened.
- The two writes never become visible half-finished to anyone else.

## The four guarantees, in plain words

Database engineers describe a transaction with four properties, often shortened to **ACID**. Here is what each
one means without the jargon.

**1. All-or-nothing (the technical word is "atomic").**
"Atomic" means "cannot be divided." A transaction is one indivisible change. You cannot buy half of it. If one
write inside the group fails, every write in the group is thrown away and the database returns to exactly how
it was before the group started.

**2. Consistent (no rules are broken).**
The database has rules — for example, "a balance is never negative," or "every order must belong to a real
customer." A transaction moves the database from one state where all rules are true, to another state where
all rules are true. It never stops in a state where a rule is broken.

**3. Isolated (other people do not see the middle).**
While your transaction is running, other programs do not see the half-finished work. They either see the state
before your transaction, or the state after it finished. This matters because two programs can be changing the
same data at the same time (see "the last seat on a plane" below).

**4. Durable (once it is saved, it stays saved).**
When you tell the database "save this now" — the technical word is **commit** — the change is written to disk
in a way that survives a crash or a power cut. The database does not forget a committed change.

Two words worth knowing, because you will see them in every discussion of this topic:

- **Commit** — the moment you declare the group finished and want it saved for good.
- **Rollback** — the moment you cancel the group and ask the database to undo everything in it.

## Why it matters — three concrete cases

**Case 1: money moving between accounts.**
Explained above. Without a transaction you can lose money or create money out of a crash. With one, the move
either fully happens or does not happen.

**Case 2: placing an order.**
A single order usually touches several tables: it creates an order row, it decreases the item's stock count, it
charges the customer's card. If the order is created but the charge fails, you have promised the customer
something you were not paid for. If the charge succeeds but the order is never saved, you have taken money and
delivered nothing. A transaction makes all three changes together, or none.

**Case 3: the last seat on a plane (two people at once).**
One seat is left. Two people click "buy" at the same instant. Each program reads "1 seat available," each
decides "I can buy it," each writes "0 seats available." Both customers are now told they bought the last
seat — but only one seat exists. This is not a crash; both programs ran correctly on their own. It happens
because they overlapped. Transactions with isolation prevent this: the second transaction is made to wait, or
is made to fail and retry, and it sees "0 seats available" before it acts. Exactly one customer gets the seat.

This third case is the one most people underestimate. The first two cases are about crashes. The third is about
**two correct programs running at the same time**, and it happens on healthy systems with no crash at all.

## What can go wrong without transactions

- **Partial writes.** Half of a multi-step change is saved and the other half is lost. The data now describes a
  situation that never actually existed.
- **Lost update.** Two programs overwrite each other's change; one person's work silently disappears.
- **Double charge / double spend.** The same money or the same resource is used twice because two programs did
  not see each other.
- **Broken rules.** A row violates a rule (a negative balance, an order with no customer) because the checks
  and the writes were not grouped.

## What a transaction does **not** do

It is not magic, and knowing its limits prevents surprises.

- **It does not make your program correct by itself.** You still have to put the right writes in the group. A
  transaction around the wrong two writes still gives the wrong result — reliably wrong.
- **It does not cover things outside the database.** If your code also sends an email, moves a file on disk,
  or calls an outside payment service, the transaction cannot un-send the email. Those steps are outside its
  reach. This is the hard part of real systems, and it is a separate topic (often called "distributed
  transactions" or "the saga pattern").
- **Long transactions cause problems.** The longer a transaction stays open, the longer it holds data that
  other programs may want to change. This can make them wait, and in bad cases two transactions can each be
  waiting for the other — the technical word is **deadlock**. The database usually detects this and fails one
  of them so one can proceed. The practical rule: keep transactions short, and do not do slow work (like
  sending an email) inside one.
- **It has a cost.** Grouping changes and keeping them isolated uses extra memory and coordination. You do not
  put everything in one giant transaction; you group exactly the changes that must succeed or fail together.

## The one-sentence version

A transaction is a way to tell the database "treat these changes as one change — all of them, or none of them"
— and it matters because without that promise, crashes, overlaps, and failures leave your data describing a
world that never existed, which means lost money, wrong inventory, and customers holding promises you cannot
keep.

## One thing to try next

Open any real project's code and search for the word `transaction` (or `BEGIN` and `COMMIT` in SQL). Find one
place where several writes are grouped, and read the code around it to see which writes were chosen to succeed
or fail together. That single example will make the idea concrete faster than any explanation.
