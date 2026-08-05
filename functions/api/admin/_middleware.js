// Auth for everything under /api/admin/. Pages runs _middleware before the route,
// so no admin handler can forget to check.
//
// The token is a Pages secret, never in the repo. If it is unset the whole admin
// surface returns 503 rather than falling open, because an admin API that is
// accidentally public is worse than one that is accidentally down.

// Digest both sides first: the comparison is then over two fixed 32-byte values, so
// it is length-independent by construction rather than by argument. The previous
// version looped to max(len) and its comment claimed a property it did not have.
async function tokenMatches(given, expected) {
  const enc = new TextEncoder();
  const [a, b] = await Promise.all([
    crypto.subtle.digest('SHA-256', enc.encode(given)),
    crypto.subtle.digest('SHA-256', enc.encode(expected)),
  ]);
  const x = new Uint8Array(a), y = new Uint8Array(b);
  let diff = 0;
  for (let i = 0; i < 32; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

const deny = (status, error) =>
  new Response(JSON.stringify({ error }), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      // a browser prompt here would be worse than the page's own token field
      'x-robots-tag': 'noindex',
    },
  });

export async function onRequest(context) {
  const { request, env, next } = context;

  if (!env.ADMIN_TOKEN) return deny(503, 'admin is not configured');

  const header = request.headers.get('authorization') || '';
  const token = header.replace(/^Bearer\s+/i, '');
  if (!token || !(await tokenMatches(token, env.ADMIN_TOKEN))) {
    return deny(401, 'unauthorized');
  }

  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set('cache-control', 'no-store');
  out.headers.set('x-robots-tag', 'noindex');
  return out;
}
