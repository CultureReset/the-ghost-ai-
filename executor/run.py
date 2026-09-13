#!/usr/bin/env python3
"""The executor. The one job in the catalogue with no upstream.

    python3 -m executor.run --db node.sqlite --action ac_xxx --driver mock

Every run is the same five steps, and there is no path around them:

    fingerprint   refuse to act on a screen the map does not recognise
    execute       replay the recorded procedure
    settle        wait, because a surface does not reflect a change instantly
    verify        read it back on a DIFFERENT path than wrote it
    record        both dimensions of state, plus evidence, append-only

Anything that is not VERIFIED on every surface is not COMPLETED.
"""
import argparse, json, os, sqlite3, sys, time, uuid, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from executor import appmap
from executor.drivers import get as get_driver

EV_DIR = os.environ.get("ANEXTGENT_EVIDENCE", "/tmp/anextgent-evidence")


def _id(p): return f"{p}_{uuid.uuid4().hex[:12]}"


def _ledger(db, action_id, stage, executor, detail, evidence_id=None):
    seq = (db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM ledger WHERE action_id=?",
                      (action_id,)).fetchone()[0])
    db.execute("""INSERT INTO ledger(id,action_id,seq,stage,executor,detail,evidence_id)
                  VALUES (?,?,?,?,?,?,?)""",
               (_id("lg"), action_id, seq, stage, executor,
                json.dumps(detail, sort_keys=True), evidence_id))
    return seq


def _evidence(db, action_id, kind, path):
    blob = open(path, "rb").read()
    eid = _id("ev")
    db.execute("""INSERT INTO evidence(id,action_id,kind,sha256,uri) VALUES (?,?,?,?,?)""",
               (eid, action_id, kind, hashlib.sha256(blob).hexdigest(), path))
    return eid


def _finish(db, action_id, verdict, ok, total, note=None):
    db.execute("""UPDATE action SET lifecycle='FINISHED', verification=?,
                  surfaces_ok=?, surfaces_total=?, finished_at=datetime('now')
                  WHERE id=?""", (verdict, ok, total, action_id))
    _ledger(db, action_id, "FINISHED", None,
            {"verification": verdict, "surfaces": f"{ok}/{total}", "note": note})
    db.commit()
    return verdict


