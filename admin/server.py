#!/usr/bin/env python3
"""The console you sit in front of on the Tuesday an app vendor ships a redesign.

    python3 admin/server.py node.sqlite --port 8090

Its own module and its own port. It reads the node database and writes only two
things: a drift's state as you work it, and a decision on an action held for
approval. It does not execute anything — that is the executor's job, and this
console is not a way around the gate.
"""
import argparse, json, os, sqlite3, sys, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "ui")
sys.path.insert(0, HERE)

import edit as editmod   # noqa: E402  (needs HERE on the path)


def rows(db, sql, args=()):
    cur = db.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ---------------------------------------------------------------- queries
DENIED = """SELECT 1 FROM ledger l WHERE l.action_id = a.id AND l.stage='DENIED'"""


def q_drift(db):
    """The queue. Ordered by what is costing the most, not by what is newest.

    The impact number comes from the drift_impact view, not from a copy of the
    same SQL living here -- a console that computes its own version of a
    database's number will eventually disagree with it."""
    return rows(db, """
        SELECT id, kind, subject, capability, expected, seen,
               occurrences, state, first_seen_at, last_seen_at,
               businesses_affected AS businesses
          FROM drift_impact
         WHERE state != 'fixed'
         ORDER BY businesses DESC, occurrences DESC, last_seen_at DESC""")


def q_fleet(db):
    return rows(db, """
        SELECT dv.id, dv.label, dv.kind, dv.serial, dv.os_version, dv.channel,
               dv.health, dv.last_seen_at, e.name AS business,
               (SELECT group_concat(kind || ' ' || version, ', ')
                  FROM device_content dc WHERE dc.device_id = dv.id) AS content
          FROM device dv LEFT JOIN entity e ON e.id = dv.entity_id
         ORDER BY CASE dv.health WHEN 'down' THEN 0 WHEN 'degraded' THEN 1
                                 WHEN 'unknown' THEN 2 ELSE 3 END,
                  dv.last_seen_at""")


def q_approvals(db):
    return rows(db, """
        SELECT a.id, a.capability, a.args, a.requested_at, e.name AS business,
               p.display_name AS requested_by
          FROM action a
          LEFT JOIN entity e ON e.id = a.entity_id
          LEFT JOIN person p ON p.id = a.requested_by
         WHERE a.lifecycle = 'AWAITING_APPROVAL'
         ORDER BY a.requested_at""")


def q_actions(db, limit=40):
    return rows(db, f"""
        SELECT a.id, a.capability, a.lifecycle, a.verification,
               a.surfaces_ok, a.surfaces_total, a.requested_at, e.name AS business,
               EXISTS ({DENIED}) AS denied
          FROM action a LEFT JOIN entity e ON e.id = a.entity_id
         ORDER BY a.requested_at DESC LIMIT ?""", (limit,))


def q_inconsistent(db):
    """Only the disagreements. A console that lists everything that is fine is
    a report, not a queue."""
    return rows(db, """
        SELECT c.entity_id, e.name AS business, c.field, c.canonical_value,
               c.surface, c.observed, c.verdict, c.days_stale
          FROM consistency c LEFT JOIN entity e ON e.id = c.entity_id
         WHERE c.verdict IN ('CONTRADICTED','NOT_YET_VERIFIABLE')
         ORDER BY CASE c.verdict WHEN 'CONTRADICTED' THEN 0 ELSE 1 END,
                  c.days_stale DESC""")


