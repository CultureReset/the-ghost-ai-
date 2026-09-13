#!/usr/bin/env python3
"""MADE-UP DATA. Not yours, not anybody's.

    python3 admin/seed-demo.py demo.sqlite --i-know-this-is-fake

Every row this writes is invented: the business, the address, the tickets, the
reviews, the text messages. It exists so a screen has something on it during
development. It is not a data source and nothing in the product depends on it.

It refuses to run without the flag, and it refuses to touch a database that
already has real rows in it, because the whole reason this file is dangerous is
that its output is indistinguishable from a real business's once it is in the
table.

If you are looking at this because a dashboard showed you numbers you did not
recognise: the numbers came from here, and the real question is which writer is
missing. As of now the writers are:

    drift            executor/run.py       on a refused screen
    device           fleet/report.py       --enroll, then a timer
    device_content   fleet/report.py       digests read off the filesystem
    heartbeat        fleet/report.py       every 5 minutes
    canonical        resolve/run.py        observation -> the answer
    surface_state    resolve/run.py        and what each surface still says
    constitution     node/api.py           POST /constitution
    observation      ingest/apply.py       vendor email
    booking, lead    ingest/apply.py       vendor email
    action, ledger   node/api.py, executor/run.py

    ticket           NOTHING YET -- needs a POS connector
    review           NOTHING YET -- needs a Google Business connector
    message          NOTHING YET -- needs an SMS/social connector
    event            NOTHING YET -- needs a calendar connector

The four at the bottom are the honest gaps. Everything above them is real.
"""
import argparse, hashlib, sqlite3, sys, uuid

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

# ------------------------------------------------------------------ the floor
# The Business Hub reads real rows or it is a painting. A restaurant needs a
# menu, tickets that closed today, reviews that have not been answered and
# messages nobody has read.
MENU = [
    ("Starters", [("Royal Red Shrimp", 1600, 1), ("Smoked Tuna Dip", 1400, 1),
                  ("Fried Green Tomatoes", 1200, 1)]),
    ("Mains",    [("Grouper Sandwich", 2100, 1), ("Shrimp Scampi", 1899, 1),
                  ("Blackened Redfish", 2800, 0), ("Bushwacker Wings", 1500, 1)]),
    ("Raw Bar",  [("Gulf Oysters, dozen", 2400, 1), ("Peel & Eat, half", 1800, 1)]),
]
REVIEWS = [
    (5, "Amazing food and great service. Will be back!", "google", "-2 hours", None),
    (5, "Best grouper sandwich on the beach. Worth the wait.", "google", "-9 hours", None),
    (4, "Great music, drinks took a while on a Saturday.", "google", "-1 days", None),
    (2, "Waited 40 minutes for a table we had booked.", "google", "-1 days", None),
    (5, "Sunset from the deck is unreal.", "facebook", "-3 days", "Thank you!"),
]
MESSAGES = [
    ("in", "sms", "Do you have outdoor seating tonight?", "-8 hours"),
    ("in", "sms", "Are you open Thanksgiving?", "-2 hours"),
    ("out", "sms", "We are -- 11 to 6. See you then.", "-30 hours"),
]
EVENTS = [
    ("Team meeting", "11:00", "Prep for weekend specials"),
    ("New menu photos", "14:00", "Post to Google & Instagram"),
    ("Dinner rush", "17:00", "Peak staffing in place"),
    ("Scheduled post", "20:00", "Live music this Friday"),
]
APPS = [("io.anextgent.menu", "1.2.0"), ("io.anextgent.reviews", "1.0.4"),
        ("io.anextgent.hours", "1.1.0"), ("io.anextgent.messages", "0.9.2")]


