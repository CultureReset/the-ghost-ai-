# interface — the shell the box boots into

What a customer sees after the boot splash, and the only thing they can reach.

```bash
python3 schema/migrate.py node.sqlite
python3 admin/seed-demo.py node.sqlite      # demo data, optional
ANEXTGENT_USER="Joe Gilchrist" \
python3 interface/server.py node.sqlite --port 8088
```

Then open <http://127.0.0.1:8088>.

## What it is

Its own module, its own port, its own process. It takes a database path and
nothing else — no import of `node`, no import of `admin`, no shared library.
Copy this directory anywhere and it runs.

Six surfaces, one shell:

| Surface | What it answers |
|---|---|
| **Home** | What matters today, across every business on this box. |
| **Business** | One business's workspace — sales, reviews, the floor. |
| **Apps** | What is installed here, and what this box is connected to. |
| **Agents** | What this box knows how to want, and whether it can do it yet. |
| **Automations** | What runs on its own, and what is held for a person. |
| **Files** | What content this box is running and how old it is. |

## Every number is a query

There is no figure in this module that a business would recognise as its own.
Today's sales is `SUM(total_cents)` over tickets closed today; the delta is the
same sum for yesterday. "Reviews to reply" counts reviews with no reply row,
not every review. If the database is empty the screen says so rather than
showing a pleasant fiction — a dashboard that looks healthy when nothing is
connected is worse than no dashboard.

## Agents and automations are not the same list

They rendered as the same three cards once, which made "2 agents available"
secretly mean "2 maps exist" and hid every capability nothing had learned to
do yet.

- An **agent** is a capability — a postcondition plus who is allowed to reach
  it. It comes from `contracts/capabilities/`, found through
  `ANEXTGENT_CONTRACTS` like everywhere else in the system.
- An **automation** is a promoted map that reaches one without asking.

So a capability gets one of four honest statuses: *runs on its own*, *runs but
asks you first*, *asks you first*, or *no map yet* — and *paused, being
re-mapped* when the app underneath it changed.

## Two readings of one ledger

The Hub's Recent Activity is the owner's stream: a guest left five stars, a
ticket closed for $42.18, an item came off the menu. The Automations screen
carries the system's: `review.reply — awaiting approval`. Same ledger, two
readings, neither pretending to be the other.

## Branding is configuration

`ANEXTGENT_BRAND`, `ANEXTGENT_TAGLINE`, `ANEXTGENT_USER`. The wordmark is a
token in `tokens.css`, not a string in markup. Change them and every surface
changes.

## Integrations are a registry, not a parser

`VENDORS` in `server.py` maps a package id to a display name, a description, a
glyph and a colour. Adding an integration is a row. The fallback picks the most
meaningful segment of an unknown id, because nobody calls Toast
`Com.Toasttab.Pos` — and vendors collapse on the resolved name, so FareHarbor
arriving as both a package id and a booking channel is one card, not two
disagreeing with each other.

## No network

No CDN, no font fetch, no analytics, no remote image. Every pixel is a vector
in `art.js` or a colour in `tokens.css`. This is the first thing the box draws
after boot; a screen that needs the internet is a black screen on exactly the
morning the internet is the problem.

The server also refuses to serve anything outside `ui/`. A shell that can be
talked into reading `/etc` is a shell with a file browser nobody asked for.

## It reads, it does not write

There is no POST. The shell shows the gate; it is not a way through it.
Approving something goes through the node API, which still checks the
business's constitution, and the executor still fingerprints the screen before
it touches anything.

## On the box

`ghost-kiosk.service` runs `/usr/lib/anextgent/shell` as its one client under
`cage`. That script waits for the shell to answer, then execs a browser with
every door nailed shut — no address bar, no context menu, no new window, no
devtools, no filesystem. `ghost-shell.container` serves this module read-only
against the node database.
