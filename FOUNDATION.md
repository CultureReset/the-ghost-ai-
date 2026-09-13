# The foundation

Everything else depends on this. Written to be run, not read.

```
contracts/     what a capability is, what an action is, what a VAPP is
schema/        the database — entity graph, neutral core, vertical tables
appliance/     the operating system as one signed image
sdk/           an example VAPP that validates against the contracts
```

## Run it

```bash
# the contracts, plus any file you hand it
python3 contracts/validate.py
python3 contracts/validate.py path/to/vapp.json

# build the database
sqlite3 node.sqlite < schema/migrations/0001_core.sql
for f in schema/migrations/000[2-6]*.sql; do sqlite3 node.sqlite < "$f"; done

# build the OS
podman build -t quay.io/anextgent/ghost-os:2026.09.1 \
  --build-arg VERSION=2026.09.1 .
```

Neither the validator nor the schema has a dependency. Both run on the box.

## What is encoded here, and nowhere else

**A business is a graph.** `entity` is self-referencing. Flora-Bama → Marina →
Dolphin Cruises, each node independently addressable, each owning or inheriting
via `entity_ancestry`. There is no "one business = one row", because most
businesses worth selling to are not one row.

**Nothing is overwritten.** Facts land in `observation` with a source, a device,
an actor and a timestamp. `canonical` is computed from them and can be rebuilt
at any time. Provenance is the one thing that cannot be added later.

**Two dimensions of state.** `action.lifecycle` says where it is;
`action.verification` says what happened. The database refuses a `FINISHED` row
without a verdict, because a silent partial success reported as "completed" is
worse than a clean failure.

**The verifier is not the executor.** `validate.py` fails any write capability
whose `verify.by` overlaps its `executors`. Writing through the phone and
reading back through the phone is self-certification with extra steps.

**A capability names what, never how.** `postcondition` plus permitted
executors. The moment a capability mentions a resource-id or a library, the
executor stops being swappable.

**Apps get capabilities, not tables.** `validate.py` rejects a manifest that
asks for SQL, names an unknown capability, or exposes a write on the public
surface. The Agent Plugins specification states it has no permission system;
this is that layer.

**`app_map` is keyed on `app × app_version × map_version`.** Not `app`. An
application redesign is a new row, not a corrupted one.

## What this is not

Not the product. This is the layer the fifteen systems agree on — the thing
that had to exist before any of them could be built against anything.

The executor, the parser, the availability engine, the store, the SDK runtime,
the apps and the model work are not here. What is here is the contract they all
have to satisfy, and a machine that boots.
