"""Airbnb reservation notices."""
import re
from ..model import Booking, Result
from .fareharbor import _find, _cents, _when

VENDOR = "airbnb"
FINGERPRINT = [r"airbnb", r"confirmation code|reservation"]

def match(ctx):
    return bool(re.search(r"airbnb\.com", ctx["from"], re.I))

def parse(ctx):
    b, s = ctx["body"], ctx["subject"]
    cancelled = bool(re.search(r"\bcancell?ed\b", s + b, re.I))
    return Result(status="PARSED",
                  kind="cancellation" if cancelled else "booking",
                  booking=Booking(
                      channel=VENDOR,
                      external_ref=_find(b, r"Confirmation code:?\s*([A-Z0-9]+)") or "",
                      starts_at=_when(_find(b, r"Check-?in:\s*(.+)")),
                      trip=_find(b, r"Listing:\s*(.+)"),
                      qty=int(_find(b, r"Guests?:\s*(\d+)") or 1),
                      total_cents=_cents(_find(b, r"(?:Total payout|You earn):\s*\$?([\d,]+\.\d{2})")),
                      state="cancelled" if cancelled else "confirmed",
                      customer_name=_find(b, r"Guest:\s*(.+)")))
