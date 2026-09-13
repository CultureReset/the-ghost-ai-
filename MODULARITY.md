# Modularity, audited

Not claimed — checked, with the checks written down so they can be re-run.

## The dependency graph

```
contracts  -> nothing
schema     -> nothing
ingest     -> nothing
executor   -> nothing
node       -> nothing
sdk        -> nothing
appliance  -> nothing
```

No module imports another. There is no shared library, no `common/`, no base
class inherited across boundaries. That is the property that makes them
splittable, and it holds.

## Proven by splitting them

Copy `node`, `executor`, `ingest` and `schema` into four bare directories, put
the content somewhere else entirely, and run:

```bash
export ANEXTGENT_CONTRACTS=/bundle/contracts
export ANEXTGENT_APPMAPS=/bundle/appmaps
export ANEXTGENT_MAPS=/bundle/vendormaps

python3 schema/migrate.py n.sqlite        # 60 tables, 6 views
python3 -m ingest.run  --db n.sqlite ...  # parsed 1
python3 -m executor.run --db n.sqlite ... # VERIFIED 4/4
python3 node/api.py    --db n.sqlite      # {"ok": true, "capabilities": 6}
```

All four, in separate repositories, against content published from a third
place.

**This did not work before the audit.** `node` and `executor` found `contracts`
by walking up the directory tree, which silently required them to be siblings
forever. Content location is configuration now, and a module that cannot find
what it needs says which variable to set instead of raising a `FileNotFoundError`
about a path nobody chose.

That was not a cosmetic fix. In production these are not source files at all —
a capability definition and a vendor map are **pulled artifacts**. A path that
assumes a checkout cannot pull.

## What is deliberately still coupled

Three, and each is a boundary rather than an accident.

- **`SOURCES` in `node/api.py`** names views from `schema`. A read capability can
  only project from that whitelist. If a pushed capability could name an
  arbitrary table, a content update would be remote code execution on every box.
  This stays in the binary.
- **Transform types in `ingest/engine.py`** (`money`, `phone`, `datetime`). Same
  reason: a map supplies patterns, never code.
- **Verbs in `executor/appmap.py`**. Same again. A map describes taps, it does
  not define them.

Everything a pushed file is allowed to say is data. Everything it could abuse is
compiled in. That line is the trust boundary and it is drawn on purpose.

## Splitting it, when you want to

```
anextgent/contracts    capability registry, manifests, validator
anextgent/schema       migrations and the migrator
anextgent/ingest       vendor maps and the engine
anextgent/executor     app maps and the drivers
anextgent/node         the API
anextgent/appliance    the bootc image
anextgent/sdk          what a developer builds against
```

`contracts` is the only one anything else agrees with, and it agrees by
configuration rather than by adjacency. Nothing has to move for this to work;
the audit above already runs them apart.

## Where this is not Red Hat yet

Red Hat's structure is five things. Two exist.

| | |
|---|---|
| **Content** | contracts, vendor maps, app maps — present, and now pullable |
| **Factory** | build, scan, sign, publish — **absent** |
| **Distribution** | registry, channels, mirror, staged rollout — **absent** |
| **Entitlement** | which box may pull what, today — **absent**. `grant_scope` is per-app, not per-box |
| **Fleet** | what version is on which machine — **absent** |

The gap is one sentence: **content is pullable but nothing publishes it and
nothing pulls it.** A box can be told where its maps live; there is no channel
to fetch them from, no signature to check, no entitlement to satisfy, and no
record of which box ended up on which version.

Until that exists, "download the box and be good to go" means someone copies
files by hand. Everything the distribution layer needs on the box side is in
place — configured paths, versioned maps, a fingerprint that fails loudly when
content is stale. What is missing is the other end of the wire.
