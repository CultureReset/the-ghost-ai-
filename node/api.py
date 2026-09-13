#!/usr/bin/env python3
"""The node API. Capabilities in, evidence out. Standard library only.

    python3 node/api.py --db node.sqlite --port 8080

Every request follows the same five steps, and there is no path around them:

    1  someone asks          capability name + arguments
    2  the gate              who is this, may they, how risky, does a person
                             have to say yes first
    3  something does it     an executor, chosen by the router
    4  something else        reads it back on a different path than it wrote
       proves it
    5  it gets written down  append-only, both dimensions of state

Reads skip 3 and 4 because there is nothing to prove. Writes never do.
"""
import argparse, json, os, sqlite3, sys, uuid, hashlib, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

def contracts_dir():
    """Where the capability registry lives.

    Configured, never assumed. On a box the contracts arrive as a signed bundle
    under /usr/lib/anextgent; in a checkout they sit beside this module. Either
    way node does not require contracts to be its sibling, which is what lets
    the two be separate repositories.
    """
    for c in (os.environ.get("ANEXTGENT_CONTRACTS"),
              "/usr/lib/anextgent/contracts",
              os.path.join(os.path.dirname(os.path.dirname(
                  os.path.abspath(__file__))), "contracts")):
        if c and os.path.isdir(os.path.join(c, "capabilities")):
            return c
    raise SystemExit(
        "no capability registry found. Set ANEXTGENT_CONTRACTS to the "
        "contracts directory, or install a bundle at /usr/lib/anextgent/contracts.")


def load_capabilities():
    caps, d = {}, os.path.join(contracts_dir(), "capabilities")
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            c = json.load(open(os.path.join(d, f), encoding="utf-8"))
            caps[c["name"]] = c
    return caps


CAPS = load_capabilities()
CONTRACTS = contracts_dir()


class Denied(Exception):
    def __init__(self, code, msg): self.code, self.msg = code, msg


# ---------------------------------------------------------------- the gate
def gate(db, cap, entity_id, actor_id, install_id=None):
    """Step 2. Runs before any side effect, for every caller without exception —
    a first-party app goes through the same door as a third-party one."""
    if not db.execute("SELECT 1 FROM entity WHERE id=?", (entity_id,)).fetchone():
        raise Denied(404, f"no such entity: {entity_id}")

    # An action is attributed to a person. An unattributable write would leave a
    # ledger entry nobody can be asked about.
    if actor_id and not db.execute("SELECT 1 FROM person WHERE id=?",
                                   (actor_id,)).fetchone():
        raise Denied(404, f"no such actor: {actor_id}")
    if cap.get("mode", "write") == "write" and not actor_id:
        raise Denied(400, "a write needs an actor")

    if install_id:
        g = db.execute("""SELECT mode, risk FROM grant_scope
                          WHERE install_id=? AND capability=?""",
                       (install_id, cap["name"])).fetchone()
        if not g:
            raise Denied(403, f"install {install_id} was never granted {cap['name']}")
        if cap.get("mode", "write") == "write" and g[0] != "write":
            raise Denied(403, f"install {install_id} holds read only on {cap['name']}")

    return decide(db, cap, entity_id)


def decide(db, cap, entity_id):
    """What the business's own constitution says about this capability.

    Most specific wins: a rule naming the capability beats one naming the risk
    tier, and the business's own constitution beats the platform default. The
    capability's declared `approval` is a floor — a business may tighten it,
    never loosen it below what the capability itself demands.
    """
    row = db.execute("""
        SELECT decision FROM authority
         WHERE (entity_id = ? OR entity_id IS NULL)
           AND (capability = ? OR (capability IS NULL AND risk = ?))
         ORDER BY (entity_id IS NULL), specificity
         LIMIT 1""",
        (entity_id, cap["name"], cap.get("risk"))).fetchone()
    decision = row[0] if row else "hold"      # no rule means ask a person

    if decision == "deny":
        raise Denied(403, f"the constitution denies {cap['name']}")

    if cap.get("approval") == "strong" and decision != "hold":
        return "hold"
    return decision


