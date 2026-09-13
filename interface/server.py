#!/usr/bin/env python3
"""The shell the box boots into.

    python3 interface/server.py node.sqlite --port 8080

Its own module, its own port. It takes a database path and nothing else -- no
import of `node`, no import of `admin`, no shared library. What it renders is
whatever is in that database; there is no number in here that a business would
recognise as its own.

Branding is configuration, not markup: ANEXTGENT_BRAND, ANEXTGENT_TAGLINE and
ANEXTGENT_USER. Change them and every surface changes.
"""
import argparse, json, os, sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")


def contracts_dir():
    """Where the capability definitions live.

    Same convention as the rest of the system: an environment variable first,
    then the installed location on a box, then a sibling checkout. In
    production these are pulled artifacts, not source files -- a path that
    assumes a checkout cannot pull. Missing is not an error here: the screen
    falls back to what the database has seen."""
    for p in (os.environ.get("ANEXTGENT_CONTRACTS"),
              "/usr/lib/anextgent/contracts",
              os.path.join(os.path.dirname(os.path.dirname(
                  os.path.abspath(__file__))), "contracts")):
        if p and os.path.isdir(os.path.join(p, "capabilities")):
            return os.path.join(p, "capabilities")
    return None
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml",
         ".json": "application/json"}


def rows(db, sql, args=()):
    cur = db.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def one(db, sql, args=(), default=0):
    r = db.execute(sql, args).fetchone()
    return default if r is None or r[0] is None else r[0]


def has(db, table):
    return bool(one(db, """SELECT COUNT(*) FROM sqlite_master
                           WHERE type IN ('table','view') AND name=?""", (table,)))


# ------------------------------------------------------------------ pieces
def primary_entity(db):
    """The business this box belongs to. A box is issued to one of them; where
    that is ambiguous, the one with a device attached wins over the one without,
    because the box is physically sitting in somebody's dock office."""
    r = db.execute("""
        SELECT e.id, e.name, e.kind, e.vertical, e.parent_id
          FROM entity e
         ORDER BY (SELECT COUNT(*) FROM device d WHERE d.entity_id = e.id) DESC,
                  (e.parent_id IS NOT NULL), e.name
         LIMIT 1""").fetchone()
    if not r:
        return None
    return dict(zip(("id", "name", "kind", "vertical", "parent_id"), r))


def q_hub(db, ent):
    """The operator's numbers. Each one is a query; none is a constant."""
    if not ent:
        return {}
    eid = ent["id"]
    ids = [eid] + [r[0] for r in db.execute(
        "SELECT id FROM entity_ancestry WHERE ancestor_id=? AND id<>?", (eid, eid))]
    marks = ",".join("?" * len(ids))

    today = one(db, f"""SELECT SUM(total_cents) FROM ticket
                        WHERE entity_id IN ({marks}) AND closed_at IS NOT NULL
                          AND date(closed_at) = date('now')""", ids)
    yday = one(db, f"""SELECT SUM(total_cents) FROM ticket
                       WHERE entity_id IN ({marks}) AND closed_at IS NOT NULL
                         AND date(closed_at) = date('now','-1 day')""", ids)
    delta = None if not yday else round((today - yday) * 100.0 / yday)

    # "To reply" means a review with no reply row, not every review.
    open_reviews = one(db, f"""SELECT COUNT(*) FROM review r
          WHERE r.entity_id IN ({marks})
            AND NOT EXISTS (SELECT 1 FROM review_reply x WHERE x.review_id = r.id)""",
                      ids)
    new_reviews = one(db, f"""SELECT COUNT(*) FROM review
          WHERE entity_id IN ({marks})
            AND created_at > datetime('now','-7 days')""", ids)
    eightysixed = one(db, f"""SELECT COUNT(*) FROM menu_item mi
          JOIN menu_section ms ON ms.id = mi.section_id
          JOIN menu m ON m.id = ms.menu_id
         WHERE m.entity_id IN ({marks}) AND mi.available = 0""", ids)
    agenda = rows(db, f"""SELECT title, starts_at, body FROM event
         WHERE entity_id IN ({marks}) AND date(starts_at) = date('now')
         ORDER BY starts_at""", ids)

    # "Restaurant · Orange Beach, AL" -- what it is and where it is. Both are
    # rows; neither is typed into the template.
    loc = db.execute("SELECT city, region FROM location WHERE entity_id=?",
                     (eid,)).fetchone()
    where = ", ".join(x for x in [
        (ent.get("vertical") or ent["kind"] or "").title() or None,
        ", ".join(p for p in (loc or ()) if p) or None] if x).replace(", ", " · ", 1)
    return {
        "name": ent["name"], "vertical": ent.get("vertical") or "business",
        "meta": where, "sales_today": today, "sales_delta": delta,
        "reviews_open": open_reviews, "reviews_new": new_reviews,
        "eightysixed": eightysixed, "events": len(agenda), "agenda": agenda,
        "quick": [
            {"label": "Reply to Reviews", "sub": f"{open_reviews} waiting", "icon": "chat"},
            {"label": "Update Hours", "sub": "Holiday hours, special events", "icon": "clock"},
            {"label": "Post an Update", "sub": "Share news or a special", "icon": "mega"},
            {"label": "Export Sales", "sub": "Reports from the POS", "icon": "down"},
            {"label": "View Orders", "sub": "See recent tickets", "icon": "doc"},
            {"label": "Customer Messages", "sub": "Unread first", "icon": "chat"},
        ],
    }


