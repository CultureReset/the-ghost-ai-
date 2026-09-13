"""Take a raw email, hand back a normalised record."""
import email, re
from email import policy
from .model import Result, DRIFTED, PARSED, UNMATCHED
from .engine import load_maps, match_map, fingerprint, apply_map


def _text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return re.sub(r"<[^>]+>", " ", part.get_content())
        return ""
    c = msg.get_content()
    return re.sub(r"<[^>]+>", " ", c) if msg.get_content_type() == "text/html" else c


def parse_message(raw: str, maps_dir=None) -> Result:
    msg = email.message_from_string(raw, policy=policy.default)
    ctx = {
        "from":    str(msg.get("From", "")),
        "subject": str(msg.get("Subject", "")),
        "to":      str(msg.get("To", "")),
        "id":      str(msg.get("Message-ID", "")),
        "date":    str(msg.get("Date", "")),
        "body":    _text(msg) or "",
    }
    for m in load_maps(maps_dir):
        if not match_map(m, ctx):
            continue
        missing = fingerprint(m, ctx)
        if missing:
            return Result(status=DRIFTED, vendor=m["vendor"],
                          missing=missing, source_ref=ctx["id"])
        r = apply_map(m, ctx)
        r.vendor, r.source_ref = m["vendor"], ctx["id"]
        return r
    return Result(status=UNMATCHED, source_ref=ctx["id"])