# ---------------------------------------------------------------- reads
SOURCES = {          # whitelist. Nothing outside this is reachable by a read.
    "availability": {"charter_trip"},
    "consistency":  set(),
    "item_rating":  set(),
    "fillable":     {"person"},
}
IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def do_read(db, cap, entity_id, args):
    """Serve the projection the capability declares.

    No branch per capability. Sources, columns and joins are resolved against
    the whitelist above; every value arrives as a bound parameter, so nothing
    a caller sends can reach the SQL text.
    """
    spec = cap.get("read")
    if not spec:
        raise Denied(501, f"{cap['name']} declares no read projection")

    src = spec["source"]
    if src not in SOURCES:
        raise Denied(500, f"source '{src}' is not a permitted read source")

    join, cols, params = spec.get("join"), [], []
    for c in spec["select"]:
        if not IDENT.match(c):
            raise Denied(500, f"bad column '{c}'")
        if join and c == join["as"]:
            cols.append(f'j.{join["column"]} AS {c}')
        else:
            cols.append(f"s.{c}")

    sql = f'SELECT {", ".join(cols)} FROM {src} s'
    if join:
        if join["table"] not in SOURCES[src]:
            raise Denied(500, f"join to '{join['table']}' is not permitted from {src}")
        sql += f' LEFT JOIN {join["table"]} j ON j.id = s.{join["on"]}'

    where = []
    for col, rule in (spec.get("filter") or {}).items():
        if not IDENT.match(col):
            raise Denied(500, f"bad filter column '{col}'")
        if isinstance(rule, dict) and "prefix" in rule:
            v = _bind(rule["prefix"], entity_id, args)
            if v is None:
                continue
            where.append(f"s.{col} LIKE ?"); params.append(f"{v}%")
        else:
            v = _bind(rule, entity_id, args)
            if v is None:
                continue
            where.append(f"s.{col} = ?"); params.append(v)
    if where:
        sql += " WHERE " + " AND ".join(where)
    if spec.get("order"):
        if not IDENT.match(spec["order"]):
            raise Denied(500, "bad order column")
        sql += f' ORDER BY s.{spec["order"]}'

    rows = db.execute(sql, params).fetchall()
    return [dict(zip(spec["select"], r)) for r in rows]


def _bind(token, entity_id, args):
    if not isinstance(token, str) or not token.startswith("$"):
        return token
    name = token[1:]
    return entity_id if name == "entity" else args.get(name)


# ---------------------------------------------------------------- writes
def do_write(db, cap, entity_id, args, actor_id, decision):
    """Creates the action, records the plan, and stops at the gate when a person
    has to say yes. Execution is the executor's job, not the API's — this is the
    contract it satisfies."""
    key = hashlib.sha256(json.dumps(
        {"c": cap["name"], "e": entity_id, "a": args}, sort_keys=True).encode()).hexdigest()[:32]

    prior = db.execute("""SELECT id, lifecycle, verification FROM action
                          WHERE idempotency_key=?""", (key,)).fetchone()
    if prior:
        return {"action_id": prior[0], "lifecycle": prior[1],
                "verification": prior[2], "idempotent_replay": True}

    aid = "ac_" + uuid.uuid4().hex[:12]
    lifecycle = "AWAITING_APPROVAL" if decision == "hold" else "PLANNED"
    db.execute("""INSERT INTO action
        (id, entity_id, capability, args, idempotency_key, requested_by, lifecycle,
         surfaces_total)
        VALUES (?,?,?,?,?,?,?,?)""",
        (aid, entity_id, cap["name"], json.dumps(args, sort_keys=True), key,
         actor_id, lifecycle, len(cap["postcondition"]["surfaces"])))
    _ledger(db, aid, 1, "REQUESTED", None, {"args": args, "actor": actor_id})
    _ledger(db, aid, 2, "PLANNED", None,
            {"executors": cap["executors"], "verify_by": cap["verify"]["by"],
             "settle_seconds": cap["verify"]["settle_seconds"],
             "on_partial": cap.get("on_partial")})
    if decision == "hold":
        _ledger(db, aid, 3, "AWAITING_APPROVAL", "human",
                {"reason": f"risk={cap.get('risk')} approval={cap.get('approval')}"})
    db.commit()
    return {"action_id": aid, "lifecycle": lifecycle,
            "surfaces": cap["postcondition"]["surfaces"],
            "verify_by": cap["verify"]["by"],
            "awaiting_approval": decision == "hold"}


def _ledger(db, action_id, seq, stage, executor, detail):
    db.execute("""INSERT INTO ledger(id, action_id, seq, stage, executor, detail)
                  VALUES (?,?,?,?,?,?)""",
               ("lg_" + uuid.uuid4().hex[:12], action_id, seq, stage, executor,
                json.dumps(detail, sort_keys=True)))


