#!/usr/bin/env python3
"""The write half of the console: what a person is allowed to change by hand.

Kept in its own file because every function here bypasses the executor. That
is correct for these -- an owner typing their own closing time is not an agent
acting on their behalf, and routing it through the gate would mean asking them
to approve their own sentence -- but it is exactly the kind of thing that
should be easy to audit in one place rather than scattered through a server.

Two rules hold for everything in here:

  1. A person's own edit is recorded as an observation with source 'owner',
     not written straight to `canonical`. The resolver then decides, the same
     way it decides everything else. Writing canonical directly would make the
     owner a special case that the audit trail cannot see, and would silently
     lose the edit the next time the resolver ran.

  2. Nothing here can touch a row the system produced about itself -- a
     heartbeat, a ledger entry, an action's verdict, a drift's occurrence
     count. Those are facts about what happened. A console that can edit them
     is a console that can lie about what the box did.
"""
import json, re, sqlite3, uuid

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
KINDS = ("parent", "location", "operation", "unit")
VERTICALS = ("restaurant", "charter", "marina", "trades", "artist")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")


class Bad(Exception):
    def __init__(self, msg, code=400): self.msg, self.code = msg, code


def _id(p): return f"{p}_{uuid.uuid4().hex[:12]}"


def _need(body, *keys):
    out = []
    for k in keys:
        v = body.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            raise Bad(f"missing '{k}'")
        out.append(v.strip() if isinstance(v, str) else v)
    return out if len(out) > 1 else out[0]


def _observe(db, entity_id, field, value, actor=None):
    """A person said so. Record it as an observation like any other source."""
    db.execute("""INSERT INTO observation(id,entity_id,field,value,source,
                                          actor_id,observed_at,confidence)
                  VALUES (?,?,?,?,'owner',?,datetime('now'),1.0)""",
               (_id("ob"), entity_id, field, value, actor))


# ---------------------------------------------------------------- entities
def entity_save(db, body):
    """Create or rename a business, an operation, a unit.

    A parent cannot be its own descendant. Without that check a two-click
    mistake makes `entity_ancestry` recurse forever and takes every screen
    that reads it down with it."""
    eid = body.get("id")
    name = _need(body, "name")
    kind = body.get("kind") or "parent"
    if kind not in KINDS:
        raise Bad(f"kind must be one of {', '.join(KINDS)}")
    vertical = body.get("vertical") or None
    if vertical and vertical not in VERTICALS:
        raise Bad(f"vertical must be one of {', '.join(VERTICALS)}")
    parent = body.get("parent_id") or None
    slug = (body.get("slug") or re.sub(r"[^a-z0-9]+", "-",
                                       name.lower()).strip("-"))[:63]
    if not SLUG.match(slug):
        raise Bad("slug must be lowercase letters, digits and hyphens")

    if parent:
        if not db.execute("SELECT 1 FROM entity WHERE id=?", (parent,)).fetchone():
            raise Bad(f"no such parent: {parent}")
        if eid:
            if parent == eid:
                raise Bad("a business cannot be its own parent")
            loop = db.execute("""SELECT 1 FROM entity_ancestry
                                  WHERE id=? AND ancestor_id=?""",
                              (parent, eid)).fetchone()
            if loop:
                raise Bad(f"{parent} is already below this one — that would "
                          "make a loop")

    if eid:
        if not db.execute("SELECT 1 FROM entity WHERE id=?", (eid,)).fetchone():
            raise Bad(f"no such entity: {eid}", 404)
        db.execute("""UPDATE entity SET name=?, kind=?, vertical=?, parent_id=?
                       WHERE id=?""", (name, kind, vertical, parent, eid))
    else:
        eid = _id("en")
        if db.execute("SELECT 1 FROM entity WHERE slug=?", (slug,)).fetchone():
            slug = f"{slug}-{eid[-4:]}"
        db.execute("""INSERT INTO entity(id,parent_id,slug,name,kind,vertical)
                      VALUES (?,?,?,?,?,?)""",
                   (eid, parent, slug, name, kind, vertical))
    db.commit()
    return {"id": eid, "name": name, "kind": kind, "vertical": vertical,
            "parent_id": parent}


def entity_delete(db, body):
    """Refuses while anything real hangs off it. A cascade here would take the
    ledger with it, and the ledger is the thing you cannot lose."""
    eid = _need(body, "id")
    for table, label in (("entity", "operations under it"),
                         ("device", "boxes"), ("action", "actions"),
                         ("booking", "bookings"), ("ticket", "tickets")):
        col = "parent_id" if table == "entity" else "entity_id"
        n = db.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=?",
                       (eid,)).fetchone()[0]
        if n:
            raise Bad(f"still has {n} {label} — move or remove those first")
    db.execute("DELETE FROM entity WHERE id=?", (eid,))
    db.commit()
    return {"deleted": eid}


def location_save(db, body):
    eid = _need(body, "entity_id")
    f = {k: (body.get(k) or None) for k in
         ("line1", "line2", "city", "region", "postal", "country")}
    f["country"] = f["country"] or "US"
    db.execute("""INSERT INTO location(entity_id,line1,line2,city,region,postal,
                                       country,updated_at)
                  VALUES (?,?,?,?,?,?,?,datetime('now'))
                  ON CONFLICT(entity_id) DO UPDATE SET
                    line1=excluded.line1, line2=excluded.line2,
                    city=excluded.city, region=excluded.region,
                    postal=excluded.postal, country=excluded.country,
                    updated_at=excluded.updated_at""",
               (eid, f["line1"], f["line2"], f["city"], f["region"],
                f["postal"], f["country"]))
    db.commit()
    return {"entity_id": eid, **f}


# ------------------------------------------------------------------- hours
TIME = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


