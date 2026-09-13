"""Toast end-of-day sales summary — the other half of ingestion.

Not a booking. This is what closes the loop between a QR scan and what was
actually eaten, which is what makes an item-level verified review possible.
"""
import re
from ..model import SalesSummary, Result
from .fareharbor import _cents, _find

VENDOR = "toast"
FINGERPRINT = [r"toast", r"net sales|gross sales", r"orders?"]

def match(ctx):
    return bool(re.search(r"toasttab\.com|toast pos", ctx["from"] + ctx["subject"], re.I))

def parse(ctx):
    b = ctx["body"]
    items = {}
    # "  12  Shrimp Scampi" or "Shrimp Scampi x 12"
    for m in re.finditer(r"^\s*(\d{1,4})\s+([A-Za-z][A-Za-z0-9 '&/-]{2,40})\s*$", b, re.M):
        items[m.group(2).strip()] = int(m.group(1))
    for m in re.finditer(r"^\s*([A-Za-z][A-Za-z0-9 '&/-]{2,40})\s+x\s*(\d{1,4})\s*$", b, re.M):
        items[m.group(1).strip()] = int(m.group(2))
    return Result(status="PARSED", kind="sales_summary",
                  summary=SalesSummary(
                      channel=VENDOR,
                      business_day=_find(b, r"Business day:\s*(\d{4}-\d{2}-\d{2})") or "",
                      gross_cents=_cents(_find(b, r"(?:Gross|Net) sales:\s*\$?([\d,]+\.\d{2})")) or 0,
                      orders=int(_find(b, r"Orders?:\s*(\d+)") or 0),
                      items=items))
