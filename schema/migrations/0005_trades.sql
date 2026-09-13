-- 0005 trades — electricians, plumbers, HVAC
PRAGMA foreign_keys = ON;

CREATE TABLE service_type (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  name TEXT NOT NULL, description TEXT,
  callout_cents INTEGER, hourly_cents INTEGER,
  emergency INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE service_area (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  postal TEXT, radius_mi REAL, center_lat REAL, center_lon REAL,
  surcharge_cents INTEGER
);
CREATE TABLE quote_request (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  service_type_id TEXT REFERENCES service_type(id),
  body TEXT, address TEXT, urgency TEXT NOT NULL DEFAULT 'normal',
  state TEXT NOT NULL DEFAULT 'new',
  received_at TEXT NOT NULL DEFAULT (datetime('now')),
  first_response_at TEXT,
  CHECK (urgency IN ('normal','soon','emergency')),
  CHECK (state IN ('new','quoted','scheduled','won','lost'))
);
CREATE INDEX idx_quote_state ON quote_request(entity_id, state, received_at DESC);

CREATE TABLE appointment (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  quote_id TEXT REFERENCES quote_request(id),
  person_id TEXT REFERENCES person(id),
  starts_at TEXT NOT NULL, ends_at TEXT,
  state TEXT NOT NULL DEFAULT 'scheduled',
  CHECK (state IN ('scheduled','enroute','done','cancelled'))
);
CREATE TABLE job_photo (
  id TEXT PRIMARY KEY,
  appointment_id TEXT NOT NULL REFERENCES appointment(id) ON DELETE CASCADE,
  media_id TEXT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
  phase TEXT NOT NULL,                 -- before | after
  CHECK (phase IN ('before','after'))
);
