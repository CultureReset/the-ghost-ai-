-- 0002 restaurant — menus, happy hour, tables, the QR loop
PRAGMA foreign_keys = ON;

CREATE TABLE menu (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  serves_from TEXT, serves_to TEXT
);
CREATE TABLE menu_section (
  id TEXT PRIMARY KEY,
  menu_id TEXT NOT NULL REFERENCES menu(id) ON DELETE CASCADE,
  name TEXT NOT NULL, sort INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE menu_item (
  id TEXT PRIMARY KEY,
  section_id TEXT NOT NULL REFERENCES menu_section(id) ON DELETE CASCADE,
  name TEXT NOT NULL, description TEXT,
  price_cents INTEGER, currency TEXT NOT NULL DEFAULT 'USD',
  available INTEGER NOT NULL DEFAULT 1,   -- 86'd = 0
  eightysixed_at TEXT,
  allergens TEXT, sort INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_item_section ON menu_item(section_id);

CREATE TABLE happy_hour (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  weekday INTEGER NOT NULL, starts TEXT NOT NULL, ends TEXT NOT NULL,
  CHECK (weekday BETWEEN 0 AND 6)
);
CREATE TABLE happy_hour_item (
  id TEXT PRIMARY KEY,
  happy_hour_id TEXT NOT NULL REFERENCES happy_hour(id) ON DELETE CASCADE,
  label TEXT NOT NULL, price_cents INTEGER
);

CREATE TABLE dining_table (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  label TEXT NOT NULL, seats INTEGER NOT NULL, qr_token TEXT UNIQUE
);

-- The loop: a scan at a table, at a time, joined to a closed ticket.
CREATE TABLE table_scan (
  id TEXT PRIMARY KEY,
  table_id TEXT NOT NULL REFERENCES dining_table(id) ON DELETE CASCADE,
  person_id TEXT REFERENCES person(id),
  scanned_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE ticket (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  table_id TEXT REFERENCES dining_table(id),
  scan_id TEXT REFERENCES table_scan(id),
  opened_at TEXT, closed_at TEXT, total_cents INTEGER,
  source_ref TEXT
);
CREATE TABLE ticket_line (
  id TEXT PRIMARY KEY,
  ticket_id TEXT NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
  menu_item_id TEXT REFERENCES menu_item(id),
  label TEXT NOT NULL, qty INTEGER NOT NULL DEFAULT 1, price_cents INTEGER
);
CREATE INDEX idx_line_item ON ticket_line(menu_item_id);