# The integration registry: how a package id becomes something an owner
# recognises. Data, so adding a vendor is a row rather than a patch -- and so
# nothing downstream has to parse a reverse-DNS name into a display name.
#
# key -> (display name, what it does, glyph, tile colour)
VENDORS = {
    "com.toasttab.pos":          ("Toast", "POS & online orders", "doc", "--t-red"),
    "com.fareharbor.dashboard":  ("FareHarbor", "Bookings & manifests", "cal", "--t-blue"),
    "com.google.android.apps.business":
                                 ("Google Business", "Reviews, posts & profile", "tag", "--t-blue"),
    "fareharbor":                ("FareHarbor", "Bookings & manifests", "cal", "--t-blue"),
    "peek":                      ("Peek", "Bookings", "cal", "--t-violet"),
    "toast":                     ("Toast", "POS & online orders", "doc", "--t-red"),
    "google":                    ("Google Business", "Reviews, posts & profile", "tag", "--t-blue"),
    "facebook":                  ("Facebook", "Social & messages", "chat", "--t-indigo"),
    "instagram":                 ("Instagram", "Social", "image", "--t-pink"),
    "airbnb":                    ("Airbnb", "Stays", "home", "--t-pink"),
    "mailchimp":                 ("Mailchimp", "Email marketing", "mail", "--t-amber"),
    "io.anextgent.menu":         ("Menu", "Your menu, everywhere", "doc", "--t-orange"),
    "io.anextgent.reviews":      ("Reviews", "Read and reply", "star", "--t-amber"),
    "io.anextgent.hours":        ("Hours", "One set of hours, all surfaces", "clock", "--t-teal"),
    "io.anextgent.messages":     ("Messages", "Customer messages", "chat", "--t-slate"),
    "io.anextgent.availability": ("Availability", "What is bookable", "cal", "--t-green"),
}


def vendor(key):
    """Name, description, glyph and colour for a package id or channel.

    The fallback is deliberate: an unknown integration shows the most
    meaningful segment of its id rather than a reverse-DNS string with the
    first letter capitalised. Nobody calls Toast 'Com.Toasttab.Pos'."""
    if key in VENDORS:
        n, d, g, c = VENDORS[key]
        return n, d, g, f"var({c})"
    parts = [p for p in str(key).split(".") if p]
    generic = {"com", "io", "net", "org", "app", "dashboard", "pos", "www"}
    named = [p for p in parts if p not in generic] or parts
    leaf = max(named, key=len)
    return leaf.title(), key, "grid", "var(--t-slate)"


