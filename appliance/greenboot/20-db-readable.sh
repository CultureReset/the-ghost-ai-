#!/bin/bash
# A box that boots but cannot read its own database is worse than one that
# rolls back, because it looks fine.
set -euo pipefail
DB=/var/lib/anextgent/db/node.sqlite
[ -f "$DB" ] || { echo "no database yet — first boot"; exit 0; }
sqlite3 "$DB" "select count(*) from entity;" >/dev/null
sqlite3 "$DB" "pragma integrity_check;" | grep -q '^ok$'
echo "database readable and intact"
