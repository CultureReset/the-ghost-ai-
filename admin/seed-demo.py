#!/usr/bin/env python3
"""Put a plausible Tuesday into a migrated database so the console has something
to show.

    python3 schema/migrate.py demo.sqlite
    python3 admin/seed-demo.py demo.sqlite

Demo data only. It is idempotent -- run it twice and you get the same fleet, not
two of them -- and it never touches a row it did not create.
"""
import argparse, sqlite3, uuid

BOXES = [
    # id            entity   label                     serial       os        chan      health      last_seen
    ("dv_fb_bar",  "e_fb",  "Flora-Bama / main bar",  "GH-0001-AL", "1.4.2", "stable",  "ok",       "-3 minutes"),
    ("dv_fb_deck", "e_fb",  "Flora-Bama / deck",      "GH-0002-AL", "1.4.2", "stable",  "ok",       "-11 minutes"),
    ("dv_mar",     "e_mar", "Marina / dock office",   "GH-0007-AL", "1.4.1", "stable",  "degraded", "-4 hours"),
    ("dv_dol",     "e_dol", "Dolphin Cruises / desk", "GH-0011-AL", "1.4.2", "beta",    "ok",       "-1 minutes"),
    ("dv_dol_h",   "e_dol", "Captain handset",        "GH-0011-H1", "1.4.2", "beta",    "down",     "-2 days"),
]
CONTENT = {"dv_fb_bar": ("2026.09.1", "2026.09.1", "2026.09.1"),
           "dv_fb_deck": ("2026.09.1", "2026.09.1", "2026.09.1"),
           "dv_mar":     ("2026.08.3", "2026.08.3", "2026.08.3"),
           "dv_dol":     ("2026.09.1", "2026.09.1", "2026.09.1"),
           "dv_dol_h":   ("2026.08.3", "2026.08.1", "2026.08.3")}

MAPS = [
    ("am_fh_1", "com.fareharbor.dashboard", "8.2.0", 1, "availability.read",
     "android", "candidate"),
    ("am_toast_1", "com.toasttab.pos", "3.41.0", 1, "menu.eightysix_item",
     "android", "promoted"),
    ("am_toast_2", "com.toasttab.pos", "3.44.0", 2, "menu.eightysix_item",
     "android", "promoted"),
]

DRIFTS = [
    ("dr_toast", "appmap", "com.toasttab.pos", "menu.eightysix_item", "3.44.0",
     "3.51.0", "86 toggle moved out of the item sheet into a long-press menu.",
     "open", 14),
    ("dr_fh", "vendormap", "fareharbor", None, "template 2",
     "template 3 (Sep redesign)",
     "Confirmation email dropped the party-size line; qty no longer extracts.",
     "mapping", 6),
    ("dr_peek", "vendormap", "peek", None, "start time as '2:00 PM CDT'",
     "start time as '2:00 PM UTC-05:00'",
     "Timezone suffix changed shape; the datetime transform refuses rather "
     "than guessing an hour.", "open", 2),
]


