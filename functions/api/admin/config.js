// /api/admin/config   GET prices and settings, PUT to change them.
// Auth is enforced by _middleware.js. Changing a price never rewrites an existing
// order: each reservation stores the total it was quoted.

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

const SETTING_KEYS = [
  'batch_size', 'ship_window', 'slots_per_board', 'channels_per_module',
  'max_benches', 'checkout_url', 'reservations_open',
];
// Ceilings, because the schema promises money never loses precision: an unbounded
// max_benches made a computed total exceed Number.MAX_SAFE_INTEGER.
const CAP = { batch_size: 10000, slots_per_board: 40, channels_per_module: 16, max_benches: 100 };

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);
  const [prices, settings] = await Promise.all([
    env.DB.prepare('SELECT key, cents, label, updated_at FROM pricing ORDER BY key').all(),
    env.DB.prepare('SELECT key, value, updated_at FROM settings ORDER BY key').all(),
  ]);
  return json({ prices: prices.results, settings: settings.results, setting_keys: SETTING_KEYS });
}

export async function onRequestPut({ request, env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'expected JSON' }, 400);
  }

  const changed = [];

  if (body.prices && typeof body.prices === 'object') {
    for (const [key, raw] of Object.entries(body.prices)) {
      const cents = Number(raw);
      if (!Number.isInteger(cents) || cents < 0 || cents > 100000000) {
        return json({ error: `price "${key}" must be a whole number of cents under $1,000,000` }, 400);
      }
      const exists = await env.DB.prepare('SELECT key FROM pricing WHERE key = ?').bind(key).first();
      if (!exists) return json({ error: `unknown price key "${key}"` }, 400);
      await env.DB.prepare("UPDATE pricing SET cents = ?, updated_at = datetime('now') WHERE key = ?")
        .bind(cents, key).run();
      changed.push(`${key}=${cents}`);
    }
  }

  if (body.settings && typeof body.settings === 'object') {
    for (const [key, raw] of Object.entries(body.settings)) {
      if (!SETTING_KEYS.includes(key)) return json({ error: `unknown setting "${key}"` }, 400);
      const value = String(raw).slice(0, 500);

      if (key === 'checkout_url' && value) {
        // Parse it, do not prefix-match it: a prefix check constrains eight
        // characters and lets anything follow, including an attribute breakout.
        let u;
        try { u = new URL(value); } catch { return json({ error: 'checkout_url must be a URL' }, 400); }
        if (u.protocol !== 'https:') return json({ error: 'checkout_url must be https' }, 400);
        if (/["'<>\s]/.test(value)) return json({ error: 'checkout_url contains illegal characters' }, 400);
      }
      if (key in CAP) {
        if (!/^\d+$/.test(value)) return json({ error: `${key} must be a whole number` }, 400);
        const n = parseInt(value, 10);
        if (n < 1 || n > CAP[key]) {
          return json({ error: `${key} must be between 1 and ${CAP[key]}` }, 400);
        }
      }
      if (key === 'reservations_open' && value !== '0' && value !== '1') {
        return json({ error: 'reservations_open must be 0 or 1' }, 400);
      }

      await env.DB.prepare("UPDATE settings SET value = ?, updated_at = datetime('now') WHERE key = ?")
        .bind(value, key).run();
      changed.push(`${key}=${value}`);
    }
  }

  if (!changed.length) return json({ error: 'nothing to change' }, 400);

  await env.DB.prepare("INSERT INTO order_events (order_id, event, detail) VALUES ('-', 'config', ?)")
    .bind(changed.join(' ')).run();

  return json({ ok: true, changed });
}