def q_apps(db, ent):
    """Installed apps plus the vendors this business actually exchanges data
    with. A vendor the box has never seen a message from is not listed as
    connected, because that word has to mean something."""
    out = []
    if ent:
        for r in rows(db, """SELECT vapp, version FROM app_install
                             WHERE entity_id=? ORDER BY vapp""", (ent["id"],)):
            n, d, g, c = vendor(r["vapp"])
            out.append({"name": n, "desc": d, "icon": g, "color": c,
                        "id": r["vapp"], "first_party": True,
                        "status": "v" + r["version"], "state": "connected"})
    seen = {}
    if has(db, "map_run"):
        for r in rows(db, """SELECT m.app AS name, MAX(r.at) AS at,
                                    SUM(r.outcome!='OK') AS bad, COUNT(*) AS n
                               FROM app_map m LEFT JOIN map_run r ON r.map_id=m.id
                              GROUP BY m.app"""):
            seen[r["name"]] = r
    for r in rows(db, """SELECT channel AS name, COUNT(*) AS n, MAX(booked_at) AS at
                           FROM booking WHERE channel IS NOT NULL
                          GROUP BY channel"""):
        seen.setdefault(r["name"], r)
    # One vendor, one card. FareHarbor arrives here twice -- once as the app
    # map's package id and once as a booking channel -- and listing it twice
    # let the same integration show "Connected" beside "Needs re-mapping".
    # Collapse on the resolved name and let any drift on any of its ids win,
    # because a broken half is a broken integration.
    merged = {}
    for key in sorted(seen):
        n, d, g, c = vendor(key)
        e = merged.setdefault(n, {"name": n, "desc": d, "icon": g, "color": c,
                                  "ids": [], "first_party": False, "drift": 0})
        e["ids"].append(key)
        e["drift"] += one(db, """SELECT COUNT(*) FROM drift
                                  WHERE subject=? AND state!='fixed'""", (key,))
    for e in merged.values():
        e["id"] = ", ".join(e.pop("ids"))
        drifted = e.pop("drift")
        e["status"] = "Needs re-mapping" if drifted else "Connected"
        e["state"] = "approval" if drifted else "connected"
        out.append(e)
    return out


def q_attention(db, ent):
    """What actually needs a person. Drift first: it is the only thing here
    that is costing every business at once."""
    out = []
    for r in rows(db, """SELECT subject, capability, occurrences FROM drift
                          WHERE state!='fixed' ORDER BY occurrences DESC"""):
        out.append({"name": vendor(r["subject"])[0],
                    "desc": (r["capability"] or "extraction") + " refused to guess",
                    "icon": "drift", "color": "var(--t-amber)",
                    "status": f"{r['occurrences']} hits", "state": "approval"})
    n = one(db, "SELECT COUNT(*) FROM action WHERE lifecycle='AWAITING_APPROVAL'")
    if n:
        out.append({"name": "Approvals", "desc": "Held until a person decides",
                    "icon": "alert", "color": "var(--t-orange)",
                    "status": f"{n} waiting", "state": "approval"})
    if ent:
        r = one(db, """SELECT COUNT(*) FROM review r WHERE r.entity_id=?
                        AND NOT EXISTS (SELECT 1 FROM review_reply x
                                        WHERE x.review_id=r.id)""", (ent["id"],))
        if r:
            out.append({"name": "Reviews", "desc": "No reply posted yet",
                        "icon": "star", "color": "var(--t-amber)",
                        "status": f"{r} to answer", "state": "approval"})
        m = one(db, """SELECT COUNT(*) FROM message WHERE entity_id=?
                        AND direction='in'""", (ent["id"],))
        if m:
            out.append({"name": "Messages", "desc": "Customers waiting on a reply",
                        "icon": "chat", "color": "var(--t-slate)",
                        "status": f"{m} unread", "state": "waiting"})
    for r in rows(db, """SELECT label, health, last_seen_at FROM device
                          WHERE health IN ('down','degraded')
                          ORDER BY health"""):
        out.append({"name": r["label"] or "Box", "desc": "Has not reported in",
                    "icon": "screen",
                    "color": "var(--t-red)" if r["health"] == "down" else "var(--t-amber)",
                    "status": r["health"], "state": "down"})
    return out


