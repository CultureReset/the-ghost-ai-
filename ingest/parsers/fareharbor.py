"""FareHarbor booking and cancellation notices."""
import re
from ..model import Booking, Result

VENDOR = "fareharbor"
FINGERPRINT = [r"fareharbor", r"booking\s*#|reference"]

_MATCH = re.compile(r"fareharbor", re.I)

def match(ctx):
    return bool(_MATCH.search(ctx["from"]) or _MATCH.search(ctx["subject"]))

def parse(ctx):
    b, s = ctx["body"], ctx["subject"]
    cancelled = bool(re.search(r"\bcancell?ed\b", s + b, re.I))

    ref  = _find(b, r"Booking\s*#\s*([A-Z0-9-]+)", r"Reference:\s*([A-Z0-9-]+)")
    trip = _find(b, r"Item:\s*(.+)", r"Tour:\s*(.+)")
    when = _find(b, r"Date(?:/Time)?:\s*(.+)", r"When:\s*(.+)")
    qty  = _find(b, r"Guests?:\s*(\d+)", r"Party size:\s*(\d+)") or "1"
    name = _find(b, r"Customer:\s*(.+)", r"Name:\s*(.+)")
    phone= _find(b, r"Phone:\s*([0-9()+\-.\s]{7,})")
    mail = _find(b, r"Email:\s*(\S+@\S+)")
    tot  = _find(b, r"Total:\s*\$?([\d,]+\.\d{2})")

    return Result(status="PARSED",
                  kind="cancellation" if cancelled else "booking",
                  booking=Booking(
                      channel=VENDOR, external_ref=ref or "",
                      starts_at=_when(when), trip=trip, qty=int(qty),
                      total_cents=_cents(tot),
                      state="cancelled" if cancelled else "confirmed",
                      customer_name=name, customer_phone=_digits(phone),
                      customer_email=mail))

# ---- shared helpers, deliberately small and boring -------------------------
def _find(text, *pats):
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()
    return None

def _cents(s):
    return None if not s else int(round(float(s.replace(",", "")) * 100))

def _digits(s):
    if not s: return None
    d = re.sub(r"\D", "", s)
    return d if len(d) >= 10 else None

MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}

def _when(s):
    """'September 14, 2026 at 10:00 AM' -> '2026-09-14T10:00'. Returns None
    rather than a guess — a wrong timestamp silently books the wrong slot."""
    if not s: return None
    m = re.search(r"([A-Za-z]{3})[a-z]*\s+(\d{1,2}),?\s+(\d{4})", s)
    if not m: return None
    mon = MONTHS.get(m.group(1).lower())
    if not mon: return None
    t = re.search(r"(\d{1,2}):(\d{2})\s*([AaPp])?\.?[Mm]?", s)
    hh, mm = (int(t.group(1)), int(t.group(2))) if t else (0, 0)
    if t and t.group(3):
        ap = t.group(3).lower()
        if ap == "p" and hh != 12: hh += 12
        if ap == "a" and hh == 12: hh = 0
    return f"{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}T{hh:02d}:{mm:02d}"
