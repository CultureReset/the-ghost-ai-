-- 0003 charter & tourism — trips, start times, capacity, availability
PRAGMA foreign_keys = ON;

CREATE TABLE vessel (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  name TEXT NOT NULL, length_ft INTEGER, capacity INTEGER NOT NULL,
  registration TEXT, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE charter_trip (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  name TEXT NOT NULL, duration_min INTEGER NOT NULL,
  vessel_id TEXT REFERENCES vessel(id),
  capacity INTEGER NOT NULL, description TEXT, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE start_time (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES charter_trip(id) ON DELETE CASCADE,
  weekday INTEGER NOT NULL, at TEXT NOT NULL,
  CHECK (weekday BETWEEN 0 AND 6)
);
CREATE TABLE pricing_tier (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES charter_trip(id) ON DELETE CASCADE,
  label TEXT NOT NULL,                 -- adult | child | private
  price_cents INTEGER NOT NULL, min_qty INTEGER, max_qty INTEGER,
  starts_on TEXT, ends_on TEXT         -- seasonal
);
CREATE TABLE addon (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES charter_trip(id) ON DELETE CASCADE,
  label TEXT NOT NULL, price_cents INTEGER NOT NULL, required INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE deposit_rule (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES charter_trip(id) ON DELETE CASCADE,
  amount_cents INTEGER, percent REAL, refundable_until_hours INTEGER
);
CREATE TABLE waiver (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  title TEXT NOT NULL, body TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE blackout (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  starts_at TEXT NOT NULL, ends_at TEXT NOT NULL, reason TEXT
);

-- Declared capacity per slot. Bookings decrement it; cancellations restore it.
CREATE TABLE slot (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  trip_id TEXT REFERENCES charter_trip(id),
  starts_at TEXT NOT NULL,
  capacity INTEGER NOT NULL,
  hold INTEGER NOT NULL DEFAULT 0,     -- safety slot against email lag
  UNIQUE (entity_id, trip_id, starts_at)
);
CREATE INDEX idx_slot_when ON slot(entity_id, starts_at);

-- One row per booking signal, whatever channel it arrived on.
CREATE TABLE booking (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  slot_id TEXT REFERENCES slot(id),
  channel TEXT NOT NULL,               -- fareharbor | peek | airbnb | vrbo | direct | walkin
  external_ref TEXT,
  person_id TEXT REFERENCES person(id),
  lead_id TEXT,                        -- set when reconciled, see 0006
  qty INTEGER NOT NULL DEFAULT 1,
  total_cents INTEGER,
  state TEXT NOT NULL DEFAULT 'confirmed',  -- confirmed | cancelled | noshow
  booked_at TEXT NOT NULL DEFAULT (datetime('now')),
  cancelled_at TEXT,
  source_ref TEXT,                     -- the email message id
  UNIQUE (channel, external_ref),
  CHECK (state IN ('confirmed','cancelled','noshow'))
);
CREATE INDEX idx_booking_slot ON booking(slot_id, state);

-- What the public page shows. Never stored — always computed.
CREATE VIEW availability AS
SELECT s.id AS slot_id, s.entity_id, s.trip_id, s.starts_at, s.capacity, s.hold,
       COALESCE(SUM(CASE WHEN b.state='confirmed' THEN b.qty END), 0) AS booked,
       s.capacity - s.hold
         - COALESCE(SUM(CASE WHEN b.state='confirmed' THEN b.qty END), 0) AS open_seats
  FROM slot s LEFT JOIN booking b ON b.slot_id = s.id
 GROUP BY s.id;