def q_activity(db, ent):
    """What happened in the business, in the owner's language.

    Deliberately no capability rows here. "review.reply -- AWAITING_APPROVAL"
    is the system describing itself; an owner opening the Hub wants to know a
    guest left five stars and a ticket closed for $42.18. The system's own
    stream is q_sysactivity, and it lives on the Automations screen where it
    belongs. Same ledger, two readings, neither pretending to be the other."""
    out = []
    if not ent:
        return out
    eid = ent["id"]
    for r in rows(db, """SELECT rating, body, source, created_at FROM review
                          WHERE entity_id=? ORDER BY created_at DESC LIMIT 5""",
                  (eid,)):
        out.append({"title": f"New review on {(r['source'] or '').title()}",
                    "stars": r["rating"], "detail": '"' + (r["body"] or "") + '"',
                    "icon": "star", "color": "var(--t-amber)",
                    "at": r["created_at"], "action": "Reply"})
    for r in rows(db, """SELECT id, total_cents, closed_at FROM ticket
                          WHERE entity_id=? AND closed_at IS NOT NULL
                          ORDER BY closed_at DESC LIMIT 4""", (eid,)):
        n = one(db, "SELECT COUNT(*) FROM ticket_line WHERE ticket_id=?", (r["id"],))
        out.append({"title": "Ticket closed",
                    "detail": f"{r['id']} · ${(r['total_cents'] or 0)/100:.2f}"
                              + (f" · {n} items" if n else ""),
                    "icon": "doc", "color": "var(--t-red)", "at": r["closed_at"]})
    for r in rows(db, """SELECT body, sent_at FROM message
                          WHERE entity_id=? AND direction='in'
                          ORDER BY sent_at DESC LIMIT 3""", (eid,)):
        out.append({"title": "New customer message",
                    "detail": '"' + (r["body"] or "") + '"', "icon": "chat",
                    "color": "var(--t-slate)", "at": r["sent_at"],
                    "action": "Reply"})
    for r in rows(db, """SELECT mi.name, mi.eightysixed_at FROM menu_item mi
                    JOIN menu_section ms ON ms.id = mi.section_id
                    JOIN menu m ON m.id = ms.menu_id
                   WHERE m.entity_id=? AND mi.available=0
                   ORDER BY mi.eightysixed_at DESC LIMIT 3""", (eid,)):
        out.append({"title": r["name"], "detail": "Taken off the menu",
                    "icon": "box", "color": "var(--t-orange)",
                    "at": r["eightysixed_at"], "chip": "86'd", "chipkind": "bad"})
    out.sort(key=lambda x: x.get("at") or "", reverse=True)
    return out[:6]


def q_sysactivity(db):
    """The system's own stream: what was requested, and what the verdict was.
    FINISHED alone says nothing, so the verdict rides along with it."""
    out = []
    for r in rows(db, """SELECT a.id, a.capability, a.lifecycle, a.verification,
                                a.requested_at, e.name AS business,
                                EXISTS(SELECT 1 FROM ledger l
                                       WHERE l.action_id=a.id AND l.stage='DENIED')
                                  AS denied
                           FROM action a LEFT JOIN entity e ON e.id=a.entity_id
                          ORDER BY a.requested_at DESC LIMIT 10"""):
        if r["denied"]:
            chip, kind = "you said no", ""
        else:
            chip, kind = {"VERIFIED": ("verified", "ok"),
                          "FAILED": ("failed", "bad"),
                          "PARTIALLY_VERIFIED": ("partly verified", "warn")}.get(
                r["verification"],
                (r["lifecycle"].lower().replace("_", " "),
                 "warn" if r["lifecycle"] == "AWAITING_APPROVAL" else ""))
        out.append({"title": r["capability"], "detail": r["business"] or "",
                    "icon": "route", "color": "var(--t-indigo)",
                    "at": r["requested_at"], "chip": chip, "chipkind": kind})
    return out


