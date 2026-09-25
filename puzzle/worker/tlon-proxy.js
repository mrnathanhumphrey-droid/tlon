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

    // ⛔ HOP-BY-HOP HEADERS ARE NOT FORWARDED. A browser on HTTP/1.1 sends
    // `Connection: Keep-Alive`, and HTTP/2 — which the origin speaks — forbids
    // connection-specific headers (RFC 9113 §8.2.2). Ordinary proxy hygiene.
    //
    // ⛔⛤ I ADDED THIS CLAIMING IT WAS THE CAUSE OF A 400 AND IT WAS NOT. The
    // 400 survived it. The real cause was a malformed secret VALUE (below),
    // found by bisecting the headers rather than by reasoning about them. Kept
    // because it is correct, not because it fixed anything.
    for (const h of ["connection", "keep-alive", "proxy-connection",
                     "transfer-encoding", "upgrade", "te", "trailer"]) {
      headers.delete(h);
    }

    // ⛔⛔ The real reader, and the proof this Worker sent it.
    const ip = request.headers.get("CF-Connecting-IP");
    if (ip) headers.set("X-Tlon-Client-IP", ip);
    // ⛔⛔ TRIMMED, AND ONLY SENT IF IT IS A LEGAL HEADER VALUE. The secret
    // was once stored as a SINGLE non-printable character — a paste that did
    // not take — and an illegal header value makes the origin reject the whole
    // request with an empty 400 before any handler runs. That is indis-
    // tinguishable from the app being broken, and nothing in its logs mentions
    // it because the request never arrived. Refusing to send a malformed
    // secret degrades to "the client IP is not trusted", which is visible and
    // survivable, instead of taking the entire site down.
    const secret = (env.TLON_PROXY_SECRET || "").trim();
    if (secret && /^[!-~]+$/.test(secret)) {
      headers.set("X-Tlon-Proxy-Secret", secret);
    } else if (env.TLON_PROXY_SECRET) {
      console.log("TLON: refusing to send a malformed TLON_PROXY_SECRET " +
                  "(len=" + secret.length + ") — the per-IP limit will fall " +
                  "back to Cloudflare's egress address");
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

    // ⛔ THE CONTENT HEADERS GO. The Workers runtime transparently decompresses
    // a gzipped response body while `resp.headers` still declares
    // `content-encoding: gzip` and the COMPRESSED `content-length`; copying
    // those onto a now-plain body describes a response that no longer exists.
    //
    // ⛔⛤ I ALSO ADDED THIS CLAIMING IT CAUSED THE 400, AND IT DID NOT EITHER.
    // Two speculative fixes shipped before anyone asked the origin what it was
    // rejecting. A `console.log` of `resp.status` answered in one deploy what
    // three rounds of reasoning had not.
    out.delete("content-encoding");
    out.delete("content-length");
    out.delete("transfer-encoding");
    out.delete("content-range");

    // ⛔⛔⛔ SET-COOKIE IS THE ONE HEADER `new Headers(...)` CAN DESTROY.
    // A `Headers` object joins repeated fields with ", ", which is correct for
    // every header except this one: two cookies become one malformed value and
    // the browser stores NEITHER. `/say` returns exactly that pair the first
    // time a reader speaks — `tlon_bench` (their conversation) and `tlon_human`
    // (their pass) — so the failure would land on the very first turn of every
    // new reader, and it would present as the bench forgetting them: a fresh
    // conversation on every message, with nothing in any log to say why.
    // ⭐ `getSetCookie()` is the runtime's own accessor for exactly this, and
    // re-appending one at a time is the only way to keep them separate.
    if (typeof resp.headers.getSetCookie === "function") {
      const cookies = resp.headers.getSetCookie();
      if (cookies.length) {
        out.delete("set-cookie");
        for (const c of cookies) out.append("set-cookie", c);
      }
    }

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
