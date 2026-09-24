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
          throw err;
        }
        return data;
      });
    });
  }

  /* One message. `row` is {turn, role, english, surface, let_go, refused}. */
  function render(row) {
    var node = tpl.content.firstElementChild.cloneNode(true);
    node.classList.add(row.role === "you" ? "msg-you" : "msg-tlon");
    node.dataset.turn = row.turn;
    node.dataset.role = row.role;

    /* ⛔⛔ NOTHING RENDERS ENGLISH HERE. An earlier build put the reader's own
       English beside its Tlön line, which is a parallel text: one aligned pair
       per turn, free, accumulating into a word-list. The onset and the
       translate button are the only sanctioned ways meaning crosses over. */
    var text = node.querySelector(".msg-text");
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

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (busy) return;
    var english = input.value.trim();
    if (!english) return;

    busy = true;
    send.disabled = true;
    input.value = "";
    if (empty) empty.hidden = true;
    say("it is thinking…", "wait");

    post("/say", { english: english })
      .then(function (data) {
        (data.messages || []).forEach(render);
        newThread.hidden = false;
        log.scrollTop = log.scrollHeight;
        say("");
      })
      .catch(function (e) {
        /* ⛔ Put the text back. Losing what someone typed to a rate limit is a
           second punishment for the same thing. */
        input.value = english;
        say(e.message, "bad");
      })
      .then(function () {
        busy = false;
        send.disabled = false;
        input.focus();
      });
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

  /* ⛔ PLACEHOLDER MEDIA. Until Nate supplies the real files these <video>
     elements point at paths with nothing behind them. Hide any that fail to
     load so an absent asset reads as absence and never as a broken player. */
  document.querySelectorAll("[data-placeholder-video]").forEach(function (el) {
    var v = el.tagName === "VIDEO" ? el : el.querySelector("video");
    if (!v) return;
    v.addEventListener("error", function () { el.classList.add("is-missing"); }, true);
    var s = v.querySelector("source");
    if (s) s.addEventListener("error", function () { el.classList.add("is-missing"); });
  });

  fetch("/conversation")
    .then(function (r) { return r.json(); })
    .then(function (data) { renderAll(data.messages); })
    .catch(function () { /* a cold bench is the normal first visit */ });
})();
