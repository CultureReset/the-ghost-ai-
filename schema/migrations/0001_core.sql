-- A NEXT GENT — 0001 core
-- The industry-neutral centre. Every vertical builds on exactly this.
--
-- Two rules encoded here and nowhere else:
--   1. A business is a graph. `entity` is self-referencing; every node is
--      independently addressable and inherits from its parent unless it
--      overrides. There is no "one business = one row".
--   2. Nothing is overwritten. Facts arrive as `observation` rows with a
--      source and a timestamp. `canonical` is computed from them, never
--      written over the top of them. Provenance cannot be added later.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- entities

CREATE TABLE entity (
  id            TEXT PRIMARY KEY,
  parent_id     TEXT REFERENCES entity(id) ON DELETE RESTRICT,
  slug          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  kind          TEXT NOT NULL,        -- parent | location | operation | unit
  vertical      TEXT,                 -- restaurant | charter | marina | trades | artist | NULL
  status        TEXT NOT NULL DEFAULT 'active',
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (kind IN ('parent','location','operation','unit')),
  CHECK (id <> parent_id)
);
CREATE INDEX idx_entity_parent ON entity(parent_id);
CREATE INDEX idx_entity_vertical ON entity(vertical);

-- Walk a node to its root. Used by every inheritance lookup.
CREATE VIEW entity_ancestry AS
WITH RECURSIVE up(id, ancestor_id, depth) AS (
  SELECT id, id, 0 FROM entity
  UNION ALL
  SELECT u.id, e.parent_id, u.depth + 1
    FROM up u JOIN entity e ON e.id = u.ancestor_id
   WHERE e.parent_id IS NOT NULL
)
SELECT id, ancestor_id, depth FROM up;

-- ---------------------------------------------------------------- attributes

