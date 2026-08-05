// POST /api/reserve
// Public. The client sends a configuration and contact details, never a price: the
// server recomputes every total, so a number arriving from a browser is a suggestion.

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

const LIVE = "status NOT IN ('cancelled', 'refunded')";
// Permissive by design: reject obvious typos, let a bounced reply catch the rest.
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const clean = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : null);

// Hashed, salted and truncated: enough to rate-limit a source, not enough to walk back
// to an address without the salt.
async function ipHash(request, salt) {
  const ip = request.headers.get('cf-connecting-ip') || '0.0.0.0';
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(salt), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(ip));
  return [...new Uint8Array(mac)].slice(0, 16)
    .map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);
  // Fail closed: an unset salt would otherwise mean a publicly known one.
  if (!env.IP_SALT) return json({ error: 'reservations are temporarily unavailable' }, 503);

  // Cross-site posts are rejected outright. This is the amplifier for every other
  // abuse path: without it the per-source limit is meaningless, because the sources
  // are other people's browsers.
  const site = request.headers.get('sec-fetch-site');
  if (site && site !== 'same-origin' && site !== 'none') {
    return json({ error: 'bad origin' }, 403);
  }
  const origin = request.headers.get('origin');
  if (origin) {
    try {
      if (new URL(origin).host !== new URL(request.url).host) {
        return json({ error: 'bad origin' }, 403);
      }
    } catch { return json({ error: 'bad origin' }, 403); }
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'expected JSON' }, 400);
  }

  const email = clean(body.email, 200);
  if (!email || !EMAIL.test(email)) {
    return json({ error: 'A valid email is required to hold a slot.' }, 400);
  }
  // No coercion: "2abc" used to become 2 and 3.9 became a 3-bench order.
  const int = (v) => (Number.isInteger(v) ? v : (typeof v === 'string' && /^\d{1,4}$/.test(v.trim()) ? parseInt(v, 10) : NaN));
  const benches = int(body.benches), fast = int(body.fast), slow = int(body.slow);

  try {
    const settings = await env.DB.prepare('SELECT key, value FROM settings').all();
    const s = {};
    for (const r of settings.results) s[r.key] = r.value;
    const num = (k, d) => { const v = parseInt(s[k], 10); return Number.isFinite(v) ? v : d; };
    const slots = num('slots_per_board', 10);
    const maxBenches = num('max_benches', 12);
    const batch = num('batch_size', 100);

    if (!Number.isFinite(benches) || benches < 1 || benches > maxBenches) {
      return json({ error: `Benches must be between 1 and ${maxBenches}.` }, 400);
    }
    if (![fast, slow].every((n) => Number.isFinite(n) && n >= 0 && n <= slots)) {
      return json({ error: `Module counts must be between 0 and ${slots}.` }, 400);
    }
    if (fast + slow > slots) {
      return json({ error: `A board has ${slots} slots; you configured ${fast + slow}.` }, 400);
    }
    if (s.reservations_open !== '1') {
      return json({ error: 'Reservations are closed. Email pooyamn@gmail.com for the next batch.' }, 409);
    }

    const hash = await ipHash(request, env.IP_SALT);
    await env.DB.prepare("DELETE FROM rate WHERE at < datetime('now', '-2 hours')").run();
    const [mine, everyone] = await Promise.all([
      env.DB.prepare("SELECT COUNT(*) AS n FROM rate WHERE hash = ? AND at > datetime('now', '-1 hour')").bind(hash).first(),
      env.DB.prepare("SELECT COUNT(*) AS n FROM rate WHERE at > datetime('now', '-1 hour')").first(),
    ]);
    if (mine && mine.n >= 5) {
      return json({ error: 'Too many reservations from this address. Email pooyamn@gmail.com and I will hold one by hand.' }, 429);
    }
    if (everyone && everyone.n >= 40) {
      return json({ error: 'Unusually busy right now. Email pooyamn@gmail.com and I will hold one by hand.' }, 429);
    }

    // One live reservation per address: a slot costs nothing to claim, so without
    // this one person can quietly take the batch.
    const dupe = await env.DB.prepare(
      `SELECT id FROM orders WHERE lower(email) = lower(?) AND ${LIVE}`).bind(email).first();
    if (dupe) {
      return json({ error: `You already hold ${dupe.id}. Email pooyamn@gmail.com to change it.` }, 409);
    }

    const prices = await env.DB.prepare('SELECT key, cents FROM pricing').all();
    const p = {};
    for (const r of prices.results) p[r.key] = r.cents;
    const hardware = ((p.base || 0) + fast * (p.fast || 0) + slow * (p.slow || 0)) * benches;
    const deposit = p.deposit || 0;
    const id = 'ORD-' + [...crypto.getRandomValues(new Uint8Array(8))]
      .map((x) => x.toString(16).padStart(2, '0')).join('').toUpperCase();

    // Capacity is checked inside the INSERT rather than before it, so two people
    // claiming the last board cannot both pass a check and both write.
    const res = await env.DB.prepare(
      `INSERT INTO orders (id, email, name, company, note, benches, fast, slow,
                           hardware_cents, deposit_cents, status)
       SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reserved'
       WHERE (SELECT COALESCE(SUM(benches), 0) FROM orders WHERE ${LIVE}) + ? <= ?`
    ).bind(id, email, clean(body.name, 120), clean(body.company, 120), clean(body.note, 2000),
           benches, fast, slow, hardware, deposit, benches, batch).run();

    if (!res.meta || res.meta.changes === 0) {
      const taken = await env.DB.prepare(
        `SELECT COALESCE(SUM(benches), 0) AS n FROM orders WHERE ${LIVE}`).first();
      const left = Math.max(0, batch - (taken ? taken.n : 0));
      return json({ error: left
        ? `Only ${left} board${left === 1 ? '' : 's'} left in the first batch.`
        : 'The first batch is fully reserved. Email pooyamn@gmail.com for the next one.' }, 409);
    }

    await env.DB.batch([
      env.DB.prepare('INSERT INTO order_events (order_id, event, detail) VALUES (?, ?, ?)')
        .bind(id, 'reserved', `${benches} bench(es), ${fast} fast, ${slow} slow`),
      env.DB.prepare('INSERT INTO rate (hash) VALUES (?)').bind(hash),
    ]);

    const after = await env.DB.prepare(
      `SELECT COALESCE(SUM(benches), 0) AS n FROM orders WHERE ${LIVE}`).first();

    return json({
      id, hardware_cents: hardware, deposit_cents: deposit,
      checkout_url: s.checkout_url || null,
      slots_left: Math.max(0, batch - (after ? after.n : 0)),
    }, 201);
  } catch {
    return json({ error: 'Could not record the reservation. Email pooyamn@gmail.com and I will hold it by hand.' }, 500);
  }
}
