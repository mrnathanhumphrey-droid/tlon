/* THE BENCH — post and render. Deliberately small and deliberately dumb.
 *
 * ⛔⛔ NOTHING THE MODEL PRODUCED EVER TOUCHES innerHTML. Every Tlön surface,
 * gloss and literary render is written with textContent, and the message
 * markup is cloned from a <template> rather than assembled from a string. The
 * Oracle ships marked + DOMPurify because it renders model-authored markdown;
 * this app renders plain text, so the safe thing is to not have the capability
 * at all rather than to sanitise it afterwards.
 *
 * ⛔ THE TRANSLATION IS NOT IN THE PAGE UNTIL IT IS ASKED FOR. /say returns the
 * Tlön and nothing else; /reveal is a separate request. If the gloss rode along
 * with the reply it would sit in the network tab of every reader who never
 * pressed the button and the puzzle would be decorative.
 */
(function () {
  "use strict";

  var log = document.getElementById("chat-log");
  var empty = document.getElementById("chat-empty");
  var form = document.getElementById("ask-form");
  var input = document.getElementById("ask-input");
  var send = document.getElementById("ask-send");
  var note = document.getElementById("ask-note");
  var newThread = document.getElementById("new-thread");
  var tpl = document.getElementById("tpl-msg");
  var busy = false;

  function say(text, kind) {
    note.textContent = text || "";
    note.className = "ask-note" + (kind ? " " + kind : "");
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) {
        if (!r.ok) {
          var err = new Error(data.error || ("request failed (" + r.status + ")"));
          err.status = r.status;
          /* ⛔ The server names WHICH check failed (`no turnstile token`,
             `invalid-input-response`, `invalid-input-secret`…). Dropping it
             here is what made every Turnstile failure present as the same
             unactionable sentence. */
          err.turnstile = data.turnstile || "";
          throw err;
        }
        return data;
      });
    });
  }

  /* ════════════════════════════════════════════════════════════════════════
     THE GATE.

     ⛔⛔⛔ THE DESIGN ERROR, AND EVERY SYMPTOM CAME FROM IT. The first three
     builds verified a Turnstile token on EVERY message. A Turnstile token is
     SINGLE-USE, so that means a fresh challenge per message: the widget had to
     be re-armed after each turn, and there was no state in which it was
     "done". Nate tried it three times and said, in order: it activates every
     time I send · it isn't visible but it's blocking me · it hasn't cleared
     yet, it's either invisible or permanent.

     ⭐⭐ ALL THREE ARE ONE BUG: A DOOR WAS BEING USED AS A TICKET INSPECTOR.
     `/verify` now exchanges one solved challenge for a signed, IP-bound,
     httponly session pass, and every later message rides it. The widget is
     shown at most ONCE and then removed from the document. That is what every
     site using Turnstile actually does, and it is why nobody else's captcha
     "won't clear".

     ⛔ THE CARD IS ALWAYS RENDERED, PARKED OFF-SCREEN. Turnstile will not draw
     into a `display:none` subtree, so hiding the gate the obvious way produces
     a challenge that never appears — which is exactly the "invisible" failure
     already shipped once. Parked, Cloudflare solves it silently for most
     readers and the gate is never raised at all.
     ════════════════════════════════════════════════════════════════════════ */

  var tsGate = document.getElementById("ts-gate");
  var tsGateNote = document.getElementById("ts-gate-note");
  var tsHost = document.getElementById("ts-widget");
  /* ⛔ The key is read from the attribute the SERVER substituted, so "no key
     configured" is one fact in one place. When it is absent the server's
     `turnstile.required()` is false as well — the two agree because both read
     the same absence, not because someone kept them in step. */
  var tsKey = tsHost ? (tsHost.getAttribute("data-sitekey") || "").trim() : "";
  var tsId = null;
  var human = false;            /* the server's answer, never a guess */
  var queued = null;            /* a message typed before the gate was passed */

  function gateSay(text, bad) {
    if (!tsGateNote) return;
    tsGateNote.textContent = text || "";
    tsGateNote.className = "ts-gate-note" + (bad ? " bad" : "");
  }

  function gateOpen() {
    if (human || !tsGate) return;
    tsGate.classList.add("is-open");
    tsGate.setAttribute("aria-hidden", "false");
    /* ⭐ The page behind a modal does not scroll. Without this the reader can
       drift the bench away underneath the card and come back to a view that
       looks like the check broke the layout. */
    document.body.style.overflow = "hidden";
  }

  /* ⛔⛔ DONE MEANS GONE. Not hidden, not reset, not parked for later — the
     whole complaint was a challenge that kept coming back, so once the pass is
     granted the gate leaves the document and nothing in this file can raise it
     again. */
  function gateDone() {
    human = true;
    document.body.style.overflow = "";
    if (!tsGate) return;
    tsGate.classList.remove("is-open");
    tsGate.classList.add("is-done");
    tsGate.setAttribute("aria-hidden", "true");
  }

  /* ⛔ NOT `onload=` ALONE, AND NOT A POLL FOR `window.turnstile` EITHER.
     The global appears BEFORE the library is usable: rendering on its mere
     existence returned a widget id, reserved the box, and drew no iframe and
     fired no callback. Cloudflare's readiness signal under `async defer` is
     the `?onload=` callback, parked by the inline block in the page head.
     ⛔ `turnstile.ready()` is NOT usable here — it THROWS when api.js carries
     async or defer, which is how this page loads it, and that throw is what
     silently prevented any render at all. */
  function whenTurnstile(cb) {
    if (window.__tlonTurnstileReady) { cb(); return; }
    window.__tlonOnTurnstile = cb;
    var tries = 0;
    var iv = setInterval(function () {
      if (window.__tlonTurnstileReady) {
        clearInterval(iv);
      } else if (++tries > 75) {                       /* 15s */
        clearInterval(iv);
        gateOpen();
        gateSay("the check could not load — an extension or your network may "
                + "be blocking challenges.cloudflare.com", true);
      }
    }, 200);
  }

  /* ⛔⛔⛔ THE SPIN. A failed /verify used to reset the widget, the widget
     auto-solved, that fired this again, /verify failed again, and round it
     went — forever, with the gate spinning and "HTTPError" flashing. An
     unbounded retry on a failure that is NOT transient is not resilience, it
     is a loop. The failure here was a misconfigured server key: no number of
     retries could ever have fixed it, and every one of them cost a siteverify
     round-trip.
     ⭐ Two attempts, then stop and SAY SO. A reader must be told the bench is
     broken rather than watched a spinner lie to them. */
  var tsTries = 0;
  var TS_MAX_TRIES = 2;

  /* One solved challenge, exchanged for a pass. */
  function tsPassed(token) {
    gateSay("");
    tsTries += 1;
    post("/verify", { turnstile: token })
      .then(function () {
        gateDone();
        /* ⭐ If they pressed send while the gate was up, finish the job for
           them. Making someone retype a sentence they already wrote because a
           captcha interrupted them is the kind of small insult that reads as
           the whole site being broken. */
        if (queued) {
          var q = queued;
          queued = null;
          submit(q);
        }
      })
      .catch(function (e) {
        gateOpen();
        /* ⛔⛔ NAME THE FAULT THE READER CANNOT FIX. `invalid-input-secret`
           means the SERVER's key is wrong: nobody will ever get through, and
           telling them to try again is a lie that wastes their afternoon. It
           is the single most important code Cloudflare returns and it was
           being swallowed twice over — once by the client discarding the
           reason, once by the server reporting a 400 as "unreachable". */
        var why = e.turnstile || "";
        if (why.indexOf("invalid-input-secret") !== -1) {
          gateSay("this bench is misconfigured on our side — nothing you can "
                  + "do will clear this. it has been reported.", true);
          return;                        /* ⛔ and DO NOT retry. Ever. */
        }
        if (tsTries >= TS_MAX_TRIES) {
          gateSay("the check keeps failing"
                  + (why ? " (" + why + ")" : "")
                  + " — try reloading, or come back later", true);
          return;
        }
        gateSay(why ? "that did not verify (" + why + ") — trying once more"
                    : "that did not verify — trying once more", true);
        /* ⛔ A refused token is spent. Re-arm so the reader has something to
           press rather than a dead widget — but only within the cap above. */
        try { window.turnstile.reset(tsId); } catch (err) { /* nothing to do */ }
      });
  }

  function tsBoot() {
    if (!tsKey || human) return;         /* local dev, or already through */
    whenTurnstile(function () {
      try {
        tsId = window.turnstile.render(tsHost, {
          sitekey: tsKey,
          action: "turnstile-spin-v1",
          /* ⛔ NOT "auto". "auto" follows the OPERATING SYSTEM, which is how a
             white slab ended up on this dark page. The family's theme lives in
             `rr_theme` and on <html data-theme>, and the widget follows THAT. */
          theme: document.documentElement.getAttribute("data-theme") === "light"
            ? "light" : "dark",
          /* ⛔⛔ NEVER "flexible". That is what stretched the widget to the
             full width of the composer and made it read as part of it. */
          size: "normal",
          callback: tsPassed,
          /* ⛔ Returning true keeps the widget alive so a retry is possible.
             Returning false hands control to Turnstile, which is what once
             left the page with a hole in it and no way back. */
          "error-callback": function (code) {
            gateOpen();
            gateSay("that did not pass"
                    + (code ? " (cloudflare said " + code + ")" : "")
                    + " — press it again", true);
            return true;
          },
          /* ⭐ Only meaningful BEFORE the pass exists; after `gateDone` the
             gate is out of the document and these can no longer fire. */
          "expired-callback": function () {
            try { window.turnstile.reset(tsId); } catch (e) { /* gone */ }
          },
          "timeout-callback": function () {
            try { window.turnstile.reset(tsId); } catch (e) { /* gone */ }
          }
        });
        tsWatch();
      } catch (e) {
        gateOpen();
        gateSay("the check could not start — try reloading", true);
      }
    });
  }

  /* ⛔⛔⛔ DO NOT LOOK FOR AN IFRAME. I WROTE THAT TWICE AND IT WAS MEASURING
     NOTHING.

     Turnstile builds its widget inside a CLOSED shadow root. `querySelector`
     cannot pierce one and `el.shadowRoot` reports `null` for one, so a check
     for an iframe returns "absent" for a widget that is drawn, interactive and
     sitting on screen — which I then reported as "the challenge never drew",
     twice, including to Nate. A watchdog built on that signal shows a red
     "your network is blocking this" to readers whose check is working fine:
     worse than no watchdog, because it teaches them to distrust a working
     page.

     ⭐⭐ THE HONEST SIGNAL IS THAT `render()` RAN AT ALL, and it has one
     observable in the light DOM: Turnstile inserts the hidden
     `cf-turnstile-response` input as part of rendering. Present means the
     library ran; absent means it did not — which is the REAL failure this
     page actually shipped, when `turnstile.ready()` threw under `async defer`
     and the render was silently skipped. That one is worth reporting, and it
     is the only one this can honestly detect. */
  function tsRendered() {
    return !!tsHost.querySelector("input[name='cf-turnstile-response']")
        && tsHost.getBoundingClientRect().height > 0;
  }

  function tsWatch() {
    var waited = 0;
    var iv = setInterval(function () {
      if (human) { clearInterval(iv); return; }
      waited += 400;
      var up = tsRendered();
      /* ⭐ 1.6s of grace before raising anything. A managed widget often
         settles in well under a second, and for those readers the gate must
         never flash on screen at all. */
      if (waited >= 1600 && up) {
        gateOpen();
      }
      if (waited >= 12000 && !up) {
        gateOpen();
        gateSay("the check did not load — an extension or your network may be "
                + "blocking challenges.cloudflare.com", true);
      } else if (up && waited > 12000) {
        /* ⛔ AND IT TAKES ITS OWN WARNING BACK. A reader on a slow connection
           whose widget arrives late must not be left reading a sentence that
           says the page is broken. */
        if (tsGateNote.textContent.indexOf("did not load") !== -1) gateSay("");
      }
      if (waited >= 40000) { clearInterval(iv); }
    }, 400);
  }

  /* One message. `row` is {turn, role, english, surface, let_go, refused}. */
  function render(row) {
    var node = tpl.content.firstElementChild.cloneNode(true);
    node.classList.add(row.role === "you" ? "msg-you" : "msg-tlon");
    node.dataset.turn = row.turn;
    node.dataset.role = row.role;

    /* ⛔⛔⛔ THE READER'S BUBBLE CARRIES THE READER'S OWN ENGLISH, AND NEVER
       THE TLÖN OF IT. Their sentence rendered into Tlön, shown to the person
       who just typed the English, is an aligned pair — the exact leak every
       comment in this file warns about, assembled from the one field nobody
       guarded because it looked like Tlön rather than like English.
       ⭐ Their own words tell them nothing they did not already know. The
       PAIRING was always the secret, not the English. */
    var text = node.querySelector(".msg-text");
    if (row.role === "you") {
      /* ⛔ `row.surface` is not read here and the server no longer sends it
         for this role. Two independent refusals, because one of them has
         already been quietly wrong for months. */
      text.textContent = row.english || row.refused || "…";
      if (!row.english) node.classList.add("msg-refused");
      log.appendChild(node);
      node.querySelector(".reveal-wrap").remove();
      return node;
    }
    if (row.surface) {
      text.textContent = row.surface;
    } else {
      /* ⛔ A refusal is the language working, not an error — it is shown as an
         outcome with its reason, never swallowed into a retry. */
      node.classList.add("msg-refused");
      text.textContent = row.refused || "it could not hold that";
    }

    /* ⛔⛔ THE TRANSLATE BUTTON EXISTS ON THE TLÖNIAN'S LINES AND NOWHERE ELSE.
       We never translate the user: they wrote it, so there is nothing to
       reveal, and returning its English would be an aligned pair — the
       parallel-text leak, asked for politely. The server enforces this too
       (/reveal accepts role "tlon" only); this is the half a reader sees. */
    var wrap = node.querySelector(".reveal-wrap");
    if (!row.surface || row.role !== "tlon") {
      wrap.remove();
    } else {
      wrap.querySelector(".reveal-btn").addEventListener("click", function () {
        onReveal(node, row);
      });
    }
    log.appendChild(node);
    return node;
  }

  function onReveal(node, row) {
    var body = node.querySelector(".reveal-body");
    var btn = node.querySelector(".reveal-btn");
    var label = node.querySelector(".reveal-label");
    if (node.dataset.revealed === "1") {          /* a toggle, not a one-way door */
      body.hidden = !body.hidden;
      label.textContent = body.hidden ? "translate" : "hide";
      return;
    }
    btn.disabled = true;
    post("/reveal", { turn: Number(row.turn), role: row.role })
      .then(function (data) {
        node.querySelector(".reveal-literary").textContent = data.literary || "";
        node.querySelector(".reveal-gloss").textContent = data.gloss || "";
        node.dataset.revealed = "1";
        body.hidden = false;
        label.textContent = "hide";
      })
      .catch(function (e) { say(e.message, "bad"); })
      .then(function () { btn.disabled = false; });
  }

  function renderAll(messages) {
    log.querySelectorAll(".msg").forEach(function (n) { n.remove(); });
    (messages || []).forEach(render);
    var any = (messages || []).length > 0;
    if (empty) empty.hidden = any;
    newThread.hidden = !any;
    if (any) log.scrollTop = log.scrollHeight;
  }

  /* ⛔⛔ ONE PLACE THAT SENDS. The gate may finish AFTER the reader pressed
     send, and when it does it has to be able to complete the turn they already
     asked for. Two copies of this logic would drift; there is one. */
  function submit(english) {
    busy = true;
    send.disabled = true;
    input.value = "";
    /* ⭐ NATE'S WORDING, AND IT IS THE PAGE'S ONLY LINE OF TLÖN-SHAPED ENGLISH.
       "it is thinking" gives the speaker a persisting self that does a thing.
       "the thinking happens" is the happening without the thinker — which is
       the grammar the whole language is built on, said in English. */
    say("the thinking happens…", "wait");
    /* ⛔ THE EMPTY STATE IS NOT TAKEN AWAY UNTIL THERE IS SOMETHING TO PUT
       IN ITS PLACE. This used to hide on submit, so a turn that was refused —
       a rate limit, a failed check, a cold start — left the reader looking
       at an empty box with no way back short of a reload. */
    post("/say", { english: english })
      .then(function (data) {
        if (empty) empty.hidden = true;
        (data.messages || []).forEach(render);
        newThread.hidden = false;
        log.scrollTop = log.scrollHeight;
        say("");
      })
      .catch(function (e) {
        /* ⛔ Put the text back. Losing what someone typed to a rate limit
           is a second punishment for the same thing. */
        input.value = english;
        if (e.status === 403) {
          /* ⛔⛔ THE PASS EXPIRED OR WAS NEVER GRANTED. Raise the gate
             rather than printing a sentence about not being a person that
             names nothing to press — which is exactly what Nate was handed
             three times. ⛐ The message is kept so the next attempt sends
             itself once the gate clears. */
          queued = english;
          human = false;
          if (tsGate) { tsGate.classList.remove("is-done"); }
          gateOpen();
          gateSay(e.turnstile ? "cloudflare said: " + e.turnstile : "", true);
          say("", "");
          try { window.turnstile.reset(tsId); } catch (err) { /* not booted */ }
          tsBoot();
        } else {
          say(e.message, "bad");
        }
      })
      .then(function () {
        busy = false;
        send.disabled = false;
        input.focus();
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (busy) return;
    var english = input.value.trim();
    if (!english) return;

    /* ⛔⛔ IF THE GATE HAS NOT BEEN PASSED, HOLD THE MESSAGE — DO
       NOT SPEND IT. Firing /say without a pass buys a 403 whose wording names
       nothing the reader can do. Raising the gate and sending the moment it
       clears is the difference between a check and an obstacle. */
    if (tsKey && !human) {
      queued = english;
      input.value = "";
      gateOpen();
      say("", "");
      return;
    }
    submit(english);
  });

  newThread.addEventListener("click", function () {
    post("/new").then(function () {
      renderAll([]);
      say("");
      input.focus();
    }).catch(function (e) { say(e.message, "bad"); });
  });

  /* ⛔⛔ THE EXAMPLE HANDLER IS GONE, AND NOTHING MAY PUT IT BACK. Suggested
     lines were removed because a reader who presses a known English sentence
     and reads the Tlön that returns is holding an aligned pair before they
     have decoded anything — the parallel-text leak the reply template warns
     about, arriving first and unasked. `data-q` is therefore a dead attribute
     in this app; if one ever reappears in the markup, nothing here will fill
     the composer from it. */

  /* ⛔ THE PLACEHOLDER-VIDEO HANDLER IS GONE WITH THE VIDEOS. Four <video>
     elements pointed at paths with nothing behind them; all four 404'd on
     every load, apex's chrome injected a big play button over each one, and
     the fallback only half-fired — the figures got their dashed box while the
     players kept their controls in the accessibility tree. Nothing to hide is
     better than a hide that works most of the time. */

  /* ⛔⛔ THE SERVER SAYS WHETHER THE GATE IS NEEDED; THE PAGE NEVER GUESSES.
     The pass cookie is httponly — deliberately, so nothing here can read or
     replay it — which means the only honest source for "has this reader
     already proved they are a person?" is the server. A page that guessed
     would show a human a challenge they had already passed, which is the
     complaint this whole rewrite exists to answer.
     ⭐ `human: true` also covers "Turnstile is switched off", because that is
     the same answer to the only question being asked. */
  fetch("/conversation")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      renderAll(data.messages);
      if (data.human) {
        gateDone();                  /* already through: never render a widget */
      } else {
        tsBoot();
      }
    })
    .catch(function () {
      /* ⛔ A cold bench is the normal first visit, but an unreachable
         /conversation must not leave the gate unbooted — that would be a
         composer that can never send. Assume the check is needed. */
      tsBoot();
    });
})();
