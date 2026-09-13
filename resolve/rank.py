#!/usr/bin/env python3
"""Per-field source ordering: who wins when two sources disagree.

Ranks are rows, not code. A field class plus a source gives a number; lower
wins. `*` is the fallback class, used when a field has no class of its own.

    python3 -m resolve.rank --db node.sqlite --load           # ship defaults
    python3 -m resolve.rank --db node.sqlite --list
    python3 -m resolve.rank --db node.sqlite --set hours owner 0

The defaults say: the owner beats the till, the till beats the website, the
website beats social. That ordering is a business decision, not a technical
one, which is why it is data a business can change.
"""
import argparse, sqlite3, sys

# field_class, source, rank
DEFAULTS = [
    # Anything, unless a field class below says otherwise.
    ("*", "owner",          0),
    ("*", "staff",          10),
    ("*", "android",        20),   # read off the vendor's own app
    ("*", "email",          30),   # a confirmation the vendor sent
    ("*", "browser",        40),   # scraped from a public page
    ("*", "inferred",       90),

    # Hours: the person who unlocks the door outranks every machine.
    ("hours", "owner",      0),
    ("hours", "staff",      5),
    ("hours", "android",    20),
    ("hours", "browser",    40),

    # Price: the till is the system of record, not the printed menu.
    ("price", "android",    0),    # the POS
    ("price", "owner",      5),
    ("price", "email",      30),
    ("price", "browser",    40),

    # Availability: whoever takes the booking knows first.
    ("availability", "email",   0),
    ("availability", "android", 10),
    ("availability", "owner",   20),
]


def field_class(field):
    """'hours.friday.closes' -> 'hours'. The class is the first segment."""
    return (field or "").split(".", 1)[0]


def source_kind(source):
    """'email:fareharbor' -> 'email'. Rank by how a thing was learned, not by
    which vendor it came from -- otherwise every new integration needs a new
    rank row before it can ever win an argument."""
    return (source or "").split(":", 1)[0]


def load_defaults(db):
    for fc, src, rank in DEFAULTS:
        db.execute("""INSERT INTO source_rank(field_class,source,rank)
                      VALUES (?,?,?)
                      ON CONFLICT(field_class,source) DO UPDATE SET rank=excluded.rank""",
                   (fc, src, rank))
    db.commit()
    return len(DEFAULTS)


def rank_of(db, field, source, _cache={}):
    """Lower wins. An unknown source ranks below every known one rather than
    above: a source nobody has ranked has not earned the right to overwrite
    the owner."""
    fc, sk = field_class(field), source_kind(source)
    key = (fc, sk)
    if key not in _cache:
        r = db.execute("""SELECT rank FROM source_rank
                           WHERE field_class=? AND source=?""", (fc, sk)).fetchone()
        if r is None:
            r = db.execute("""SELECT rank FROM source_rank
                               WHERE field_class='*' AND source=?""", (sk,)).fetchone()
        _cache[key] = r[0] if r else 999
    return _cache[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--load", action="store_true", help="write the shipped defaults")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--set", nargs=3, metavar=("FIELD_CLASS", "SOURCE", "RANK"))
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    if a.load:
        print(f"loaded {load_defaults(db)} rank rows")
    if a.set:
        fc, src, rank = a.set
        db.execute("""INSERT INTO source_rank(field_class,source,rank) VALUES (?,?,?)
                      ON CONFLICT(field_class,source) DO UPDATE SET rank=excluded.rank""",
                   (fc, src, int(rank)))
        db.commit()
        print(f"{fc}/{src} = {rank}")
    if a.list or not (a.load or a.set):
        for r in db.execute("""SELECT field_class, source, rank FROM source_rank
                               ORDER BY field_class, rank"""):
            print(f"  {r[0]:<14} {r[1]:<10} {r[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
