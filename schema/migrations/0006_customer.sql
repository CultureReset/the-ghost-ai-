-- 0006 customer capture and reconciliation
-- The mechanism that takes the customer relationship back from the platform.
PRAGMA foreign_keys = ON;

-- Captured on your page, BEFORE the redirect. This is the whole point.
CREATE TABLE lead (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  name TEXT, phone TEXT, email TEXT,
  intent_trip_id TEXT,                  -- what they were looking at
  intent_slot_id TEXT REFERENCES slot(id),
  intent_at TEXT,                       -- the date/time they wanted
  redirected_to TEXT,                   -- fareharbor | peek | airbnb
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  reconciled_booking_id TEXT REFERENCES booking(id),
  reconciled_at TEXT,
  match_confidence REAL
);
CREATE INDEX idx_lead_open ON lead(entity_id, reconciled_at, created_at DESC);
CREATE INDEX idx_lead_phone ON lead(phone);

-- Waiting list. Feeds the cancellation loop.
CREATE TABLE waitlist (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  trip_id TEXT, wants_from TEXT, wants_to TEXT, qty INTEGER NOT NULL DEFAULT 1,
  notified_at TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE message (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  direction TEXT NOT NULL,              -- in | out
  channel TEXT NOT NULL,                -- sms | voice | email
  body TEXT, sent_at TEXT NOT NULL DEFAULT (datetime('now')),
  campaign TEXT, action_id TEXT REFERENCES action(id),
  CHECK (direction IN ('in','out'))
);
CREATE INDEX idx_msg_person ON message(person_id, sent_at DESC);

CREATE TABLE review (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  subject_kind TEXT NOT NULL DEFAULT 'entity',   -- entity | menu_item | trip
  subject_id TEXT,
  rating INTEGER, body TEXT,
  verified_by TEXT,                     -- ticket:<id> | booking:<id>
  source TEXT NOT NULL DEFAULT 'own',   -- own | google | facebook | yelp
  external_ref TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (rating IS NULL OR rating BETWEEN 1 AND 5)
);
CREATE INDEX idx_review_subject ON review(subject_kind, subject_id);

CREATE TABLE review_reply (
  id TEXT PRIMARY KEY,
  review_id TEXT NOT NULL REFERENCES review(id) ON DELETE CASCADE,
  draft TEXT NOT NULL, approved_by TEXT REFERENCES person(id),
  approved_at TEXT, posted_at TEXT, action_id TEXT REFERENCES action(id)
);

CREATE TABLE loyalty_account (
  id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  entity_id TEXT REFERENCES entity(id),  -- NULL = co-op, across businesses
  points INTEGER NOT NULL DEFAULT 0,
  tier TEXT, UNIQUE (person_id, entity_id)
);
CREATE TABLE loyalty_event (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL REFERENCES loyalty_account(id) ON DELETE CASCADE,
  delta INTEGER NOT NULL, reason TEXT, ref TEXT,
  at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Item-level verified ratings. What the public page shows.
CREATE VIEW item_rating AS
SELECT r.subject_id AS menu_item_id,
       ROUND(AVG(r.rating), 1) AS rating,
       COUNT(*) AS verified_orders
  FROM review r
 WHERE r.subject_kind = 'menu_item' AND r.verified_by IS NOT NULL
 GROUP BY r.subject_id;

-- Open seats with someone to text about them.
CREATE VIEW fillable AS
SELECT a.slot_id, a.entity_id, a.starts_at, a.open_seats,
       w.person_id, w.qty AS wants
  FROM availability a
  JOIN waitlist w
    ON w.entity_id = a.entity_id
   AND (w.trip_id IS NULL OR w.trip_id = a.trip_id)
   AND a.starts_at BETWEEN COALESCE(w.wants_from, a.starts_at)
                       AND COALESCE(w.wants_to,   a.starts_at)
 WHERE a.open_seats > 0 AND w.notified_at IS NULL;