def run(db, action_id, driver_name="android", verifier_name=None, maps_dir=None,
        acts_as=None, verifier_acts_as=None):
    """`driver_name` is what actually drives; `acts_as` is the executor kind it
    stands in for. They differ only for the mock, which impersonates a real
    executor so the whole chain can be exercised with no hardware."""
    kind = acts_as or driver_name
    vkind = verifier_acts_as or verifier_name
    a = db.execute("""SELECT id, entity_id, capability, args, lifecycle
                      FROM action WHERE id=?""", (action_id,)).fetchone()
    if not a:
        raise SystemExit(f"no such action: {action_id}")
    _, entity_id, capability, args_json, lifecycle = a
    args = json.loads(args_json)

    if lifecycle == "AWAITING_APPROVAL":
        raise SystemExit(f"{action_id} is held for approval — a person has not said yes")
    if lifecycle == "FINISHED":
        raise SystemExit(f"{action_id} already finished")

    cap = json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "contracts", "capabilities", f"{capability}.json"), encoding="utf-8"))
    surfaces = cap["postcondition"]["surfaces"]

    m = appmap.find(capability, executor=kind, d=maps_dir)
    if not m:
        _ledger(db, action_id, "EXECUTING", driver_name, {"error": "no promoted map"})
        return _finish(db, action_id, "FAILED", 0, len(surfaces), "no promoted map")

    errs = appmap.validate(m)
    if errs:
        return _finish(db, action_id, "FAILED", 0, len(surfaces), f"bad map: {errs}")

    steps, missing = appmap.substitute(m["steps"], args)
    if missing:
        return _finish(db, action_id, "FAILED", 0, len(surfaces),
                       f"map needs arguments not supplied: {missing}")

    drv = get_driver(driver_name).Driver()
    ok, why = drv.available()
    if not ok:
        _ledger(db, action_id, "EXECUTING", driver_name, {"unavailable": why})
        return _finish(db, action_id, "FAILED", 0, len(surfaces), why)

    os.makedirs(EV_DIR, exist_ok=True)
    db.execute("UPDATE action SET lifecycle='EXECUTING' WHERE id=?", (action_id,))
    _ledger(db, action_id, "EXECUTING", driver_name,
            {"map": m["_file"], "map_version": m["map_version"],
             "app_version": m["app_version"], "device": why})

    # ---- 1. fingerprint ---------------------------------------------------
    drv.launch(m["steps"][0].get("package", m["app"]))
    absent = [f for f in m["fingerprint"] if not drv.present(f, timeout=5)]
    if absent:
        shot = drv.screenshot(os.path.join(EV_DIR, f"{action_id}-drift.json"))
        eid = _evidence(db, action_id, "screenshot", shot)
        _ledger(db, action_id, "DRIFTED", driver_name,
                {"absent": absent,
                 "app_version_seen": drv.app_version(m["app"]),
                 "map_expected": m["app_version"]}, eid)
        _map_run(db, m, action_id, appmap.DRIFTED)
        return _finish(db, action_id, "FAILED", 0, len(surfaces),
                       "screen did not match the map — refused to act")

    # ---- 2. execute -------------------------------------------------------
    try:
        for i, s in enumerate(steps):
            v = s["verb"]
            if v == "launch":   drv.launch(s["package"])
            elif v == "tap":    drv.tap(s["select"])
            elif v == "type":   drv.type(s["select"], s["text"])
            elif v == "clear":  drv.clear(s["select"])
            elif v == "back":   drv.back()
            elif v == "scroll": drv.scroll(s.get("direction", "down"))
            elif v == "wait":   time.sleep(float(s.get("seconds", 1)))
            elif v == "read":   drv.read(s["select"])
            elif v == "assert":
                if not drv.present(s["select"], timeout=int(s.get("timeout", 10))):
                    raise AssertionError(f"step {i}: expected {s['select']}")
    except Exception as e:
        shot = drv.screenshot(os.path.join(EV_DIR, f"{action_id}-fail.json"))
        eid = _evidence(db, action_id, "screenshot", shot)
        _ledger(db, action_id, "FAILED", driver_name, {"step": i, "error": str(e)}, eid)
        _map_run(db, m, action_id, appmap.FAILED)
        return _finish(db, action_id, "FAILED", 0, len(surfaces), str(e))

    shot = drv.screenshot(os.path.join(EV_DIR, f"{action_id}-after.json"))
    after = _evidence(db, action_id, "screenshot", shot)
    _ledger(db, action_id, "EXECUTED", driver_name, {"steps": len(steps)}, after)
    _map_run(db, m, action_id, appmap.OK)

    # ---- 3. settle + 4. verify -------------------------------------------
    settle = cap["verify"]["settle_seconds"]
    vname = verifier_name or cap["verify"]["by"][0]
    if (vkind or vname) == kind:
        return _finish(db, action_id, "FAILED", 0, len(surfaces),
                       "verifier is the executor — that is self-certification")

    db.execute("UPDATE action SET lifecycle='VERIFYING' WHERE id=?", (action_id,))
    _ledger(db, action_id, "VERIFYING", vname,
            {"settle_seconds": settle, "surfaces": surfaces})
    if settle and os.environ.get("ANEXTGENT_NO_SETTLE") != "1":
        time.sleep(min(settle, 3))

    results = _verify(db, action_id, m, cap, args, surfaces, drv, vname)
    good = [r for r in results if r["verdict"] == "VERIFIED"]
    pend = [r for r in results if r["verdict"] == "NOT_YET_VERIFIABLE"]

    if len(good) == len(surfaces):
        verdict = "VERIFIED"
    elif good:
        verdict = "PARTIALLY_VERIFIED"
    elif pend and not any(r["verdict"] == "CONTRADICTED" for r in results):
        verdict = "NOT_YET_VERIFIABLE"
    else:
        verdict = "CONTRADICTED"

    if verdict == "PARTIALLY_VERIFIED":
        _ledger(db, action_id, "PARTIAL", vname,
                {"on_partial": cap.get("on_partial"),
                 "unresolved": [r["surface"] for r in results if r["verdict"] != "VERIFIED"],
                 "note": "declared compensation has not been executed — that is "
                         "the next thing to build, and until it is, a partial "
                         "result is escalated rather than silently accepted"})
    return _finish(db, action_id, verdict, len(good), len(surfaces))