def q_automations(db):
    """An automation is a promoted map: learned work that now runs without a
    person. A candidate is not one -- it has never been trusted with a
    customer."""
    out = []
    for r in rows(db, """SELECT m.app, m.capability, m.state, m.map_version,
                                (SELECT COUNT(*) FROM map_run x WHERE x.map_id=m.id)
                                  AS runs,
                                (SELECT COUNT(*) FROM map_run x WHERE x.map_id=m.id
                                   AND x.outcome!='OK') AS bad,
                                (SELECT MAX(x.at) FROM map_run x WHERE x.map_id=m.id)
                                  AS last
                           FROM app_map m ORDER BY m.state DESC, m.app"""):
        bad, promoted = r["bad"], r["state"] == "promoted"
        out.append({
            "name": r["capability"], "desc": r["app"],
            "icon": "route", "color": "var(--t-indigo)" if promoted else "var(--t-slate)",
            "status": "Needs re-mapping" if bad else
                      ("Active" if promoted else r["state"].title()),
            "state": "approval" if bad else ("running" if promoted else "waiting")})
    return out


def q_agents(db):
    """What this box knows how to want.

    An agent is a capability -- a postcondition plus who is allowed to reach
    it. An automation is a promoted map that reaches one without asking. They
    were the same list on this screen, which made "2 agents available" mean
    "2 maps exist" and hid every capability nothing had learned to do yet.

    The status is the honest three-way answer: it runs on its own, it runs but
    asks you first, or nothing on this box can do it yet."""
    d = contracts_dir()
    caps = {}
    if d:
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    c = json.load(fh)
            except (OSError, ValueError):
                continue
            caps[c.get("name", f[:-5])] = c
    for r in db.execute("SELECT DISTINCT capability FROM action"):
        caps.setdefault(r[0], {"name": r[0]})
    for r in db.execute("SELECT DISTINCT capability FROM app_map"):
        caps.setdefault(r[0], {"name": r[0]})

    GL = {"review": "star", "menu": "doc", "business": "tag",
          "availability": "cal", "customer": "people"}
    out = []
    for name, c in sorted(caps.items()):
        promoted = one(db, """SELECT COUNT(*) FROM app_map
                               WHERE capability=? AND state='promoted'""", (name,))
        asks = c.get("approval") in ("required", "strong")
        mode = c.get("mode", "write")
        drifted = one(db, """SELECT COUNT(*) FROM drift
                              WHERE capability=? AND state!='fixed'""", (name,))
        if drifted:
            status, state = "Paused -- being re-mapped", "approval"
        elif promoted and not asks:
            status, state = "Runs on its own", "running"
        elif promoted:
            status, state = "Runs, asks you first", "approval"
        elif asks:
            status, state = "Asks you first", "waiting"
        else:
            status, state = "No map yet", "waiting"
        out.append({
            "name": c.get("title") or name, "desc": name,
            "icon": GL.get(name.split(".")[0], "bot"),
            "color": "var(--t-violet)" if mode == "write" else "var(--t-teal)",
            "status": status, "state": state})
    return out


def q_content(db):
    """What this box is running, and how old it is. The version is a fact about
    a device, not a claim about a repository."""
    out = []
    for r in rows(db, """SELECT dc.kind, dc.version, dc.applied_at, d.label
                           FROM device_content dc JOIN device d ON d.id=dc.device_id
                          ORDER BY d.label, dc.kind"""):
        out.append({"kind": r["kind"], "version": r["version"],
                    "detail": (r["label"] or "this box")})
    return out


