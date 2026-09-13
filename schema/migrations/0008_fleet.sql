-- 0008 fleet — what is out there, what version it is on, and whether it is well
--
-- The missing half of the Red Hat structure. Content was pullable; nothing
-- recorded which box pulled what. Without this the admin console can show a
-- drift queue but not who is affected by it.
PRAGMA foreign_keys = ON;

CREATE TABLE device (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT REFERENCES entity(id) ON DELETE SET NULL,
  label         TEXT,
  kind          TEXT NOT NULL DEFAULT 'box',   -- box | handset
  serial        TEXT UNIQUE,
  os_version    TEXT,
  channel       TEXT NOT NULL DEFAULT 'stable',
  enrolled_at   TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT,
  health        TEXT NOT NULL DEFAULT 'unknown',  -- ok | degraded | down | unknown
  CHECK (kind IN ('box','handset')),
  CHECK (health IN ('ok','degraded','down','unknown'))
);
CREATE INDEX idx_device_entity ON device(entity_id);

-- Which content bundle a box is actually running. One row per kind.
CREATE TABLE device_content (
  device_id     TEXT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,                 -- contracts | appmaps | vendormaps
  version       TEXT NOT NULL,
  sha256        TEXT,
  applied_at    TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (device_id, kind)
);

CREATE TABLE heartbeat (
  id            TEXT PRIMARY KEY,
  device_id     TEXT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
  at            TEXT NOT NULL DEFAULT (datetime('now')),
  health        TEXT NOT NULL,
  detail        TEXT
);
CREATE INDEX idx_hb_device ON heartbeat(device_id, at DESC);

-- A drift needing a human: an app or a vendor changed and something refused to
-- act. One row per (what changed), not per occurrence — the console needs a
-- queue of work, not a log.
CREATE TABLE drift (
  id            TEXT PRIMARY KEY,
  kind          TEXT NOT NULL,                 -- appmap | vendormap
  subject       TEXT NOT NULL,                 -- package name or vendor
  capability    TEXT,
  expected      TEXT,                          -- app_version the map was written for
  seen          TEXT,                          -- what is actually out there
  detail        TEXT,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT NOT NULL DEFAULT (datetime('now')),
  occurrences   INTEGER NOT NULL DEFAULT 1,
  state         TEXT NOT NULL DEFAULT 'open',  -- open | mapping | fixed
  fixed_version INTEGER,
  UNIQUE (kind, subject, capability, seen),
  CHECK (state IN ('open','mapping','fixed'))
);
CREATE INDEX idx_drift_open ON drift(state, last_seen_at DESC);

-- How many businesses a drift is actually costing, computed rather than stored.
--
-- Two different questions wearing one name. An appmap drift costs whoever tried
-- to run that capability on that app and got refused; a vendormap drift costs
-- whoever takes bookings through that channel. Counting them the same way would
-- put one global number on every row, which is a number nobody can act on.
CREATE VIEW drift_impact AS
SELECT d.id, d.kind, d.subject, d.capability, d.expected, d.seen,
       d.occurrences, d.state, d.first_seen_at, d.last_seen_at,
       CASE d.kind
         WHEN 'appmap' THEN
           (SELECT COUNT(DISTINCT a.entity_id)
              FROM map_run mr
              JOIN app_map m ON m.id = mr.map_id
              JOIN action  a ON a.id = mr.action_id
             WHERE mr.outcome = 'DRIFTED'
               AND m.app = d.subject
               AND (d.capability IS NULL OR m.capability = d.capability))
         ELSE
           (SELECT COUNT(DISTINCT b.entity_id)
              FROM booking b WHERE b.channel = d.subject)
       END AS businesses_affected
  FROM drift d;
