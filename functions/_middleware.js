// One canonical host. Cloudflare Pages' _redirects cannot match on hostname,
// so the www 301 lives here instead. Everything else passes straight through.
export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === 'www.oracova.com') {
    url.hostname = 'oracova.com';
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