CREATE TABLE location (
  entity_id     TEXT PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE,
  line1         TEXT, line2 TEXT, city TEXT, region TEXT, postal TEXT, country TEXT,
  lat           REAL, lon REAL,
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE contact (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  channel       TEXT NOT NULL,        -- phone | sms | email | url | social
  label         TEXT,
  value         TEXT NOT NULL,
  is_primary    INTEGER NOT NULL DEFAULT 0,
  CHECK (channel IN ('phone','sms','email','url','social'))
);
CREATE INDEX idx_contact_entity ON contact(entity_id);

CREATE TABLE hours (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  weekday       INTEGER NOT NULL,     -- 0 = Sunday
  opens         TEXT,                 -- 'HH:MM', NULL = closed
  closes        TEXT,
  CHECK (weekday BETWEEN 0 AND 6)
);
CREATE UNIQUE INDEX idx_hours_unique ON hours(entity_id, weekday, opens);

-- Overrides a weekday for a date range. Holiday closings live here.
CREATE TABLE hours_exception (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  starts_on     TEXT NOT NULL,
  ends_on       TEXT NOT NULL,
  opens         TEXT,
  closes        TEXT,
  closed        INTEGER NOT NULL DEFAULT 0,
  note          TEXT
);
CREATE INDEX idx_hours_exc_entity ON hours_exception(entity_id, starts_on);

CREATE TABLE media (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  role          TEXT NOT NULL,        -- hero | gallery | logo | job_photo | menu_item
  uri           TEXT NOT NULL,
  alt           TEXT,
  captured_at   TEXT,
  sort          INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_media_entity ON media(entity_id, role);

CREATE TABLE policy (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,        -- cancellation | deposit | pets | age | weather
  body          TEXT NOT NULL
);

CREATE TABLE event (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  starts_at     TEXT NOT NULL,
  ends_at       TEXT,
  body          TEXT,
  recurs        TEXT
);
CREATE INDEX idx_event_entity ON event(entity_id, starts_at);

-- ---------------------------------------------------------------- people

CREATE TABLE person (
  id            TEXT PRIMARY KEY,
  kind          TEXT NOT NULL,        -- owner | employee | customer | agent
  display_name  TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (kind IN ('owner','employee','customer','agent'))
);

CREATE TABLE person_contact (
  id            TEXT PRIMARY KEY,
  person_id     TEXT NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  channel       TEXT NOT NULL,
  value         TEXT NOT NULL,
  verified_at   TEXT,
  consent       TEXT NOT NULL DEFAULT 'none',   -- none | transactional | marketing
  CHECK (consent IN ('none','transactional','marketing'))
);
CREATE INDEX idx_pcontact_value ON person_contact(channel, value);

CREATE TABLE membership (
  id            TEXT PRIMARY KEY,
  person_id     TEXT NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  role          TEXT NOT NULL,        -- owner | manager | staff
  UNIQUE (person_id, entity_id, role)
);

-- ---------------------------------------------------------------- provenance

-- Every fact the system learns, with where it came from. Append only.
CREATE TABLE observation (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  field         TEXT NOT NULL,        -- 'hours.friday.closes', 'price.half_day'
  value         TEXT,
  source        TEXT NOT NULL,        -- owner | email:fareharbor | android:toast | browser:google
  source_ref    TEXT,                 -- message id, run id, url
  device_id     TEXT,
  actor_id      TEXT REFERENCES person(id),
  observed_at   TEXT NOT NULL,
  recorded_at   TEXT NOT NULL DEFAULT (datetime('now')),
  confidence    REAL
);
CREATE INDEX idx_obs_lookup ON observation(entity_id, field, observed_at DESC);

-- The computed answer. Rebuildable from observation at any time.
CREATE TABLE canonical (
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  field         TEXT NOT NULL,
  value         TEXT,
  from_obs_id   TEXT REFERENCES observation(id),
  decided_at    TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (entity_id, field)
);

-- Per-field source ordering. Owner beats POS beats website beats social.
CREATE TABLE source_rank (
  field_class   TEXT NOT NULL,        -- 'hours' | 'price' | 'menu' | '*'
  source        TEXT NOT NULL,
  rank          INTEGER NOT NULL,
  PRIMARY KEY (field_class, source)
);

-- ---------------------------------------------------------------- consistency

-- What each external surface currently shows for a canonical field.
-- This table is CyberCheck.
CREATE TABLE surface_state (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  field         TEXT NOT NULL,
  surface       TEXT NOT NULL,        -- website | google | facebook | yelp | booking | own
  observed      TEXT,
  verdict       TEXT NOT NULL,        -- VERIFIED | CONTRADICTED | NOT_YET_VERIFIABLE
  checked_at    TEXT NOT NULL DEFAULT (datetime('now')),
  evidence_id   TEXT,
  CHECK (verdict IN ('VERIFIED','CONTRADICTED','NOT_YET_VERIFIABLE')),
  UNIQUE (entity_id, field, surface)
);
CREATE INDEX idx_surface_stale ON surface_state(checked_at);

CREATE VIEW consistency AS
SELECT c.entity_id, c.field, c.value AS canonical_value,
       s.surface, s.observed, s.verdict, s.checked_at,
       CAST(julianday('now') - julianday(s.checked_at) AS INTEGER) AS days_stale
  FROM canonical c
  LEFT JOIN surface_state s
    ON s.entity_id = c.entity_id AND s.field = c.field;

-- ---------------------------------------------------------------- actions

-- Two dimensions, never one. `lifecycle` says where it is;
-- `verification` says what actually happened. FINISHED alone means nothing.
CREATE TABLE action (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  capability    TEXT NOT NULL,
  args          TEXT NOT NULL,        -- JSON
  idempotency_key TEXT NOT NULL UNIQUE,
  requested_by  TEXT REFERENCES person(id),
  constitution_version TEXT,
  lifecycle     TEXT NOT NULL DEFAULT 'REQUESTED',
  verification  TEXT,
  surfaces_ok   INTEGER,
  surfaces_total INTEGER,
  requested_at  TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at   TEXT,
  CHECK (lifecycle IN ('REQUESTED','PLANNED','AWAITING_APPROVAL','EXECUTING','VERIFYING','FINISHED')),
  CHECK (verification IS NULL OR verification IN
        ('VERIFIED','PARTIALLY_VERIFIED','NOT_YET_VERIFIABLE','CONTRADICTED','FAILED')),
  -- a finished action must say what happened
  CHECK (lifecycle <> 'FINISHED' OR verification IS NOT NULL)
);
CREATE INDEX idx_action_entity ON action(entity_id, requested_at DESC);

-- Append-only. Request -> authority -> executor -> observation -> verdict.
CREATE TABLE ledger (
  id            TEXT PRIMARY KEY,
  action_id     TEXT NOT NULL REFERENCES action(id) ON DELETE RESTRICT,
  seq           INTEGER NOT NULL,
  at            TEXT NOT NULL DEFAULT (datetime('now')),
  stage         TEXT NOT NULL,
  executor      TEXT,                 -- android | browser | api | human
  detail        TEXT,                 -- JSON
  evidence_id   TEXT,
  UNIQUE (action_id, seq)
);

CREATE TABLE evidence (
  id            TEXT PRIMARY KEY,
  action_id     TEXT REFERENCES action(id) ON DELETE RESTRICT,
  kind          TEXT NOT NULL,        -- screenshot | dom | api_response | tree
  sha256        TEXT NOT NULL,
  uri           TEXT NOT NULL,
  captured_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------- maps

-- The learned procedure. app_version x map_version is the key, never app alone.
CREATE TABLE app_map (
  id            TEXT PRIMARY KEY,
  app           TEXT NOT NULL,        -- com.toasttab.consumer
  app_version   TEXT NOT NULL,
  map_version   INTEGER NOT NULL,
  capability    TEXT NOT NULL,
  executor      TEXT NOT NULL,
  fingerprint   TEXT NOT NULL,        -- JSON: elements that must be on screen first
  steps         TEXT NOT NULL,        -- JSON
  state         TEXT NOT NULL DEFAULT 'candidate',  -- candidate|canary|promoted|retired
  learned_from  TEXT,                 -- ai | human_takeover | recorded
  promoted_at   TEXT,
  UNIQUE (app, app_version, capability, map_version),
  CHECK (state IN ('candidate','canary','promoted','retired'))
);
CREATE INDEX idx_map_lookup ON app_map(capability, app, state);

CREATE TABLE map_run (
  id            TEXT PRIMARY KEY,
  map_id        TEXT NOT NULL REFERENCES app_map(id),
  action_id     TEXT REFERENCES action(id),
  outcome       TEXT NOT NULL,        -- OK | DRIFTED | FAILED | TOOK_OVER
  ms            INTEGER,
  at            TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (outcome IN ('OK','DRIFTED','FAILED','TOOK_OVER'))
);
CREATE INDEX idx_maprun_map ON map_run(map_id, at DESC);

-- ---------------------------------------------------------------- installs

CREATE TABLE app_install (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  vapp          TEXT NOT NULL,        -- io.anextgent.qr-menu
  version       TEXT NOT NULL,
  source_sha    TEXT NOT NULL,        -- full 40-char commit, never a tag
  settings      TEXT,                 -- JSON
  installed_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (entity_id, vapp)
);

CREATE TABLE grant_scope (
  id            TEXT PRIMARY KEY,
  install_id    TEXT NOT NULL REFERENCES app_install(id) ON DELETE CASCADE,
  capability    TEXT NOT NULL,
  mode          TEXT NOT NULL,        -- read | write
  risk          TEXT NOT NULL,        -- low | medium | high | critical
  granted_at    TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (mode IN ('read','write')),
  CHECK (risk IN ('low','medium','high','critical'))
);