def seed_floor(db, kv, known):
    ent = "e_fb"
    if ent not in known:
        return
    kv(db, """INSERT INTO location(entity_id,line1,city,region,postal,country)
              VALUES (?,'17401 Perdido Key Dr','Perdido Key','AL','32507','US')
              ON CONFLICT(entity_id) DO NOTHING""", (ent,))
    kv(db, """INSERT INTO menu(id,entity_id,name) VALUES ('mn_main',?,'All Day')
              ON CONFLICT(id) DO NOTHING""", (ent,))
    for si, (section, items) in enumerate(MENU):
        sid = "ms_%d" % si
        kv(db, """INSERT INTO menu_section(id,menu_id,name,sort)
                  VALUES (?,'mn_main',?,?) ON CONFLICT(id) DO NOTHING""",
           (sid, section, si))
        for ii, (name, cents, avail) in enumerate(items):
            # eightysixed_at must be a timestamp, not the text of a SQL call --
            # a bound parameter is never evaluated, and the screen showed
            # "NaN days ago" as a result.
            kv(db, """INSERT INTO menu_item(id,section_id,name,price_cents,
                                            available,eightysixed_at,sort)
                      VALUES (?,?,?,?,?,
                              CASE WHEN ?=0 THEN datetime('now','-3 hours') END,?)
                      ON CONFLICT(id) DO UPDATE SET available=excluded.available,
                           price_cents=excluded.price_cents,
                           eightysixed_at=excluded.eightysixed_at""",
               ("mi_%d_%d" % (si, ii), sid, name, cents, avail, avail, ii))

    for i in range(6):
        kv(db, """INSERT INTO dining_table(id,entity_id,label,seats,qr_token)
                  VALUES (?,?,?,?,?) ON CONFLICT(id) DO NOTHING""",
           ("dt_%d" % i, ent, "T%d" % (i + 1), 2 + (i % 3) * 2, "qr_%d" % i))

    # Tickets that closed today, and the same count yesterday for the delta.
    totals_today = [4218, 2650, 1899, 3340, 2075, 5512, 1280, 2960]
    totals_yday  = [3900, 2400, 2100, 2800, 1950, 4100, 1500]
    for i, c in enumerate(totals_today):
        kv(db, """INSERT INTO ticket(id,entity_id,table_id,opened_at,closed_at,
                                     total_cents)
                  VALUES (?,?,?,datetime('now','-%d hours'),
                          datetime('now','-%d hours'),?)
                  ON CONFLICT(id) DO NOTHING""" % (i + 2, i + 1),
           ("tk_t%d" % i, ent, "dt_%d" % (i % 6), c))
    for i, c in enumerate(totals_yday):
        kv(db, """INSERT INTO ticket(id,entity_id,table_id,opened_at,closed_at,
                                     total_cents)
                  VALUES (?,?,?,datetime('now','-1 days','-%d hours'),
                          datetime('now','-1 days','-%d hours'),?)
                  ON CONFLICT(id) DO NOTHING""" % (i + 2, i + 1),
           ("tk_y%d" % i, ent, "dt_%d" % (i % 6), c))

    for i, (rating, body, source, when, reply) in enumerate(REVIEWS):
        rid = "rv_h%d" % i
        kv(db, """INSERT INTO review(id,entity_id,subject_kind,subject_id,rating,
                                     body,source,created_at)
                  VALUES (?,?,'entity',?,?,?,?,datetime('now',?))
                  ON CONFLICT(id) DO NOTHING""",
           (rid, ent, ent, rating, body, source, when))
        if reply:
            kv(db, """INSERT INTO review_reply(id,review_id,draft,posted_at)
                      VALUES (?,?,?,datetime('now','-2 days'))
                      ON CONFLICT(id) DO NOTHING""", ("rr_h%d" % i, rid, reply))

    for i, (direction, channel, body, when) in enumerate(MESSAGES):
        kv(db, """INSERT INTO message(id,entity_id,direction,channel,body,sent_at)
                  VALUES (?,?,?,?,?,datetime('now',?))
                  ON CONFLICT(id) DO NOTHING""",
           ("ms_h%d" % i, ent, direction, channel, body, when))

    for i, (title, hhmm, body) in enumerate(EVENTS):
        kv(db, """INSERT INTO event(id,entity_id,title,starts_at,body)
                  VALUES (?,?,?,date('now')||' '||?,?)
                  ON CONFLICT(id) DO NOTHING""",
           ("ev_h%d" % i, ent, title, hhmm, body))

    for i, (vapp, ver) in enumerate(APPS):
        kv(db, """INSERT INTO app_install(id,entity_id,vapp,version,source_sha)
                  VALUES (?,?,?,?,?) ON CONFLICT(id) DO NOTHING""",
           ("ai_h%d" % i, ent, vapp, ver,
            hashlib.sha256((vapp + ver).encode()).hexdigest()))

    for wd in range(7):
        kv(db, """INSERT INTO hours(id,entity_id,weekday,opens,closes)
                  VALUES (?,?,?,'11:00','02:00') ON CONFLICT(id) DO NOTHING""",
           ("hr_%d" % wd, ent, wd))




def main():
    ap = argparse.ArgumentParser(
        description="Write invented rows into a database. Development only.")
    ap.add_argument("db", help="path to a migrated node database")
    ap.add_argument("--i-know-this-is-fake", action="store_true", dest="ack",
                    help="required. every row this writes is made up.")
    ap.add_argument("--force", action="store_true",
                    help="seed even though the database already has real rows")
    a = ap.parse_args()
    if not a.ack:
        print(__doc__)
        print("refusing: pass --i-know-this-is-fake", file=sys.stderr)
        return 1
    db = sqlite3.connect(a.db)
    db.execute("PRAGMA foreign_keys=ON")

    # A database that already has rows nobody invented is not a demo database.
    # Mixing the two is how a made-up ticket ends up in somebody's sales total.
    real = {t: db.execute(
                f"SELECT COUNT(*) FROM {t} WHERE id NOT LIKE 'tk\\_%' ESCAPE '\\'"
                ).fetchone()[0] if t == "ticket" else
            db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("observation", "booking", "heartbeat")}
    if any(real.values()) and not a.force:
        print("refusing: this database has rows a real writer produced "
              f"({', '.join(f'{k}={v}' for k, v in real.items() if v)}).",
              file=sys.stderr)
        print("         seeding would mix invented rows into real ones. "
              "--force if you are certain.", file=sys.stderr)
        return 1

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

    seed_floor(db, kv, known)

    db.commit()
    n = lambda t: db.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
    print("devices %d  content %d  drift %d  maps %d  map_run %d  surfaces %d"
          % (n("device"), n("device_content"), n("drift"), n("app_map"),
             n("map_run"), n("surface_state")))
    print("menu_item %d  ticket %d  review %d  message %d  event %d  apps %d"
          % (n("menu_item"), n("ticket"), n("review"), n("message"),
             n("event"), n("app_install")))


if __name__ == "__main__":
    sys.exit(main() or 0)
