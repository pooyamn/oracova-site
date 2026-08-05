// GET /api/pricing
// Public. Everything the pre-order page needs to price a bench and to know whether the
// batch is still open. The page also ships these numbers hardcoded, so if the database
// is unreachable it degrades to a stale price rather than a blank where the total goes.

const json = (body, status = 200, maxAge = 0) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': maxAge ? `public, max-age=${maxAge}` : 'no-store',
    },
  });

// Cancelled and refunded reservations release their boards back to the batch.
export const LIVE = "status NOT IN ('cancelled', 'refunded')";

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);
  try {
    const [prices, settings, taken] = await Promise.all([
      env.DB.prepare('SELECT key, cents, label FROM pricing').all(),
      env.DB.prepare('SELECT key, value FROM settings').all(),
      // boards, not orders: an order for three benches takes three of the hundred
      env.DB.prepare(`SELECT COALESCE(SUM(benches), 0) AS n FROM orders WHERE ${LIVE}`).first(),
    ]);

    const p = {}, labels = {};
    for (const r of prices.results) { p[r.key] = r.cents; labels[r.key] = r.label; }
    const s = {};
    for (const r of settings.results) s[r.key] = r.value;
    const num = (k, d) => { const v = parseInt(s[k], 10); return Number.isFinite(v) ? v : d; };

    const batch = num('batch_size', 100);
    const claimed = taken ? taken.n : 0;
    const left = Math.max(0, batch - claimed);

    return json({
      prices: p, labels,
      slots_per_board: num('slots_per_board', 10),
      channels_per_module: num('channels_per_module', 4),
      max_benches: num('max_benches', 12),
      ship_window: s.ship_window || '',
      batch_size: batch,
      slots_taken: claimed,
      slots_left: left,
      open: s.reservations_open === '1' && left > 0,
    }, 200, 30);
  } catch {
    return json({ error: 'pricing unavailable' }, 500);
  }
}