def hours_save(db, body):
    """Set the week. Closing after midnight is normal on this coast, so a
    closing time earlier than the opening time is allowed and means the next
    morning -- it is not a validation error."""
    eid = _need(body, "entity_id")
    days = body.get("days")
    if not isinstance(days, list):
        raise Bad("days must be a list of {weekday, opens, closes}")
    for d in days:
        wd = d.get("weekday")
        if not isinstance(wd, int) or not 0 <= wd <= 6:
            raise Bad("weekday must be 0-6, Monday is 0")
        if d.get("closed"):
            continue
        for k in ("opens", "closes"):
            if not TIME.match(str(d.get(k) or "")):
                raise Bad(f"{WEEKDAYS[wd]} {k}: expected HH:MM, got "
                          f"{d.get(k)!r}")
    db.execute("DELETE FROM hours WHERE entity_id=?", (eid,))
    for d in days:
        if d.get("closed"):
            _observe(db, eid, f"hours.{d['weekday']}", "closed",
                     body.get("actor"))
            continue
        db.execute("""INSERT INTO hours(id,entity_id,weekday,opens,closes)
                      VALUES (?,?,?,?,?)""",
                   (_id("hr"), eid, d["weekday"], d["opens"], d["closes"]))
        # The resolver decides; this is the owner's claim, not the answer.
        _observe(db, eid, f"hours.{d['weekday']}.opens", d["opens"],
                 body.get("actor"))
        _observe(db, eid, f"hours.{d['weekday']}.closes", d["closes"],
                 body.get("actor"))
    db.commit()
    return {"entity_id": eid, "days": len(days)}


# -------------------------------------------------------------------- menu
def menu_item_save(db, body):
    """Add, rename, reprice or 86 an item.

    86ing through here sets availability directly, which is the point: it is
    the one thing a line cook has to be able to do in two seconds on a Friday
    night without anybody approving anything."""
    iid = body.get("id")
    if iid:
        row = db.execute("SELECT id FROM menu_item WHERE id=?", (iid,)).fetchone()
        if not row:
            raise Bad(f"no such item: {iid}", 404)
    price = body.get("price_cents")
    if price is not None:
        try:
            price = int(price)
        except (TypeError, ValueError):
            raise Bad("price_cents must be a whole number of cents")
        if price < 0:
            raise Bad("a price cannot be negative")
    available = 0 if body.get("available") in (0, False, "0", "false") else 1

    if iid:
        db.execute("""UPDATE menu_item
                         SET name=COALESCE(?,name),
                             description=COALESCE(?,description),
                             price_cents=COALESCE(?,price_cents),
                             available=?,
                             eightysixed_at=CASE WHEN ?=0
                                 THEN COALESCE(eightysixed_at, datetime('now'))
                                 ELSE NULL END
                       WHERE id=?""",
                   (body.get("name"), body.get("description"), price,
                    available, available, iid))
    else:
        sid = _need(body, "section_id")
        if not db.execute("SELECT 1 FROM menu_section WHERE id=?",
                          (sid,)).fetchone():
            raise Bad(f"no such menu section: {sid}")
        iid = _id("mi")
        db.execute("""INSERT INTO menu_item(id,section_id,name,description,
                                            price_cents,available)
                      VALUES (?,?,?,?,?,?)""",
                   (iid, sid, _need(body, "name"), body.get("description"),
                    price, available))
    db.commit()
    return {"id": iid, "available": bool(available)}


def menu_section_save(db, body):
    eid = _need(body, "entity_id")
    row = db.execute("SELECT id FROM menu WHERE entity_id=? AND active=1",
                     (eid,)).fetchone()
    if row:
        mid = row[0]
    else:
        mid = _id("mn")
        db.execute("INSERT INTO menu(id,entity_id,name) VALUES (?,?,'All Day')",
                   (mid, eid))
    sid = body.get("id") or _id("ms")
    db.execute("""INSERT INTO menu_section(id,menu_id,name,sort)
                  VALUES (?,?,?,?)
                  ON CONFLICT(id) DO UPDATE SET name=excluded.name""",
               (sid, mid, _need(body, "name"), int(body.get("sort") or 0)))
    db.commit()
    return {"id": sid, "menu_id": mid}


# ------------------------------------------------------------------ boxes
def device_save(db, body):
    """Only what a person legitimately knows: which business a box belongs to,
    what to call it, and which channel it follows.

    Serial, OS version, content versions and health are not editable and never
    will be. Those are written by the box about itself, and a fleet table whose
    rows can be typed tells you what somebody meant to deploy rather than what
    is deployed."""
    did = _need(body, "id")
    if not db.execute("SELECT 1 FROM device WHERE id=?", (did,)).fetchone():
        raise Bad(f"no such box: {did}", 404)
    ch = body.get("channel")
    if ch and ch not in ("stable", "beta", "canary"):
        raise Bad("channel must be stable, beta or canary")
    db.execute("""UPDATE device SET entity_id=COALESCE(?,entity_id),
                                    label=COALESCE(?,label),
                                    channel=COALESCE(?,channel)
                   WHERE id=?""",
               (body.get("entity_id"), body.get("label"), ch, did))
    db.commit()
    return {"id": did}


def device_retire(db, body):
    """A box that is gone. Its heartbeats and content rows go with it; its
    actions and ledger entries do not, because those happened."""
    did = _need(body, "id")
    db.execute("DELETE FROM device WHERE id=?", (did,))
    db.commit()
    return {"retired": did}


ROUTES = {
    "entity":       entity_save,
    "entity/del":   entity_delete,
    "location":     location_save,
    "hours":        hours_save,
    "menu/section": menu_section_save,
    "menu/item":    menu_item_save,
    "device":       device_save,
    "device/del":   device_retire,
}
