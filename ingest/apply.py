"""Write a parsed message into the node.

Nothing is overwritten. Every fact becomes an observation with its source and
timestamp; bookings are upserted by (channel, external_ref) so replaying the
same mailbox twice cannot double-book.

Also performs reconciliation: if a lead was captured on the business's own page
before the visitor was handed to the platform, the confirmation email is what
joins the two. That join is how the business ends up owning the customer.
"""
import sqlite3, json, uuid, re
from .model import PARSED


def _id(p): return f"{p}_{uuid.uuid4().hex[:12]}"


def apply_result(db: sqlite3.Connection, entity_id: str, r, raw_ref=None):
    if r.status != PARSED:
        return {"written": 0, "status": r.status, "missing": r.missing}
    if r.summary:
        return _sales(db, entity_id, r)
    if r.booking:
        return _booking(db, entity_id, r)
    return {"written": 0, "status": "IGNORED"}


# ---------------------------------------------------------------- bookings
def _booking(db, entity_id, r):
    b, out = r.booking, {"status": PARSED, "kind": r.kind}

    row = db.execute("""SELECT id, state, person_id FROM booking
                        WHERE channel=? AND external_ref=?""",
                     (b.channel, b.external_ref)).fetchone()

    if row:
        bid, current, person_id = row
        slot_id = None
        # State only advances. Mailboxes get replayed and messages arrive out
        # of order; a cancellation is terminal, so an older booking notice must
        # never un-cancel a seat that is already back in inventory.
        if current == "cancelled":
            out["duplicate" if b.state == "cancelled" else "ignored_stale"] = True
        elif b.state != current:
            db.execute("""UPDATE booking SET state=?,
                          cancelled_at=CASE WHEN ?='cancelled' THEN datetime('now')
                                            ELSE cancelled_at END
                          WHERE id=?""", (b.state, b.state, bid))
            out["updated"] = b.state
        else:
            out["duplicate"] = True
    else:
        person_id = _person(db, b)
        slot_id = _slot(db, entity_id, b)
        bid = _id("bk")
        db.execute("""INSERT INTO booking
            (id, entity_id, slot_id, channel, external_ref, person_id, qty,
             total_cents, state, source_ref)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (bid, entity_id, slot_id, b.channel, b.external_ref, person_id,
             b.qty, b.total_cents, b.state, r.source_ref))
        out["created"] = bid

    _observe(db, entity_id, f"booking.{b.channel}.{b.external_ref}.state",
             b.state, f"email:{b.channel}", r.source_ref)

    if not out.get("duplicate") and not out.get("ignored_stale"):
        lead = _reconcile(db, entity_id, b, bid, person_id)
        if lead:
            out["reconciled_lead"] = lead

    out["booking_id"], out["slot_id"], out["person_id"] = bid, slot_id, person_id
    out["written"] = 1
    return out


def _person(db, b):
    """Find an existing customer by phone or email before creating another."""
    for ch, val in (("sms", b.customer_phone), ("email", b.customer_email)):
        if not val:
            continue
        row = db.execute("""SELECT person_id FROM person_contact
                            WHERE channel=? AND value=?""", (ch, val)).fetchone()
        if row:
            return row[0]
    # A name with no phone and no email cannot be deduplicated, so creating a
    # person for it manufactures a new duplicate on every replay.
    if not (b.customer_phone or b.customer_email):
        return None
    pid = _id("pr")
    db.execute("INSERT INTO person(id,kind,display_name) VALUES (?,'customer',?)",
               (pid, b.customer_name))
    for ch, val in (("sms", b.customer_phone), ("email", b.customer_email)):
        if val:
            db.execute("""INSERT INTO person_contact(id,person_id,channel,value,consent)
                          VALUES (?,?,?,?,'transactional')""", (_id("pc"), pid, ch, val))
    return pid


def _slot(db, entity_id, b):
    """Bookings arrive for times the operator declared. An arrival for a time
    nobody declared is still recorded — it just has no capacity to decrement,
    and that discrepancy is what the reconciliation report is for."""
    if not b.starts_at:
        return None
    row = db.execute("""SELECT s.id FROM slot s
                        LEFT JOIN charter_trip t ON t.id = s.trip_id
                        WHERE s.entity_id=? AND s.starts_at=?
                          AND (? IS NULL OR t.name = ?)""",
                     (entity_id, b.starts_at, b.trip, b.trip)).fetchone()
    return row[0] if row else None


def _reconcile(db, entity_id, b, booking_id, person_id):
    """lead + booking -> one customer the business owns."""
    if not (b.customer_phone or b.customer_email):
        return None
    row = db.execute("""SELECT id FROM lead
                        WHERE entity_id=? AND reconciled_at IS NULL
                          AND (phone=? OR email=?)
                        ORDER BY created_at DESC LIMIT 1""",
                     (entity_id, b.customer_phone, b.customer_email)).fetchone()
    if not row:
        return None
    db.execute("""UPDATE lead SET reconciled_booking_id=?, reconciled_at=datetime('now'),
                  match_confidence=?, person_id=COALESCE(person_id,?) WHERE id=?""",
               (booking_id, 0.95, person_id, row[0]))
    db.execute("UPDATE booking SET lead_id=? WHERE id=?", (row[0], booking_id))
    return row[0]


# ---------------------------------------------------------------- sales
def _sales(db, entity_id, r):
    s = r.summary
    _observe(db, entity_id, "sales.gross_cents", str(s.gross_cents),
             f"email:{s.channel}", r.source_ref, s.business_day)
    _observe(db, entity_id, "sales.orders", str(s.orders),
             f"email:{s.channel}", r.source_ref, s.business_day)
    matched = 0
    for label, qty in s.items.items():
        _observe(db, entity_id, f"item.sold.{label}", str(qty),
                 f"email:{s.channel}", r.source_ref, s.business_day)
        row = db.execute("""SELECT mi.id FROM menu_item mi
                            JOIN menu_section ms ON ms.id = mi.section_id
                            JOIN menu m ON m.id = ms.menu_id
                            WHERE m.entity_id=? AND lower(mi.name)=lower(?)""",
                         (entity_id, label)).fetchone()
        if row:
            matched += 1
    return {"status": PARSED, "kind": "sales_summary", "written": len(s.items) + 2,
            "items": len(s.items), "matched_menu_items": matched}


def _observe(db, entity_id, field, value, source, source_ref, observed_at=None):
    db.execute("""INSERT INTO observation
        (id, entity_id, field, value, source, source_ref, observed_at)
        VALUES (?,?,?,?,?,?,COALESCE(?, datetime('now')))""",
        (_id("ob"), entity_id, field, value, source, source_ref, observed_at))
