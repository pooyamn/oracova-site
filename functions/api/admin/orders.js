// /api/admin/orders   GET list, PATCH one. Auth is enforced by _middleware.js.

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

// A reservation moves forward through these, or leaves sideways. Anything else is
// rejected, so the status column cannot drift into free text.
const STATUS = ['reserved', 'paid', 'scoped', 'building', 'shipped', 'cancelled', 'refunded'];
const LIVE = "status NOT IN ('cancelled', 'refunded')";
// One projection, used by both handlers, so a PATCH response cannot return more
// than the list does.
const COLS = `id, created_at, updated_at, email, name, company, note,
              benches, fast, slow, hardware_cents, deposit_cents,
              status, stripe_ref, admin_note`;

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);

  const [rows, counts, setting, taken] = await Promise.all([
    env.DB.prepare(`SELECT ${COLS} FROM orders ORDER BY created_at DESC LIMIT 500`).all(),
    env.DB.prepare('SELECT status, COUNT(*) AS n FROM orders GROUP BY status').all(),
    env.DB.prepare("SELECT value FROM settings WHERE key = 'batch_size'").first(),
    // boards, not orders: an order for three benches takes three of the hundred
    env.DB.prepare(`SELECT COALESCE(SUM(benches), 0) AS n FROM orders WHERE ${LIVE}`).first(),
  ]);

  const byStatus = {};
  for (const r of counts.results) byStatus[r.status] = r.n;
  const batch = setting ? parseInt(setting.value, 10) : 100;
  const claimed = taken ? taken.n : 0;

  return json({
    orders: rows.results,
    by_status: byStatus,
    batch_size: batch,
    slots_taken: claimed,
    slots_left: Math.max(0, batch - claimed),
    statuses: STATUS,
  });
}

export async function onRequestPatch({ request, env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'expected JSON' }, 400);
  }

  const id = typeof body.id === 'string' ? body.id.trim().slice(0, 64) : '';
  if (!id) return json({ error: 'id is required' }, 400);

  const existing = await env.DB.prepare('SELECT id, status FROM orders WHERE id = ?')
    .bind(id).first();
  if (!existing) return json({ error: 'no such order' }, 404);

  // Column names are fixed literals; only values are ever bound from input.
  const sets = [], vals = [], events = [];
  if (body.status !== undefined) {
    if (!STATUS.includes(body.status)) {
      return json({ error: `status must be one of: ${STATUS.join(', ')}` }, 400);
    }
    if (body.status !== existing.status) {
      sets.push('status = ?'); vals.push(body.status);
      events.push(['status', `${existing.status} -> ${body.status}`]);
    }
  }
  if (body.admin_note !== undefined) {
    sets.push('admin_note = ?'); vals.push(String(body.admin_note).slice(0, 4000));
    events.push(['note', 'admin note updated']);
  }
  if (body.stripe_ref !== undefined) {
    sets.push('stripe_ref = ?'); vals.push(String(body.stripe_ref).slice(0, 200));
    events.push(['stripe', 'payment reference set']);
  }
  if (!sets.length) return json({ error: 'nothing to change' }, 400);

  sets.push("updated_at = datetime('now')");
  await env.DB.prepare(`UPDATE orders SET ${sets.join(', ')} WHERE id = ?`)
    .bind(...vals, id).run();

  if (events.length) {
    await env.DB.batch(events.map(([e, d]) =>
      env.DB.prepare('INSERT INTO order_events (order_id, event, detail) VALUES (?, ?, ?)')
        .bind(id, e, d)));
  }

  const updated = await env.DB.prepare(`SELECT ${COLS} FROM orders WHERE id = ?`)
    .bind(id).first();
  return json({ order: updated });
}

// A buyer asking to be forgotten should not need someone to hand-edit the database.
export async function onRequestDelete({ request, env }) {
  if (!env.DB) return json({ error: 'database not bound' }, 503);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'expected JSON' }, 400);
  }
  const id = typeof body.id === 'string' ? body.id.trim().slice(0, 64) : '';
  if (!id) return json({ error: 'id is required' }, 400);

  const res = await env.DB.prepare('DELETE FROM orders WHERE id = ?').bind(id).run();
  if (!res.meta || res.meta.changes === 0) return json({ error: 'no such order' }, 404);
  await env.DB.prepare('INSERT INTO order_events (order_id, event, detail) VALUES (?, ?, ?)')
    .bind(id, 'deleted', 'order erased at request').run();
  return json({ ok: true, deleted: id });
}