# ---------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    server_version = "anextgent-node/1.0"

    def _send(self, code, body):
        b = json.dumps(body, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a): pass

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        db = self.server.db
        try:
            if u.path == "/healthz":
                db.execute("SELECT 1 FROM entity LIMIT 1").fetchone()
                return self._send(200, {"ok": True, "capabilities": len(CAPS)})

            if u.path == "/capabilities":
                return self._send(200, [{
                    "name": c["name"], "mode": c.get("mode", "write"),
                    "risk": c["risk"], "approval": c.get("approval", "notify"),
                    "surfaces": c["postcondition"]["surfaces"]} for c in CAPS.values()])

            if u.path == "/consistency":
                e = q.get("entity") or self._need("entity")
                rows = db.execute("""SELECT field, canonical_value, surface, observed,
                                            verdict, days_stale FROM consistency
                                     WHERE entity_id=? ORDER BY field, surface""",
                                  (e,)).fetchall()
                return self._send(200, [dict(zip(
                    ("field", "canonical", "surface", "observed", "verdict",
                     "days_stale"), r)) for r in rows])

            if u.path == "/fillable":
                e = q.get("entity") or self._need("entity")
                rows = db.execute("""SELECT f.starts_at, f.open_seats, p.display_name,
                                            pc.value, f.wants
                                     FROM fillable f
                                     JOIN person p ON p.id=f.person_id
                                     LEFT JOIN person_contact pc
                                       ON pc.person_id=p.id AND pc.channel='sms'
                                     WHERE f.entity_id=?""", (e,)).fetchall()
                return self._send(200, [dict(zip(
                    ("starts_at", "open_seats", "name", "sms", "wants"), r))
                    for r in rows])

            if u.path.startswith("/action/"):
                aid = u.path.rsplit("/", 1)[-1]
                a = db.execute("""SELECT id, capability, lifecycle, verification,
                                         surfaces_ok, surfaces_total
                                  FROM action WHERE id=?""", (aid,)).fetchone()
                if not a:
                    raise Denied(404, "no such action")
                lg = db.execute("""SELECT seq, stage, executor, detail FROM ledger
                                   WHERE action_id=? ORDER BY seq""", (aid,)).fetchall()
                return self._send(200, {
                    "action_id": a[0], "capability": a[1],
                    "lifecycle": a[2], "verification": a[3],
                    "surfaces": f"{a[4] if a[4] is not None else 0}/{a[5]}",
                    "ledger": [{"seq": r[0], "stage": r[1], "executor": r[2],
                                "detail": json.loads(r[3])} for r in lg]})

            if u.path.startswith("/read/"):
                name = u.path[len("/read/"):]
                cap = CAPS.get(name) or self._nocap(name)
                if cap.get("mode") != "read":
                    raise Denied(405, f"{name} is a write capability; POST /do/{name}")
                e = q.get("entity") or self._need("entity")
                gate(db, cap, e, q.get("actor"), q.get("install"))
                return self._send(200, do_read(db, cap, e, q))

            raise Denied(404, "no such route")
        except Denied as d:
            self._send(d.code, {"error": d.msg})
        except Exception as ex:
            self._send(500, {"error": str(ex)})

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "body is not JSON"})
        db = self.server.db
        try:
            if not u.path.startswith("/do/"):
                raise Denied(404, "no such route")
            name = u.path[len("/do/"):]
            cap = CAPS.get(name) or self._nocap(name)
            if cap.get("mode", "write") != "write":
                raise Denied(405, f"{name} is a read capability; GET /read/{name}")
            e = body.get("entity") or self._need("entity")
            _check_args(cap, body.get("args", {}))
            decision = gate(db, cap, e, body.get("actor"), body.get("install"))
            return self._send(202, do_write(db, cap, e, body.get("args", {}),
                                            body.get("actor"), decision))
        except Denied as d:
            self._send(d.code, {"error": d.msg})
        except Exception as ex:
            self._send(500, {"error": str(ex)})

    def _need(self, w): raise Denied(400, f"missing '{w}'")
    def _nocap(self, n): raise Denied(404, f"no such capability: {n}")


def _check_args(cap, args):
    spec = cap.get("args", {})
    for k, s in spec.items():
        if s.get("required") and k not in args:
            raise Denied(400, f"missing required argument '{k}'")
        if k in args and "enum" in s and args[k] not in s["enum"]:
            raise Denied(400, f"'{k}' must be one of {s['enum']}")
    for k in args:
        if k not in spec:
            raise Denied(400, f"unexpected argument '{k}'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.db = sqlite3.connect(a.db, check_same_thread=False)
    srv.db.execute("PRAGMA foreign_keys=ON")
    print(f"node on http://127.0.0.1:{a.port}  db={a.db}  "
          f"capabilities={len(CAPS)}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