def payload(db):
    ent = primary_entity(db)
    brand = os.environ.get("ANEXTGENT_BRAND", "GHOST")
    return {
        "meta": {
            "brand": brand,
            "user": os.environ.get("ANEXTGENT_USER", "Operator"),
            "tagline": os.environ.get("ANEXTGENT_TAGLINE",
                                      "Your AI business partner."),
            "online": True,
        },
        "home": {
            "greeting": greeting(os.environ.get("ANEXTGENT_USER", "there")),
            "events_today": one(db, """SELECT COUNT(*) FROM event
                                        WHERE date(starts_at)=date('now')"""),
            "tasks_due": one(db, """SELECT COUNT(*) FROM action
                                     WHERE lifecycle='AWAITING_APPROVAL'""")
                         + one(db, "SELECT COUNT(*) FROM drift WHERE state!='fixed'"),
            "unread": one(db, "SELECT COUNT(*) FROM message WHERE direction='in'"),
            "automations_active": one(db, """SELECT COUNT(*) FROM app_map
                                              WHERE state='promoted'"""),
        },
        "entities": rows(db, """SELECT e.id, e.name, e.kind, e.vertical,
                TRIM(COALESCE(UPPER(SUBSTR(e.vertical,1,1))||SUBSTR(e.vertical,2),
                              UPPER(SUBSTR(e.kind,1,1))||SUBSTR(e.kind,2))
                     || COALESCE(' · '||l.city||', '||l.region,'')) AS where_,
                (SELECT COUNT(*) FROM device d WHERE d.entity_id=e.id) AS devices
                FROM entity e LEFT JOIN location l ON l.entity_id = e.id
                ORDER BY (e.parent_id IS NOT NULL), e.name"""),
        "hub": q_hub(db, ent),
        "apps": q_apps(db, ent),
        "appgroups": appgroups(db, ent),
        "attention": q_attention(db, ent),
        "activity": q_activity(db, ent),
        "sysactivity": q_sysactivity(db),
        "automations": q_automations(db),
        "approvals": rows(db, """SELECT a.id, a.capability, a.args, a.requested_at,
                                        e.name AS business
                                   FROM action a LEFT JOIN entity e ON e.id=a.entity_id
                                  WHERE a.lifecycle='AWAITING_APPROVAL'
                                  ORDER BY a.requested_at"""),
        "content": q_content(db),
        "agentpage": {
            "available": len(q_agents(db)),
            "running": one(db, "SELECT COUNT(*) FROM app_map WHERE state='promoted'"),
            "done_today": one(db, """SELECT COUNT(*) FROM action
                                      WHERE lifecycle='FINISHED'
                                        AND date(requested_at)=date('now')"""),
            "agents": q_agents(db),
        },
        "hubsections": hubsections(db, ent),
    }


def greeting(user):
    import datetime
    h = datetime.datetime.now().hour
    part = "morning" if h < 12 else "afternoon" if h < 18 else "evening"
    return f"Good {part}, {user.split()[0]}."


def appgroups(db, ent):
    apps = q_apps(db, ent)
    installed = [a for a in apps if a.get("first_party")]
    connected = [a for a in apps if not a.get("first_party")]
    groups = []
    if installed:
        groups.append({"title": "Installed on this box", "more": "Manage",
                       "items": installed})
    if connected:
        groups.append({"title": "Connected", "more": "Add an integration",
                       "items": connected})
    return groups


