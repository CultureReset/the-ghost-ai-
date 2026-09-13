"""Take a raw email, hand back a normalised record."""
import email, re
from email import policy
from .model import Result, DRIFTED, PARSED, UNMATCHED
from .parsers import load


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


def parse_message(raw: str) -> Result:
    msg = email.message_from_string(raw, policy=policy.default)
    ctx = {
        "from":    str(msg.get("From", "")),
        "subject": str(msg.get("Subject", "")),
        "to":      str(msg.get("To", "")),
        "id":      str(msg.get("Message-ID", "")),
        "date":    str(msg.get("Date", "")),
        "body":    _text(msg) or "",
    }
    for mod in load():
        if not mod.match(ctx):
            continue
        # Fingerprint gate. Same rule as the executor: if the message does not
        # look like what we were mapped against, refuse to parse it.
        whole = "\n".join((ctx["from"], ctx["subject"], ctx["body"]))
        missing = [m for m in mod.FINGERPRINT if not re.search(m, whole, re.I)]
        if missing:
            return Result(status=DRIFTED, vendor=mod.VENDOR,
                          missing=missing, source_ref=ctx["id"])
        r = mod.parse(ctx)
        r.status, r.vendor, r.source_ref = PARSED, mod.VENDOR, ctx["id"]
        return r
    return Result(status=UNMATCHED, source_ref=ctx["id"])
