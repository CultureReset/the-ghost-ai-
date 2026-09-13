-- 0004 marina — slips, rental inventory, dock services
PRAGMA foreign_keys = ON;

CREATE TABLE slip (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  label TEXT NOT NULL, length_ft INTEGER, beam_ft INTEGER, depth_ft REAL,
  power TEXT, monthly_cents INTEGER, nightly_cents INTEGER,
  status TEXT NOT NULL DEFAULT 'available',
  CHECK (status IN ('available','occupied','maintenance'))
);
CREATE TABLE slip_assignment (
  id TEXT PRIMARY KEY,
  slip_id TEXT NOT NULL REFERENCES slip(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  vessel_name TEXT, starts_on TEXT NOT NULL, ends_on TEXT
);
CREATE TABLE rental_inventory (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                  -- pontoon | jetski | kayak | paddleboard
  label TEXT NOT NULL, units INTEGER NOT NULL,
  hourly_cents INTEGER, half_day_cents INTEGER, full_day_cents INTEGER,
  active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE dock_service (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  name TEXT NOT NULL,                  -- fuel | pumpout | ice | bait | haulout
  price_cents INTEGER, unit TEXT, available INTEGER NOT NULL DEFAULT 1
);
