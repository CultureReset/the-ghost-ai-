"""One engine. Every vendor is data.

This is the difference between a re-map being a code release and a re-map being
a data push. FareHarbor changes their template on a Tuesday; the fix is a new
JSON map, signed and pulled like any other artifact, on every node overnight —
not a rebuild, not a fleet image, not a deploy.

Same reason app maps are data and not Python.
"""
import json, os, re, glob
from .model import Booking, SalesSummary, Result, PARSED, DRIFTED, UNMATCHED

MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")


def load_maps(d=None):
    maps = []
    for f in sorted(glob.glob(os.path.join(d or MAPS_DIR, "*.json"))):
        m = json.load(open(f, encoding="utf-8"))
        m["_file"] = os.path.basename(f)
        maps.append(m)
    return maps


# ---------------------------------------------------------------- transforms
MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}


def _datetime(s):
    """Returns None rather than a guess. A wrong timestamp silently books the
    wrong slot, which is worse than not booking one."""
    m = re.search(r"([A-Za-z]{3})[a-z]*\s+(\d{1,2}),?\s+(\d{4})", s)
    if not m:
        return None
    mon = MONTHS.get(m.group(1).lower())
    if not mon:
        return None
    t = re.search(r"(\d{1,2}):(\d{2})\s*([AaPp])?\.?[Mm]?", s)
    hh, mm = (int(t.group(1)), int(t.group(2))) if t else (0, 0)
    if t and t.group(3):
        ap = t.group(3).lower()
        if ap == "p" and hh != 12: hh += 12
        if ap == "a" and hh == 12: hh = 0
    return f"{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}T{hh:02d}:{mm:02d}"


def _phone(s):
    d = re.sub(r"\D", "", s)
    return d if len(d) >= 10 else None


TRANSFORM = {
    "string":   lambda s: s.strip() or None,
    "int":      lambda s: int(re.sub(r"\D", "", s)) if re.search(r"\d", s) else None,
    "money":    lambda s: int(round(float(s.replace(",", "").strip()) * 100)),
    "datetime": _datetime,
    "phone":    _phone,
    "email":    lambda s: s.strip() or None,
}


def _extract(body, spec):
    for p in spec.get("patterns", []):
        m = re.search(p, body, re.I | re.M)
        if m:
            try:
                v = TRANSFORM[spec.get("type", "string")](m.group(1))
            except (ValueError, KeyError):
                v = None
            if v is not None:
                return v
    return spec.get("default")


# ---------------------------------------------------------------- apply a map
def apply_map(m, ctx):
    body = ctx["body"]
    fields = {k: _extract(body, s) for k, s in m.get("fields", {}).items()}

    if m.get("kind") == "sales_summary":
        items = {}
        for rule in m.get("repeating", {}).get("items", []):
            for mm in re.finditer(rule["pattern"], body, re.M):
                items[mm.group(rule["label"]).strip()] = int(mm.group(rule["qty"]))
        return Result(status=PARSED, kind="sales_summary",
                      summary=SalesSummary(channel=m["vendor"],
                                           business_day=fields.get("business_day") or "",
                                           gross_cents=fields.get("gross_cents") or 0,
                                           orders=fields.get("orders") or 0,
                                           items=items))

    cancelled = bool(m.get("cancelled_when") and
                     re.search(m["cancelled_when"], ctx["subject"] + body, re.I))
    return Result(status=PARSED,
                  kind="cancellation" if cancelled else "booking",
                  booking=Booking(channel=m["vendor"],
                                  external_ref=fields.get("external_ref") or "",
                                  starts_at=fields.get("starts_at"),
                                  trip=fields.get("trip"),
                                  qty=fields.get("qty") or 1,
                                  total_cents=fields.get("total_cents"),
                                  state="cancelled" if cancelled else "confirmed",
                                  customer_name=fields.get("customer_name"),
                                  customer_phone=fields.get("customer_phone"),
                                  customer_email=fields.get("customer_email")))


def match_map(m, ctx):
    where = "".join(ctx[k] for k in m.get("match_on", ["from", "subject"]))
    return any(re.search(p, where, re.I) for p in m["match"])


def fingerprint(m, ctx):
    """Same gate as the executor: if the message does not look like what the
    map was written against, refuse rather than parse it into wrong numbers."""
    whole = "\n".join((ctx["from"], ctx["subject"], ctx["body"]))
    return [p for p in m.get("fingerprint", []) if not re.search(p, whole, re.I)]
