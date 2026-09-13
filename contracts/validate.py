#!/usr/bin/env python3
"""Validate capabilities, ActionSpecs and VAPP manifests against the contracts.

No dependencies. Runs anywhere Python 3.8+ runs, including on the box.

Beyond JSON Schema it enforces the four rules that are not expressible in
JSON Schema and that the architecture actually turns on:

  1. verify.by must not overlap executors on a WRITE — the verifier is never
     the executor, or it is self-certification with extra steps
  2. write capabilities must set on_partial — silent partial success is worse
                                              than clean failure
  3. a VAPP names capabilities, never tables
  4. FINISHED requires a verification verdict
"""
import json, sys, re, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- mini schema
def check(inst, sch, path="$", errs=None, root=None):
    errs = [] if errs is None else errs
    root = sch if root is None else root
    if "$ref" in sch:
        return check(inst, resolve(sch["$ref"], root), path, errs, root)
    t = sch.get("type")
    if t:
        ok = {"object": dict, "array": list, "string": str, "boolean": bool,
              "number": (int, float), "integer": int}[t]
        if t == "integer" and isinstance(inst, bool): ok = ()
        if not isinstance(inst, ok):
            errs.append(f"{path}: expected {t}, got {type(inst).__name__}"); return errs
    if "enum" in sch and inst not in sch["enum"]:
        errs.append(f"{path}: {inst!r} not one of {sch['enum']}")
    if "const" in sch and inst != sch["const"]:
        errs.append(f"{path}: expected {sch['const']!r}")
    if isinstance(inst, str):
        if "pattern" in sch and not re.search(sch["pattern"], inst):
            errs.append(f"{path}: {inst!r} does not match {sch['pattern']}")
        if "minLength" in sch and len(inst) < sch["minLength"]:
            errs.append(f"{path}: shorter than {sch['minLength']}")
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in sch and inst < sch["minimum"]:
            errs.append(f"{path}: below minimum {sch['minimum']}")
    if isinstance(inst, list):
        if "minItems" in sch and len(inst) < sch["minItems"]:
            errs.append(f"{path}: needs at least {sch['minItems']} item(s)")
        if "items" in sch:
            for i, v in enumerate(inst):
                check(v, sch["items"], f"{path}[{i}]", errs, root)
    if isinstance(inst, dict):
        for r in sch.get("required", []):
            if r not in inst: errs.append(f"{path}: missing required '{r}'")
        props = sch.get("properties", {})
        if sch.get("additionalProperties") is False:
            for k in inst:
                if k not in props: errs.append(f"{path}: unexpected property '{k}'")
        for k, v in inst.items():
            if k in props:
                check(v, props[k], f"{path}.{k}", errs, root)
            elif isinstance(sch.get("additionalProperties"), dict):
                check(v, sch["additionalProperties"], f"{path}.{k}", errs, root)
    for sub in sch.get("allOf", []):
        if "if" in sub:
            if not check(inst, sub["if"], path, [], root):
                check(inst, sub.get("then", {}), path, errs, root)
        else:
            check(inst, sub, path, errs, root)
    return errs

def resolve(ref, root):
    node = root
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node

def load(p): return json.load(open(p, encoding="utf-8"))

# ---------------------------------------------------------------- extra rules
def capability_rules(c):
    e = []
    ex = set(c.get("executors", []))
    by = set(c.get("verify", {}).get("by", []))
    # Independence is a rule about writes. A read changes nothing, so there is
    # no second path to prove it on.
    if c.get("mode", "write") == "write" and ex & by:
        e.append(f"verify.by overlaps executors on {sorted(ex & by)} — "
                 "the verifier must not be the executor")
    if c.get("mode", "write") == "write" and "on_partial" not in c:
        e.append("write capability has no on_partial — a partial result would "
                 "report as completed")
    if c.get("risk") in ("high", "critical") and c.get("approval") in (None, "none"):
        e.append(f"risk={c['risk']} with approval={c.get('approval')} — "
                 "high-risk writes need a person")
    return e

TABLEY = re.compile(r"^(select|insert|update|delete)\b|_table$|^db\.", re.I)
def vapp_rules(v, known):
    e = []
    for k in ("reads", "writes"):
        for name in v.get(k, []):
            if TABLEY.search(name) or "/" in name:
                e.append(f"{k}: '{name}' looks like data access, not a capability")
            elif known and name not in known:
                e.append(f"{k}: '{name}' is not a known capability")
    for name in v.get("mcp", {}).get("public", []):
        cap = known.get(name) if known else None
        if cap and cap.get("mode", "write") == "write":
            e.append(f"mcp.public exposes write capability '{name}' — "
                     "the public surface is read-only by construction")
    return e

def action_rules(a):
    e = []
    if a.get("lifecycle") == "FINISHED" and not a.get("verification"):
        e.append("FINISHED without a verification verdict")
    if a.get("verification") == "PARTIALLY_VERIFIED":
        v = [s for s in a.get("surfaces", []) if s.get("verdict") != "VERIFIED"]
        if not v:
            e.append("PARTIALLY_VERIFIED but every surface verified")
    return e

# ---------------------------------------------------------------- main
def main(argv):
    schemas = {n: load(f"{HERE}/schemas/{n}.schema.json")
               for n in ("capability", "actionspec", "vapp.manifest")}
    caps, failures, checked = {}, 0, 0

    for f in sorted(glob.glob(f"{HERE}/capabilities/*.json")):
        c = load(f); checked += 1
        errs = check(c, schemas["capability"]) + capability_rules(c)
        report(f, errs); failures += bool(errs)
        if not errs: caps[c["name"]] = c

    for f in argv:
        d = load(f); checked += 1
        kind = ("vapp.manifest" if "targets" in d else
                "actionspec"    if "lifecycle" in d else "capability")
        errs = check(d, schemas[kind])
        errs += (vapp_rules(d, caps) if kind == "vapp.manifest" else
                 action_rules(d)     if kind == "actionspec" else
                 capability_rules(d))
        report(f, errs); failures += bool(errs)

    print(f"\n{checked} checked, {failures} failed, {len(caps)} capabilities registered")
    return 1 if failures else 0

def report(f, errs):
    name = os.path.relpath(f)
    if errs:
        print(f"FAIL  {name}")
        for e in errs: print(f"        {e}")
    else:
        print(f"ok    {name}")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