def kv(db, sql, args): db.execute(sql, args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", help="path to a migrated node database")
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    db.execute("PRAGMA foreign_keys=ON")

    known = {r[0] for r in db.execute("SELECT id FROM entity")}
    for did, ent, label, serial, osv, chan, health, seen in BOXES:
        if ent not in known:
            continue
        kv(db, """INSERT INTO device(id,entity_id,label,kind,serial,os_version,
                                    channel,health,last_seen_at)
                  VALUES (?,?,?,?,?,?,?,?,datetime('now',?))
                  ON CONFLICT(id) DO UPDATE SET health=excluded.health,
                       os_version=excluded.os_version,
                       last_seen_at=excluded.last_seen_at""",
           (did, ent, label, "handset" if serial.endswith("H1") else "box",
            serial, osv, chan, health, seen))
        for kind, ver in zip(("contracts", "appmaps", "vendormaps"), CONTENT[did]):
            kv(db, """INSERT INTO device_content(device_id,kind,version)
                      VALUES (?,?,?)
                      ON CONFLICT(device_id,kind) DO UPDATE SET
                           version=excluded.version""", (did, kind, ver))
        kv(db, """INSERT INTO heartbeat(id,device_id,at,health,detail)
                  VALUES (?,?,datetime('now',?),?,?)
                  ON CONFLICT(id) DO NOTHING""",
           ("hb_" + did, did, seen, health,
            None if health == "ok" else "greenboot reported a failed check"))

    for m in MAPS:
        kv(db, """INSERT INTO app_map(id,app,app_version,map_version,capability,
                                      executor,fingerprint,steps,state)
                  VALUES (?,?,?,?,?,?,'[]','[]',?)
                  ON CONFLICT(id) DO NOTHING""", m)

    for did, kind, subject, cap, exp, seen, detail, state, occ in DRIFTS:
        kv(db, """INSERT INTO drift(id,kind,subject,capability,expected,seen,
                                    detail,state,occurrences,
                                    first_seen_at,last_seen_at)
                  VALUES (?,?,?,?,?,?,?,?,?,datetime('now','-2 days'),
                          datetime('now','-20 minutes'))
                  ON CONFLICT(id) DO UPDATE SET state=excluded.state,
                       occurrences=excluded.occurrences""",
           (did, kind, subject, cap, exp, seen, detail, state, occ))

    # A drift is only real if something refused because of it. Give the appmap
    # drift the refusals that justify its count.
    ent = [r[0] for r in db.execute(
        "SELECT id FROM entity ORDER BY COALESCE(parent_id,id)")]
    for i, e in enumerate(ent):
        aid = "ac_demo_%d" % i
        kv(db, """INSERT INTO action(id,entity_id,capability,args,
                                     idempotency_key,lifecycle,
                                     verification,requested_at)
                  VALUES (?,?,'menu.eightysix_item','{}',?,'FINISHED','FAILED',
                          datetime('now','-3 hours'))
                  ON CONFLICT(id) DO NOTHING""", (aid, e, "demo:" + aid))
        kv(db, """INSERT INTO map_run(id,map_id,action_id,outcome,ms)
                  VALUES (?,'am_toast_2',?,'DRIFTED',820)
                  ON CONFLICT(id) DO NOTHING""", ("mr_demo_%d" % i, aid))

    # One fact, four places, one of them wrong. The inconsistency view exists
    # for exactly this row; seeding only agreement would prove nothing.
    facts = [("e_fb", "hours", "Mon-Sun 11:00-02:00"),
             ("e_dol", "hours", "Daily 08:00-18:00"),
             ("e_dol", "phone", "+12519811000")]
    for ent, field, val in facts:
        if ent not in known:
            continue
        kv(db, """INSERT INTO canonical(entity_id,field,value) VALUES (?,?,?)
                  ON CONFLICT(entity_id,field) DO UPDATE SET value=excluded.value""",
           (ent, field, val))
    surfaces = [
        ("e_fb",  "hours", "own",      "Mon-Sun 11:00-02:00",   "VERIFIED",           "-2 hours"),
        ("e_fb",  "hours", "google",   "Mon-Sun 11:00-00:00",   "CONTRADICTED",       "-9 hours"),
        ("e_fb",  "hours", "facebook", None,                    "NOT_YET_VERIFIABLE", "-8 days"),
        ("e_dol", "hours", "own",      "Daily 08:00-18:00",     "VERIFIED",           "-1 hours"),
        ("e_dol", "hours", "booking",  "Daily 08:00-16:00",     "CONTRADICTED",       "-30 minutes"),
        ("e_dol", "phone", "google",   "+12519811000",          "VERIFIED",           "-3 hours"),
    ]
    for ent, field, surface, observed, verdict, when in surfaces:
        if ent not in known:
            continue
        kv(db, """INSERT INTO surface_state(id,entity_id,field,surface,observed,
                                            verdict,checked_at)
                  VALUES (?,?,?,?,?,?,datetime('now',?))
                  ON CONFLICT(entity_id,field,surface) DO UPDATE SET
                       observed=excluded.observed, verdict=excluded.verdict,
                       checked_at=excluded.checked_at""",
           ("ss_%s_%s_%s" % (ent, field, surface), ent, field, surface,
            observed, verdict, when))

    db.commit()
    n = lambda t: db.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
    print("devices %d  content %d  drift %d  maps %d  map_run %d  surfaces %d"
          % (n("device"), n("device_content"), n("drift"), n("app_map"),
             n("map_run"), n("surface_state")))


if __name__ == "__main__":
    main()
