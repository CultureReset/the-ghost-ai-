"""Peek Pro booking notices."""
import re
from ..model import Booking, Result
from .fareharbor import _find, _cents, _digits, _when

VENDOR = "peek"
FINGERPRINT = [r"peek", r"confirmation\s*(code|#)|booking id"]

def match(ctx):
    return bool(re.search(r"peek(pro)?\.com|peek pro", ctx["from"] + ctx["subject"], re.I))

def parse(ctx):
    b = ctx["body"]
    cancelled = bool(re.search(r"\bcancell?ed\b", ctx["subject"] + b, re.I))
    return Result(status="PARSED",
                  kind="cancellation" if cancelled else "booking",
                  booking=Booking(
                      channel=VENDOR,
                      external_ref=_find(b, r"Confirmation\s*(?:code|#)\s*:?\s*([A-Z0-9-]+)",
                                            r"Booking ID:\s*([A-Z0-9-]+)") or "",
                      starts_at=_when(_find(b, r"Activity date:\s*(.+)", r"When:\s*(.+)")),
                      trip=_find(b, r"Activity:\s*(.+)"),
                      qty=int(_find(b, r"(?:Guests?|Tickets?):\s*(\d+)") or 1),
                      total_cents=_cents(_find(b, r"Total(?: paid)?:\s*\$?([\d,]+\.\d{2})")),
                      state="cancelled" if cancelled else "confirmed",
                      customer_name=_find(b, r"Guest(?: name)?:\s*(.+)"),
                      customer_phone=_digits(_find(b, r"Phone:\s*([0-9()+\-.\s]{7,})")),
                      customer_email=_find(b, r"Email:\s*(\S+@\S+)")))
