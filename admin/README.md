# admin — the console

The screen you sit in front of on the Tuesday an app vendor ships a redesign.

```bash
python3 schema/migrate.py node.sqlite
python3 admin/seed-demo.py node.sqlite     # demo data, optional
python3 admin/server.py   node.sqlite --port 8090
```

Then open <http://127.0.0.1:8090>.

## What it is

Its own module, its own port, its own process. It takes a database path and
nothing else — no import of `node`, no import of `executor`, no shared library.
Copy this directory anywhere and it runs.

Seven views, each answering one question:

| View | The question |
|---|---|
| **Drift** | What changed out there that we have not re-mapped? |
| **Approvals** | What is waiting on a person? |
| **Fleet** | Which boxes are out there, on what, and which have gone quiet? |
| **Inconsistent** | Where does a business's own surfaces disagree with itself? |
| **Actions** | What was requested, and what actually happened? |
| **Entities** | The graph — a business is not one row. |
| **Content** | Which maps are in the field, and which are only candidates? |

## What it will not do

It reads. It writes exactly two things: a drift's state as you work it, and a
decision on an action held for approval.

It does not execute. Approving moves an action to `PLANNED` so the executor may
pick it up — the executor still fingerprints the screen, still refuses an
unrecognised one, still verifies with something that is not itself. **This
console is not a way around the gate.** If it could run a capability directly,
every guarantee in `contracts/` would be one click wide.

Every decision it does take is appended to `ledger`. `APPROVED` and `DENIED`
are recorded with an executor of `human`, because a person deciding is a step
in the action's history, not an absence of one.

## Two things it is careful about

**A denial is not a failure.** The postcondition was not met, but nothing was
attempted and nothing broke. The tiles count them separately; counting them
together would make a day of careful refusals look like a day of outages.

**Every tab badge counts the rows behind it.** A badge that counts something
narrower than the table it opens is a badge that lies.

## No network

No CDN font, no external stylesheet, no analytics. This gets opened on a dock
office laptop and on the box itself; a console that needs the internet is blank
on exactly the day the network is the problem.
