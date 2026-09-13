#!/usr/bin/env python3
"""Compute canonical values from observations.

    python3 -m resolve.run --db node.sqlite
    python3 -m resolve.run --db node.sqlite --entity e_fb --field hours.5.closes
    python3 -m resolve.run --db node.sqlite --explain

Rebuildable from scratch at any time: `canonical` is a cache of a decision,
never a place anything is typed. Delete every row and run this and you get the
same answers back, which is the property that makes the observation log worth
keeping.

The rule, in one sentence: for each (entity, field), take the best-ranked
source, and within that source the most recent observation. Rank first, then
recency -- not the other way round. A scraper that runs every hour would
otherwise outvote the owner simply by being noisier.
"""
import argparse, sqlite3, sys, uuid
from .rank import rank_of, field_class, source_kind

# Which observation sources are things a customer can actually read. A losing
# observation from one of these is not just a worse guess -- it is the business
# publicly saying something it does not believe.
SURFACE_OF = {"browser": lambda q: q or "website",
              "own": lambda q: "own"}


def surface_for(source):
    kind = source_kind(source)
    if kind not in SURFACE_OF:
        return None
    qualifier = (source.split(":", 1) + [None])[1]
    return SURFACE_OF[kind](qualifier)


def candidates(db, entity_id=None, field=None):
    sql = """SELECT entity_id, field FROM observation"""
    args, where = [], []
    if entity_id:
        where.append("entity_id=?"); args.append(entity_id)
    if field:
        where.append("field=?"); args.append(field)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY entity_id, field"
    return db.execute(sql, args).fetchall()


def decide(db, entity_id, field):
    """Return (observation_row, losers) for one field, or (None, [])."""
    obs = db.execute("""SELECT id, value, source, observed_at, confidence
                          FROM observation
                         WHERE entity_id=? AND field=?
                         ORDER BY observed_at DESC""", (entity_id, field)).fetchall()
    if not obs:
        return None, []
    scored = sorted(obs, key=lambda o: (rank_of(db, field, o[2]),
                                        # observed_at descending inside a rank
                                        _neg(o[3])))
    return scored[0], scored[1:]


def _contradictions(db, eid, field, win, losers):
    """Record what each public surface says, against what is true.

    This is the other half of the resolver and the reason the whole thing is
    worth running. Deciding the canonical value is only useful if you also know
    which of your own surfaces is still telling customers something else --
    that is the difference between "we fixed it" and "we fixed it everywhere".

    A surface that agrees is VERIFIED, one that disagrees is CONTRADICTED. A
    surface nobody has looked at recently is neither, and gets no row at all:
    silence is not agreement."""
    for o in [win] + list(losers):
        surface = surface_for(o[2])
        if not surface:
            continue
        verdict = "VERIFIED" if o[1] == win[1] else "CONTRADICTED"
        db.execute("""INSERT INTO surface_state(id,entity_id,field,surface,
                                                observed,verdict,checked_at)
                      VALUES (?,?,?,?,?,?,?)
                      ON CONFLICT(entity_id,field,surface) DO UPDATE SET
                        observed=excluded.observed, verdict=excluded.verdict,
                        checked_at=excluded.checked_at""",
                   ("ss_" + uuid.uuid4().hex[:12], eid, field, surface,
                    o[1], verdict, o[3]))


def _neg(ts):
    """Sort a timestamp string descending inside an ascending sort."""
    return tuple(-ord(c) for c in (ts or ""))


def resolve(db, entity_id=None, field=None, explain=False):
    changed, seen = 0, 0
    for eid, f in candidates(db, entity_id, field):
        seen += 1
        win, losers = decide(db, eid, f)
        if not win:
            continue
        cur = db.execute("""SELECT value, from_obs_id FROM canonical
                             WHERE entity_id=? AND field=?""", (eid, f)).fetchone()
        if cur and cur[1] == win[0]:
            continue
        db.execute("""INSERT INTO canonical(entity_id,field,value,from_obs_id,decided_at)
                      VALUES (?,?,?,?,datetime('now'))
                      ON CONFLICT(entity_id,field) DO UPDATE SET
                        value=excluded.value, from_obs_id=excluded.from_obs_id,
                        decided_at=excluded.decided_at""",
                   (eid, f, win[1], win[0]))
        changed += 1
        _contradictions(db, eid, f, win, losers)
        if explain:
            print(f"\n  {eid}  {f}")
            print(f"    -> {win[1]!r}")
            print(f"       from {win[2]} (rank {rank_of(db, f, win[2])})"
                  f" observed {win[3]}")
            for l in losers:
                print(f"       over {l[2]} (rank {rank_of(db, f, l[2])})"
                      f" observed {l[3]}: {l[1]!r}")
    db.commit()
    return seen, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--entity")
    ap.add_argument("--field")
    ap.add_argument("--explain", action="store_true",
                    help="say which source won each field and what it beat")
    a = ap.parse_args()
    db = sqlite3.connect(a.db, timeout=15)
    db.execute("PRAGMA foreign_keys=ON")
    if not db.execute("SELECT COUNT(*) FROM source_rank").fetchone()[0]:
        print("no source_rank rows — run:  python3 -m resolve.rank --db "
              f"{a.db} --load", file=sys.stderr)
        return 1
    seen, changed = resolve(db, a.entity, a.field, a.explain)
    print(f"\n{seen} fields considered, {changed} canonical values written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
