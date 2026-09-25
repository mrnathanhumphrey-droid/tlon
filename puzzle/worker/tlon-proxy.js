/**
 * ⛔⛔ THE FRONT DOOR FOR tlon.resolveresearcher.com.
 *
 * Modal gates custom domains behind its Team plan ($250/mo), which is absurd
 * for a free puzzle. So this Worker sits on the family domain and proxies to
 * the `modal.run` URL. The reader only ever sees resolveresearcher.com; Modal
 * routes on its own hostname because THIS makes a fresh request to it.
 *
 * ⛔⛔ THE ONE THING THAT MUST NOT BE GOT WRONG IS THE CLIENT ADDRESS.
 * `puzzle/guard.py` limits 12 turns per IP per 10 minutes, and it reads the
 * LAST `X-Forwarded-For` entry — correct behind Fly, which appends the real
 * client last. Through Cloudflare -> Modal the last entry is CLOUDFLARE'S
 * egress address. Left alone, every reader on earth would share one identity,
 * the per-IP limit would silently become a second global limit, and nothing
 * would look wrong: it fails OPEN.
 *
 * ⛔ AND A BARE CUSTOM HEADER WOULD BE WORSE THAN NOTHING. The modal.run URL
 * stays publicly reachable, so anyone could send `X-Tlon-Client-IP` themselves
 * and mint a fresh identity per request — handing out unlimited per-IP budget
 * on a GPU. The header is therefore paired with a shared secret that only this
 * Worker and the Modal app know, compared in constant time on the far side.
 *
 * ⭐ `CF-Connecting-IP` is set BY Cloudflare and overwritten on every request,
 * so a client cannot forge it. That is why it is the source of truth here and
 * `X-Forwarded-For` is not.
 */

const ORIGIN = "https://mr-nathanhumphrey--tlon-bench-bench-web.modal.run";

export default {
  async fetch(request, env) {
    const inbound = new URL(request.url);
    const target = new URL(inbound.pathname + inbound.search, ORIGIN);

    const headers = new Headers(request.headers);

    // ⛔ DROP the inbound Host. `fetch()` sets it from the target URL, and a
    // stale `tlon.resolveresearcher.com` here makes Modal fail to route —
    // which presents as a 404 on a URL that plainly exists.
    headers.delete("host");

    // ⛔⛔ The real reader, and the proof this Worker sent it.
    const ip = request.headers.get("CF-Connecting-IP");
    if (ip) headers.set("X-Tlon-Client-IP", ip);
    if (env.TLON_PROXY_SECRET) {
      headers.set("X-Tlon-Proxy-Secret", env.TLON_PROXY_SECRET);
    }
    // ⭐ The app sets a `Secure` cookie and Turnstile checks the hostname the
    // token was minted for; both need to know the reader arrived over https on
    // the family domain, not over whatever this hop happens to use.
    headers.set("X-Forwarded-Proto", "https");
    headers.set("X-Forwarded-Host", inbound.host);

    const resp = await fetch(target, {
      method: request.method,
      headers,
      body: request.body,
      // ⛔ MANUAL. Following a redirect here would resolve it against the
      // modal.run origin and leak that hostname into the reader's address bar,
      // undoing the entire point of this Worker.
      redirect: "manual",
    });

    // ⛔ Rebuilt rather than returned as-is so the headers are mutable — an
    // immutable `Response` from `fetch` cannot have its Location rewritten.
    const out = new Headers(resp.headers);
    const loc = out.get("location");
    if (loc && loc.startsWith(ORIGIN)) {
      out.set("location", loc.replace(ORIGIN, `https://${inbound.host}`));
    }
    return new Response(resp.body, {
      status: resp.status,
      statusText: resp.statusText,
      headers: out,
    });
  },
};
