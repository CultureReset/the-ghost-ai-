# SDK

An app is a directory that validates against `contracts/`. That is the whole
interface.

## Build one

1. Write `plugin.json` to the Agent Plugins 1.0.0 spec.
2. Put the A NEXT GENT manifest under `extensions["io.anextgent"]`.
3. Declare `reads` and `writes` as **capability names**. Never a table, never a
   query, never a path.
4. Ship any of three targets: `node` (logic), `public` (profile sections),
   `owner` (the console view).
5. Validate: `python3 contracts/validate.py your/plugin-extension.json`

## What the store checks before listing

- The manifest matches the schema.
- Every capability named exists in the registry.
- Nothing asks for data access directly.
- No write capability is exposed on the public MCP surface.
- `source_sha` is a full forty-character commit. A tag can be moved.

An app that fails any of these is not listed. That gate is the difference
between this store and a plugin index.

## What an app never gets

The database. Credentials. Another app's data. A route from the public target
back into the node. Those are absences in the architecture, not settings.

`example-app/` is a working manifest that passes.
