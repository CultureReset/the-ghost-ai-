"""An AppMap is a recorded procedure. It is data, for the same reason a vendor
parser is data: when Toast moves a button, the fix has to be a signed file every
node pulls overnight, not a code release.

Keyed on app x app_version x map_version, never on app alone. A redesign is a
new row, not a corrupted one.
"""
import json, os, glob, re

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appmaps")

DRIFTED, OK, FAILED, TOOK_OVER = "DRIFTED", "OK", "FAILED", "TOOK_OVER"

VERBS = {"launch", "tap", "type", "clear", "wait", "scroll", "back", "assert", "read"}


def load_all(d=None):
    out = []
    for f in sorted(glob.glob(os.path.join(d or DIR, "*.json"))):
        if os.path.basename(f).startswith("_"):
            continue          # fixtures and screens files, not maps
        m = json.load(open(f, encoding="utf-8"))
        m["_file"] = os.path.basename(f)
        out.append(m)
    return out


def find(capability, executor=None, app=None, d=None):
    """Promoted maps win. A candidate is never run against a customer."""
    best = None
    for m in load_all(d):
        if m["capability"] != capability:
            continue
        if executor and m["executor"] != executor:
            continue
        if app and m["app"] != app:
            continue
        rank = {"promoted": 0, "canary": 1, "candidate": 2, "retired": 9}[m.get("state", "candidate")]
        if best is None or (rank, -m["map_version"]) < best[0]:
            best = ((rank, -m["map_version"]), m)
    if best and best[0][0] >= 2:
        return None            # candidate only — not fit to run
    return best[1] if best else None


def validate(m):
    errs = []
    for k in ("app", "app_version", "map_version", "capability", "executor",
              "fingerprint", "steps"):
        if k not in m:
            errs.append(f"missing '{k}'")
    if not m.get("fingerprint"):
        errs.append("fingerprint is empty — a map with no fingerprint cannot "
                    "refuse to act on a screen it does not recognise")
    for i, s in enumerate(m.get("steps", [])):
        if s.get("verb") not in VERBS:
            errs.append(f"step {i}: unknown verb {s.get('verb')!r}")
        if s.get("verb") in ("tap", "type", "clear", "read", "assert") and not s.get("select"):
            errs.append(f"step {i}: {s['verb']} needs a selector")
        if s.get("select", {}).get("at"):
            errs.append(f"step {i}: coordinate selector — a map that taps a "
                        "point breaks the moment anything moves")
    return errs


def substitute(steps, args):
    """{{day}} -> args['day']. A step referencing an argument that was not
    supplied is an error, not an empty string."""
    out, missing = [], set()
    def sub(v):
        if not isinstance(v, str):
            return v
        def rep(mo):
            k = mo.group(1).strip()
            if k not in args:
                missing.add(k); return mo.group(0)
            return str(args[k])
        return re.sub(r"\{\{([^}]+)\}\}", rep, v)
    for s in steps:
        out.append({k: ({kk: sub(vv) for kk, vv in v.items()} if isinstance(v, dict) else sub(v))
                    for k, v in s.items()})
    return out, sorted(missing)
