PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS episodes (
  id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  created_at TEXT NOT NULL,
  instruction TEXT,
  outcome TEXT,
  evidence_json TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS episodes_expiry_idx ON episodes(expires_at);
CREATE INDEX IF NOT EXISTS episodes_repo_idx ON episodes(repo, created_at);

CREATE TABLE IF NOT EXISTS candidates (
  id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  rule_text TEXT NOT NULL,
  rule_hash TEXT NOT NULL UNIQUE,
  score REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK(status IN ('pending','promoted','rejected','superseded')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS candidates_status_idx ON candidates(status, score, created_at);

CREATE TABLE IF NOT EXISTS rules (
  id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  rule_text TEXT NOT NULL,
  rule_hash TEXT NOT NULL UNIQUE,
  reuse_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS rules_repo_idx ON rules(repo, reuse_count, updated_at);