def q_businesses(db):
    """The entity graph, in graph order.

    Sorting by parent_id put a child above its own parent and gave a grandchild
    the same indent as its parent -- which is exactly the flattening the entity
    model exists to prevent. Order by the root, then by the materialised path,
    and take the depth from entity_ancestry rather than guessing it from
    whether parent_id is set."""
    return rows(db, """
        WITH RECURSIVE path(id, root, sort, depth) AS (
          SELECT id, id, name, 0 FROM entity WHERE parent_id IS NULL
          UNION ALL
          SELECT e.id, p.root, p.sort || char(31) || e.name, p.depth + 1
            FROM entity e JOIN path p ON e.parent_id = p.id
        )
        SELECT e.id, e.name, e.kind, e.vertical, e.parent_id, p.depth,
               (SELECT COUNT(*) FROM entity c WHERE c.parent_id = e.id) AS children,
               (SELECT COUNT(*) FROM device d WHERE d.entity_id = e.id) AS devices,
               (SELECT COUNT(*) FROM app_install i WHERE i.entity_id = e.id) AS apps
          FROM entity e JOIN path p ON p.id = e.id
         ORDER BY p.root, p.sort""")


def q_content(db):
    return rows(db, """
        SELECT m.app AS subject, m.app_version, m.map_version, m.capability,
               m.executor, m.state,
               (SELECT COUNT(*) FROM map_run r WHERE r.map_id = m.id) AS runs,
               (SELECT COUNT(*) FROM map_run r WHERE r.map_id = m.id
                                            AND r.outcome != 'OK') AS bad
          FROM app_map m ORDER BY m.app, m.map_version DESC""")


def q_editable(db):
    """Everything the editor needs to draw a form, in one shape.

    Deliberately one payload rather than a route per form: the editor is a
    single screen and a second round-trip per panel would mean it can render
    half-populated, which looks like data loss to whoever is typing."""
    ent = rows(db, """SELECT e.id, e.name, e.kind, e.vertical, e.parent_id, e.slug,
                             l.line1, l.line2, l.city, l.region, l.postal
                        FROM entity e LEFT JOIN location l ON l.entity_id = e.id
                       ORDER BY (e.parent_id IS NOT NULL), e.name""")
    return {
        "entities": ent,
        "hours": rows(db, """SELECT entity_id, weekday, opens, closes FROM hours
                              ORDER BY entity_id, weekday"""),
        "sections": rows(db, """SELECT ms.id, ms.name, ms.sort, m.entity_id
                                  FROM menu_section ms JOIN menu m ON m.id=ms.menu_id
                                 ORDER BY m.entity_id, ms.sort"""),
        "items": rows(db, """SELECT mi.id, mi.section_id, mi.name, mi.description,
                                    mi.price_cents, mi.available, m.entity_id
                               FROM menu_item mi
                               JOIN menu_section ms ON ms.id = mi.section_id
                               JOIN menu m ON m.id = ms.menu_id
                              ORDER BY m.entity_id, ms.sort, mi.sort, mi.name"""),
        "devices": rows(db, """SELECT id, entity_id, label, kind, serial,
                                      os_version, channel, health
                                 FROM device ORDER BY label"""),
    }


def q_summary(db):
    """The tiles. A denial is not a failure: the postcondition was not met, but
    nobody tried and nothing broke. Counting the two together would make a day
    of careful refusals look like a day of outages."""
    one = lambda s, a=(): db.execute(s, a).fetchone()[0]
    return {
        # The tile and the Drift tab must be the same number. Anything not
        # marked fixed is still costing somebody, whether or not a human has
        # started on it.
        "drift_unfixed": one("SELECT COUNT(*) FROM drift WHERE state!='fixed'"),
        "drift_open":    one("SELECT COUNT(*) FROM drift WHERE state='open'"),
        "drift_mapping": one("SELECT COUNT(*) FROM drift WHERE state='mapping'"),
        "approvals":    one("SELECT COUNT(*) FROM action WHERE lifecycle='AWAITING_APPROVAL'"),
        "boxes_down":   one("SELECT COUNT(*) FROM device WHERE health IN ('down','degraded')"),
        "boxes":        one("SELECT COUNT(*) FROM device"),
        "contradicted": one("SELECT COUNT(*) FROM consistency WHERE verdict='CONTRADICTED'"),
        "businesses":   one("SELECT COUNT(*) FROM entity WHERE parent_id IS NULL"),
        "failed_today": one(f"""SELECT COUNT(*) FROM action a
                                 WHERE a.verification='FAILED'
                                   AND a.requested_at > datetime('now','-1 day')
                                   AND NOT EXISTS ({DENIED})"""),
        "denied_today": one(f"""SELECT COUNT(*) FROM action a
                                 WHERE a.requested_at > datetime('now','-1 day')
                                   AND EXISTS ({DENIED})"""),
    }


