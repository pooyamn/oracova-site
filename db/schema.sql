-- Oracova pre-order backend, D1 schema.
-- Prices live here, never in the page, so a change is one UPDATE and not a deploy.
-- Money is stored in integer cents. Never floats: a price that reads $2,000.00 on the
-- page and 1999.9999 in a sum is the exact class of bug this site's copy rules ban.

CREATE TABLE IF NOT EXISTS pricing (
  key        TEXT PRIMARY KEY,
  cents      INTEGER NOT NULL CHECK (cents >= 0),
  label      TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id             TEXT PRIMARY KEY,
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  email          TEXT NOT NULL,
  name           TEXT,
  company        TEXT,
  note           TEXT,
  benches        INTEGER NOT NULL CHECK (benches >= 1),
  fast           INTEGER NOT NULL CHECK (fast >= 0),
  slow           INTEGER NOT NULL CHECK (slow >= 0),
  -- the price the server computed at reservation time, so a later price change
  -- never silently rewrites what someone was quoted
  hardware_cents INTEGER NOT NULL,
  deposit_cents  INTEGER NOT NULL,
  status         TEXT NOT NULL DEFAULT 'reserved',
  stripe_ref     TEXT,
  admin_note     TEXT,
  ip_hash        TEXT,
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orders_created ON orders (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status  ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_iphash  ON orders (ip_hash, created_at);

-- One row per audited change, so "why is this order marked paid" always has an answer.
CREATE TABLE IF NOT EXISTS order_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id   TEXT NOT NULL,
  at         TEXT NOT NULL DEFAULT (datetime('now')),
  event      TEXT NOT NULL,
  detail     TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_order ON order_events (order_id, at DESC);
