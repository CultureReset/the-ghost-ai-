#!/usr/bin/env python3
"""Apply migrations to a node database. Idempotent, ordered, no dependencies.

    python3 schema/migrate.py node.sqlite            # core + every vertical
    python3 schema/migrate.py node.sqlite --core     # core only
    python3 schema/migrate.py node.sqlite --status
"""
import sqlite3, sys, os, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

def applied(db):
    db.execute("""CREATE TABLE IF NOT EXISTS schema_migration (
        name TEXT PRIMARY KEY, sha256 TEXT NOT NULL,
        applied_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    return {r[0]: r[1] for r in db.execute("SELECT name, sha256 FROM schema_migration")}

def main(argv):
    if not argv:
        print(__doc__); return 1
    path, flags = argv[0], argv[1:]
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    done = applied(db)

    files = sorted(glob.glob(f"{HERE}/migrations/*.sql"))
    if "--core" in flags:
        files = [f for f in files if "0001" in os.path.basename(f)]

    if "--status" in flags:
        for f in files:
            n = os.path.basename(f)
            print(f"{'applied ' if n in done else 'pending '} {n}")
        return 0

    for f in files:
        name = os.path.basename(f)
        body = open(f, encoding="utf-8").read()
        sha = hashlib.sha256(body.encode()).hexdigest()
        if name in done:
            if done[name] != sha:
                print(f"CHANGED  {name} — already applied with different content.")
                print("         Migrations are append-only. Add a new file instead.")
                return 1
            print(f"skip     {name}")
            continue
        db.executescript(body)
        db.execute("INSERT INTO schema_migration(name, sha256) VALUES (?,?)", (name, sha))
        db.commit()
        print(f"applied  {name}")

    t = db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    v = db.execute("SELECT count(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
    print(f"\n{path}: {t} tables, {v} views")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
