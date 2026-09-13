-- 0007 constitution — standing authority, set per business, versioned
--
-- Approval policy was a set literal in the API. That meant every business on
-- every box had the same answer to "does a person have to say yes", and the
-- only way to change it was to ship code. It is a customer setting, so it
-- lives with the customer.
PRAGMA foreign_keys = ON;

CREATE TABLE constitution (
  id            TEXT PRIMARY KEY,
  entity_id     TEXT REFERENCES entity(id) ON DELETE CASCADE,  -- NULL = platform default
  version       INTEGER NOT NULL,
  active        INTEGER NOT NULL DEFAULT 1,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  note          TEXT,
  UNIQUE (entity_id, version)
);

-- One rule: for this risk level (or this exact capability), what happens.
CREATE TABLE constitution_rule (
  id              TEXT PRIMARY KEY,
  constitution_id TEXT NOT NULL REFERENCES constitution(id) ON DELETE CASCADE,
  capability      TEXT,          -- NULL = applies to a whole risk tier
  risk            TEXT,          -- NULL = applies to the named capability
  decision        TEXT NOT NULL, -- auto | notify | hold | deny
  CHECK (decision IN ('auto','notify','hold','deny')),
  CHECK (capability IS NOT NULL OR risk IS NOT NULL)
);
CREATE INDEX idx_crule_lookup ON constitution_rule(constitution_id, capability, risk);

-- Most specific wins: a rule naming the capability beats a rule naming the
-- tier, and the business's own constitution beats the platform default.
CREATE VIEW authority AS
SELECT c.entity_id, r.capability, r.risk, r.decision, c.version,
       CASE WHEN r.capability IS NOT NULL THEN 0 ELSE 1 END AS specificity
  FROM constitution c
  JOIN constitution_rule r ON r.constitution_id = c.id
 WHERE c.active = 1;

-- Platform defaults. A business overrides any of these without touching code.
INSERT INTO constitution(id, entity_id, version, note)
VALUES ('cn_default', NULL, 1, 'Platform default');
INSERT INTO constitution_rule(id, constitution_id, risk, decision) VALUES
 ('cr_low',      'cn_default', 'low',      'auto'),
 ('cr_medium',   'cn_default', 'medium',   'notify'),
 ('cr_high',     'cn_default', 'high',     'hold'),
 ('cr_critical', 'cn_default', 'critical', 'hold');
