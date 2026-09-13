#!/usr/bin/env python3
"""Run the mailbox through the node.

    python3 -m ingest.run --db node.sqlite --entity e_charter ingest/samples/*.eml

Idempotent: replaying the same messages writes nothing new.
"""
import argparse, glob, sqlite3, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingest.parse import parse_message
from ingest.apply import apply_result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--entity", required=True)
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()

    db = sqlite3.connect(a.db); db.execute("PRAGMA foreign_keys=ON")
    paths = [p for f in a.files for p in glob.glob(f)]
    counts = {"PARSED": 0, "DRIFTED": 0, "UNMATCHED": 0}

    for p in sorted(paths):
        r = parse_message(open(p, encoding="utf-8").read())
        counts[r.status] = counts.get(r.status, 0) + 1
        res = apply_result(db, a.entity, r)
        flag = {"PARSED": "ok  ", "DRIFTED": "DRIFT", "UNMATCHED": "skip"}[r.status]
        detail = ""
        if r.status == "DRIFTED":
            detail = f"  vendor={r.vendor} missing={r.missing}"
        elif res.get("duplicate"):
            detail = "  (already seen)"
        elif res.get("reconciled_lead"):
            detail = f"  reconciled lead {res['reconciled_lead']}"
        elif res.get("updated"):
            detail = f"  -> {res['updated']}"
        print(f"{flag} {os.path.basename(p):34}{detail}")
    db.commit()

    print(f"\nparsed {counts['PARSED']}  drifted {counts['DRIFTED']}  "
          f"unmatched {counts['UNMATCHED']}")
    if counts["DRIFTED"]:
        print("\nA drifted message means a vendor changed their template. Nothing was\n"
              "written from it. Re-map the parser once; every node gets the fix.")
    return 2 if counts["DRIFTED"] else 0


if __name__ == "__main__":
    sys.exit(main())