ROUTES = {"drift": q_drift, "fleet": q_fleet, "approvals": q_approvals,
          "editable": q_editable,
          "actions": q_actions, "inconsistent": q_inconsistent,
          "businesses": q_businesses, "content": q_content, "summary": q_summary}


class Handler(BaseHTTPRequestHandler):
    server_version = "anextgent-admin/1.0"
    def log_message(self, *a): pass

    def _json(self, code, body):
        b = json.dumps(body, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        db = self.server.db
        if u.path in ("/", "/index.html"):
            p = os.path.join(UI, "index.html")
            b = open(p, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/all":
            return self._json(200, {k: fn(db) for k, fn in ROUTES.items()})
        name = u.path[len("/api/"):] if u.path.startswith("/api/") else None
        if name in ROUTES:
            return self._json(200, ROUTES[name](db))
        self._json(404, {"error": "no such route"})

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        db = self.server.db
        try:
            if u.path == "/api/drift/state":
                state = body["state"]
                if state not in ("open", "mapping", "fixed"):
                    return self._json(400, {"error": "bad state"})
                db.execute("UPDATE drift SET state=?, fixed_version=? WHERE id=?",
                           (state, body.get("map_version"), body["id"]))
                db.commit()
                return self._json(200, {"ok": True, "id": body["id"], "state": state})

            if u.path == "/api/approval":
                # Approve moves it to PLANNED so the executor may pick it up.
                # Denying finishes it with a verdict, because an action that
                # ended has to say what happened.
                if body["decision"] == "approve":
                    db.execute("""UPDATE action SET lifecycle='PLANNED'
                                  WHERE id=? AND lifecycle='AWAITING_APPROVAL'""",
                               (body["id"],))
                    stage, detail = "APPROVED", {"by": body.get("by")}
                else:
                    db.execute("""UPDATE action SET lifecycle='FINISHED',
                                  verification='FAILED', finished_at=datetime('now')
                                  WHERE id=? AND lifecycle='AWAITING_APPROVAL'""",
                               (body["id"],))
                    stage, detail = "DENIED", {"by": body.get("by"),
                                               "reason": body.get("reason")}
                seq = db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM ledger WHERE action_id=?",
                                 (body["id"],)).fetchone()[0]
                db.execute("""INSERT INTO ledger(id,action_id,seq,stage,executor,detail)
                              VALUES (?,?,?,?,'human',?)""",
                           ("lg_" + uuid.uuid4().hex[:12], body["id"], seq, stage,
                            json.dumps(detail)))
                db.commit()
                return self._json(200, {"ok": True, "id": body["id"], "stage": stage})

            # Everything a person may change by hand lives in edit.py, which
            # bypasses the executor on purpose -- an owner typing their own
            # closing time is not an agent acting for them. Keeping it behind
            # one prefix means the whole bypass is auditable in one place.
            if u.path.startswith("/api/edit/"):
                name = u.path[len("/api/edit/"):]
                fn = editmod.ROUTES.get(name)
                if not fn:
                    return self._json(404, {"error": f"no such editor: {name}"})
                try:
                    return self._json(200, fn(db, body))
                except editmod.Bad as b:
                    return self._json(b.code, {"error": b.msg})
                except sqlite3.IntegrityError as e:
                    return self._json(409, {"error": str(e)})

            self._json(404, {"error": "no such route"})
        except KeyError as e:
            self._json(400, {"error": f"missing {e}"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", help="path to a migrated node database")
    ap.add_argument("--port", type=int, default=8090)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.db = sqlite3.connect(a.db, check_same_thread=False, timeout=15)
    srv.db.execute("PRAGMA foreign_keys=ON")
    print(f"admin on http://127.0.0.1:{a.port}  db={a.db}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
