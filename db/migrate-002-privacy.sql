-- Stop persisting a per-person network identifier alongside their name and email.
-- The old orders.ip_hash was a truncated SHA-256 of salt:ip, which a review recovered
-- from a known hash in 0.3 seconds on one CPU core: IPv4 is only 2^32 candidates and
-- there is no KDF. Rate limiting now lives in its own table and expires, so nothing
-- durable links a reservation to an address.

CREATE TABLE IF NOT EXISTS rate (
  hash TEXT NOT NULL,
  at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rate_hash ON rate (hash, at);
CREATE INDEX IF NOT EXISTS idx_rate_at   ON rate (at);

ALTER TABLE orders DROP COLUMN ip_hash;
