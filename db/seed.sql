-- Seed values confirmed with Pouya 2026-08-04. Editable from /admin afterwards;
-- this file only establishes the starting state of a fresh database.

INSERT INTO pricing (key, cents, label) VALUES
  ('base',          200000, 'Augur One base board'),
  ('fast',           10000, 'High-speed analog module'),
  ('slow',            5000, 'Medium-speed analog module'),
  ('deposit',        10000, 'Reservation deposit'),
  ('support_year',  100000, 'Support, per board per year after the first')
ON CONFLICT(key) DO NOTHING;

INSERT INTO settings (key, value) VALUES
  ('batch_size',          '100'),
  ('ship_window',         'Q1 2027'),
  ('slots_per_board',     '10'),
  ('channels_per_module', '4'),
  ('max_benches',         '12'),
  -- empty until the Stripe payment link exists; the reserve flow degrades to
  -- "we will email you a payment link", which works without it
  ('checkout_url',        ''),
  ('reservations_open',   '1')
ON CONFLICT(key) DO NOTHING;
