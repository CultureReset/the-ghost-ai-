# What is real, and what is still painted

The honest inventory. One row per table the product reads, and the answer to
one question: **when a real business uses this, what puts data there?**

Re-run it yourself — it is a grep, not a claim:

```bash
for t in drift device heartbeat device_content canonical surface_state \
         constitution_rule observation booking ticket review message event; do
  printf "%-18s " "$t"
  grep -rl -E "INSERT (OR [A-Z]+ )?INTO $t\b|UPDATE $t\b" --include='*.py' \
    node executor ingest fleet resolve admin interface 2>/dev/null \
    | grep -v seed-demo | tr '\n' ' '
  echo
done
```

## Written by a real writer

| Table | Writer | When |
|---|---|---|
| `action`, `ledger` | `node/api.py`, `executor/run.py` | a request comes in, a step happens |
| `evidence` | `executor/run.py` | a screenshot, at the moment of refusal |
| `map_run`, `app_map` | `executor/run.py` | every run, outcome recorded |
| `drift` | `executor/run.py` | a screen did not match its map |
| `device`, `device_content`, `heartbeat` | `fleet/report.py` | enrollment, then every 5 min |
| `canonical`, `surface_state` | `resolve/run.py` | every 10 min, from observations |
| `constitution`, `constitution_rule` | `node/api.py` | `POST /constitution` |
| `source_rank` | `resolve/rank.py --load` | once, then whenever a business changes it |
| `observation` | `ingest/apply.py` | a vendor email arrives |
| `booking`, `lead`, `person`, `person_contact` | `ingest/apply.py` | a vendor email arrives |

## Not written by anything yet

| Table | What it needs | Why it is not built |
|---|---|---|
| `ticket`, `ticket_line` | a POS connector | Toast has an API; it needs a partner agreement |
| `review`, `review_reply` | a Google Business connector | public API, cheapest real connector to build next |
| `message` | SMS or social | needs a number and a provider |
| `event` | a calendar | needs a calendar account |
| `media` | photo upload | no upload path on the box yet |

Those five are why `admin/seed-demo.py` exists. Until a connector fills them,
a Business Hub on a real box shows `$0.00` and "Quiet so far", which is the
correct thing for it to show.

## Still unproven, as opposed to unbuilt

These are written, and have never run against the real thing:

- **`appliance/Containerfile` has never been built.** No privileged podman in
  the environment it was written in. The kiosk path is wired and unbooted.
- **The Android driver has never driven a real app.** Every executor run so far
  has been against `executor/drivers/mock.py`. The five failure paths are
  exercised; the accessibility service on a real handset is not.
- **The vendor maps were written against emails nobody sent.** `ingest/maps/`
  matches FareHarbor, Peek, Airbnb and Toast confirmations that were invented
  for the purpose. One real forwarded email would settle whether they hold.
- **`greenboot` health has never returned anything but `unknown`** outside a
  real bootc box, which is correct — `fleet/report.py` refuses to call a box
  healthy on a machine where greenboot never ran.

## The rule this file exists to enforce

A number on a screen has a writer, or it has a seed. If it has a seed, it is
not a feature yet. `admin/seed-demo.py` refuses to run without
`--i-know-this-is-fake` and refuses to touch a database that already has rows a
real writer produced — because invented rows and real ones are
indistinguishable once they are in the same table.
