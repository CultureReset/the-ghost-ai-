# schema

SQLite for the node; the DDL is deliberately plain so it ports to Postgres
with little more than `TEXT`→`uuid` and `datetime('now')`→`now()`.

| file | what |
|---|---|
| `0001_core.sql` | entity graph, attributes, people, observation/canonical, surface consistency, actions, ledger, evidence, app maps, installs |
| `0002_restaurant.sql` | menus, sections, items, happy hour, tables, the QR scan → ticket → line loop |
| `0003_charter.sql` | vessels, trips, start times, pricing tiers, addons, deposits, waivers, slots, bookings, the `availability` view |
| `0004_marina.sql` | slips, assignments, rental inventory, dock services |
| `0005_trades.sql` | service types, areas, quote requests, appointments, job photos |
| `0006_customer.sql` | leads, reconciliation, waitlist, messages, reviews, replies, loyalty, `item_rating`, `fillable` |

## Three views are the product

- **`availability`** — capacity minus confirmed bookings minus safety hold.
  Never stored, always computed, so a cancellation restores seats with no job
  to run.
- **`consistency`** — canonical value against every external surface, with how
  many days stale. This is CyberCheck.
- **`fillable`** — open seats joined to people who asked about that time and
  have not been told. This is the cancellation loop.

## Common centre, vertical edges

`0001` is shared by every business. `0002`–`0005` are the operational facts
that differ. A marina that runs a kitchen loads both. Adding a vertical means
adding one file, not a new platform.
