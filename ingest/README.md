# ingest

Email is the universal integration surface. Every vendor already emails the
business, and none of them can turn it off without breaking their own product.

```bash
python3 -m ingest.run --db node.sqlite --entity e_dol mail/*.eml
```

## Vendors are data, not code

`maps/*.json` — one file per vendor. Adding a vendor is adding a file. **Fixing
a vendor that changed its template is editing a file**, which matters more than
it sounds: that fix is a signed artifact every node pulls overnight, not a code
release, a rebuilt image and a fleet roll.

That is the whole churn-absorption loop, and it only works if the map is data:

```
template changes  ->  DRIFTED, nothing written
                  ->  edit maps/<vendor>.json, bump map_version
                  ->  sign, push
                  ->  every node parses both the old and new template
```

A map declares `match` (is this message theirs), `fingerprint` (markers that
must be present), `fields` (patterns and a type), and for summaries a
`repeating` block.

## Fingerprint before parsing

Same rule as the executor. If the markers a map was written against are missing,
the message is recorded `DRIFTED` and **nothing is written**. A vendor changing
their template fails loudly on one message instead of quietly writing wrong
numbers for a week.

## Types, and why `datetime` returns None

`string int money datetime phone email`. The date parser returns `None` rather
than a guess — a wrong timestamp silently books the wrong slot, which is worse
than not booking one.

## Replay is safe

Bookings upsert on `(channel, external_ref)`. A cancellation is terminal, so an
older booking notice arriving later cannot un-cancel a seat already back in
inventory. A person is only created when there is a phone or email to
deduplicate against.