def hubsections(db, ent):
    """Each sidebar section is a real query against this business's rows."""
    if not ent:
        return {}
    eid = ent["id"]
    out = {}
    out["sales"] = [{
        "t": r["id"], "q": f"{r['lines']} items",
        "when": (r["closed_at"] or "")[11:16],
        "chip": f"${(r['total_cents'] or 0)/100:.2f}", "icon": "doc",
        "color": "var(--t-red)"}
        for r in rows(db, """SELECT t.id, t.total_cents, t.closed_at,
                 (SELECT COUNT(*) FROM ticket_line l WHERE l.ticket_id=t.id) AS lines
                 FROM ticket t WHERE t.entity_id=? AND t.closed_at IS NOT NULL
                 ORDER BY t.closed_at DESC LIMIT 25""", (eid,))]
    out["reviews"] = [{
        "t": "★" * (r["rating"] or 0) + f"  {(r['source'] or '').title()}",
        "q": r["body"], "when": (r["created_at"] or "")[:10],
        "chip": "replied" if r["replied"] else "needs a reply",
        "chipkind": "ok" if r["replied"] else "warn",
        "icon": "star", "color": "var(--t-amber)"}
        for r in rows(db, """SELECT r.*, EXISTS(SELECT 1 FROM review_reply x
                 WHERE x.review_id=r.id) AS replied FROM review r
                 WHERE r.entity_id=? ORDER BY r.created_at DESC""", (eid,))]
    out["inventory"] = [{
        "t": r["name"], "q": r["section"],
        "chip": "86'd" if not r["available"] else f"${(r['price_cents'] or 0)/100:.2f}",
        "chipkind": "bad" if not r["available"] else "",
        "icon": "box", "color": "var(--t-orange)"}
        for r in rows(db, """SELECT mi.name, mi.price_cents, mi.available,
                 ms.name AS section FROM menu_item mi
                 JOIN menu_section ms ON ms.id=mi.section_id
                 JOIN menu m ON m.id=ms.menu_id WHERE m.entity_id=?
                 ORDER BY mi.available, ms.sort, mi.sort""", (eid,))]
    out["customers"] = [{
        "t": r["display_name"] or "Guest", "q": r["detail"] or "",
        "when": (r["at"] or "")[:10], "icon": "people", "color": "var(--t-teal)"}
        for r in rows(db, """SELECT p.display_name,
                 (SELECT c.value FROM person_contact c WHERE c.person_id=p.id
                  LIMIT 1) AS detail, p.created_at AS at
                 FROM person p ORDER BY p.created_at DESC LIMIT 25""")]
    out["marketing"] = [{
        "t": r["body"], "q": r["channel"] + " · " + r["direction"],
        "when": (r["sent_at"] or "")[:16], "icon": "mega", "color": "var(--t-violet)"}
        for r in rows(db, """SELECT * FROM message WHERE entity_id=?
                 ORDER BY sent_at DESC LIMIT 25""", (eid,))]
    out["team"] = [{
        "t": r["label"] or r["id"], "q": (r["business"] or "") + " · " + r["channel"],
        "chip": r["health"], "chipkind": {"ok": "ok", "degraded": "warn"}.get(
            r["health"], "bad"), "icon": "screen", "color": "var(--t-blue)"}
        for r in rows(db, """SELECT d.*, e.name AS business FROM device d
                 LEFT JOIN entity e ON e.id=d.entity_id ORDER BY d.label""")]
    out["settings"] = [
        {"t": "Constitution", "q": "What this box may do without asking",
         "icon": "doc", "color": "var(--t-slate)",
         "chip": str(one(db, "SELECT COUNT(*) FROM constitution_rule")) + " rules"},
        {"t": "Content", "q": "Maps and contracts this box is running",
         "icon": "folder", "color": "var(--t-slate)",
         "chip": str(one(db, "SELECT COUNT(*) FROM app_map")) + " maps"},
        {"t": "Boxes", "q": "Devices enrolled to this business",
         "icon": "screen", "color": "var(--t-slate)",
         "chip": str(one(db, "SELECT COUNT(*) FROM device")) + " enrolled"},
    ]
    return out


# ------------------------------------------------------------------ server
class Handler(BaseHTTPRequestHandler):
    server_version = "anextgent-shell/1.0"
    def log_message(self, *a): pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/home":
            try:
                return self._send(200, json.dumps(payload(self.server.db),
                                                  default=str).encode(),
                                  "application/json")
            except sqlite3.Error as e:
                return self._send(500, json.dumps({"error": str(e)}).encode(),
                                  "application/json")
        name = "index.html" if path == "/" else path.lstrip("/")
        # Serve only out of ui/. A shell that can be talked into reading /etc
        # is a shell with a file browser nobody asked for.
        full = os.path.normpath(os.path.join(UI, name))
        if not full.startswith(UI + os.sep) or not os.path.isfile(full):
            return self._send(404, b"not found", "text/plain")
        ext = os.path.splitext(full)[1]
        self._send(200, open(full, "rb").read(),
                   TYPES.get(ext, "application/octet-stream"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", help="path to a migrated node database")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.db = sqlite3.connect(a.db, check_same_thread=False, timeout=15)
    print(f"shell on http://{a.host}:{a.port}  db={a.db}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