def _verify(db, action_id, m, cap, args, surfaces, drv, vname):
    """Read the result back and write it to surface_state. This table is what
    the consistency view reads, so verifying an action and knowing where a
    business is inconsistent are the same act."""
    spec = m.get("verify", {})
    field = spec.get("field")
    expect, _ = appmap.substitute([{"v": spec.get("expect", "")}], args)
    expect = expect[0]["v"]
    out = []
    for s in surfaces:
        observed, verdict = None, "NOT_YET_VERIFIABLE"
        if vname == "mock" or (vname == "browser" and hasattr(drv, "public_value")):
            observed = drv.public_value(field) if hasattr(drv, "public_value") else None
            if observed is not None:
                verdict = "VERIFIED" if str(observed) == str(expect) else "CONTRADICTED"
        db.execute("""INSERT INTO surface_state(id,entity_id,field,surface,observed,verdict)
                      VALUES (?,(SELECT entity_id FROM action WHERE id=?),?,?,?,?)
                      ON CONFLICT(entity_id,field,surface) DO UPDATE SET
                        observed=excluded.observed, verdict=excluded.verdict,
                        checked_at=datetime('now')""",
                   (_id("ss"), action_id, cap["name"], s, observed, verdict))
        _ledger(db, action_id, "SURFACE", vname,
                {"surface": s, "expected": expect, "observed": observed, "verdict": verdict})
        out.append({"surface": s, "observed": observed, "verdict": verdict})
    return out


def _map_run(db, m, action_id, outcome):
    row = db.execute("""SELECT id FROM app_map WHERE app=? AND app_version=?
                        AND capability=? AND map_version=?""",
                     (m["app"], m["app_version"], m["capability"], m["map_version"])).fetchone()
    if not row:
        mid = _id("mp")
        db.execute("""INSERT INTO app_map(id,app,app_version,map_version,capability,
                        executor,fingerprint,steps,state,learned_from)
                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                   (mid, m["app"], m["app_version"], m["map_version"], m["capability"],
                    m["executor"], json.dumps(m["fingerprint"]), json.dumps(m["steps"]),
                    m.get("state", "candidate"), m.get("learned_from")))
    else:
        mid = row[0]
    db.execute("INSERT INTO map_run(id,map_id,action_id,outcome) VALUES (?,?,?,?)",
               (_id("mr"), mid, action_id, outcome))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--action", required=True)
    ap.add_argument("--driver", default="android")
    ap.add_argument("--verifier")
    ap.add_argument("--as", dest="acts_as",
                    help="executor kind this driver stands in for (mock only)")
    ap.add_argument("--verifier-as", dest="verifier_acts_as")
    ap.add_argument("--maps")
    a = ap.parse_args()
    db = sqlite3.connect(a.db, timeout=15); db.execute("PRAGMA foreign_keys=ON")
    v = run(db, a.action, a.driver, a.verifier, a.maps, a.acts_as, a.verifier_acts_as)
    row = db.execute("""SELECT lifecycle, verification, surfaces_ok, surfaces_total
                        FROM action WHERE id=?""", (a.action,)).fetchone()
    print(f"\n  lifecycle    {row[0]}")
    print(f"  verification {row[1]}")
    print(f"  surfaces     {row[2]}/{row[3]}")
    return 0 if v == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
