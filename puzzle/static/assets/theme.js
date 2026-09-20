// Light/dark theme toggle.
//
// Initial paint is set by a tiny inline <script> in each page's <head> so
// authed-or-stored light-mode users don't flash dark first. This file
// handles toggle clicks, the live OS-preference listener, and icon
// updates.
(function () {
  'use strict';

  var KEY = 'rr_theme';
  var root = document.documentElement;

  function getStored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setStored(v) {
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }

  function current() {
    return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }
  function apply(theme) {
    // The ticker is a CSS marquee. When data-theme flips, the browser
    // recalculates every var-driven rule on the page, which can drop
    // the animation back to position 0 on some browsers. Snapshot the
    // current transform before the swap, freeze each track on its
    // captured X, then resume with a negative animation-delay so the
    // animation continues seamlessly from the same spot.
    var tracks = document.querySelectorAll('.ticker-track');
    var snaps = [];
    tracks.forEach(function (t) {
      var cs = getComputedStyle(t);
      var raw = cs.transform;
      var x = 0;
      if (raw && raw !== 'none') {
        try {
          var m = new DOMMatrixReadOnly(raw);
          x = m.m41;
        } catch (e) {
          var match = raw.match(/matrix\(([^)]+)\)/);
          if (match) { x = parseFloat(match[1].split(',')[4]) || 0; }
        }
      }
      // Track loops at translateX(-50%). offsetWidth is the full
      // duplicated width; halfway = offsetWidth/2 of travel.
      var travel = t.offsetWidth / 2;
      snaps.push({ el: t, x: x, travel: travel });
      // Freeze in place during the swap.
      t.style.animation = 'none';
      t.style.transform = 'translateX(' + x + 'px)';
    });
    // Force a reflow so the freeze is committed before the attribute flip.
    void root.offsetHeight;
    if (theme === 'light') root.setAttribute('data-theme', 'light');
    else root.removeAttribute('data-theme');
    var resume = function () {
      snaps.forEach(function (s) {
        var progress = s.travel > 0 ? Math.min(Math.abs(s.x) / s.travel, 1) : 0;
        var elapsed = progress * 50; // animation duration is 50s
        s.el.style.animation = '';
        s.el.style.transform = '';
        s.el.style.animationDelay = (-elapsed) + 's';
      });
    };
    if (window.requestAnimationFrame) requestAnimationFrame(resume);
    else resume();
  }

  // Button shows the icon for the theme you'd switch TO. In dark, show
  // sun (click → light). In light, show moon (click → dark).
  function syncIcons() {
    var goingTo = current() === 'light' ? 'dark' : 'light';
    var iconClass = goingTo === 'light' ? 'ph-sun' : 'ph-moon';
    var label = 'switch to ' + goingTo + ' mode';
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.setAttribute('aria-label', label);
      btn.setAttribute('title', label);
      var i = btn.querySelector('i');
      if (i) i.className = 'ph ' + iconClass;
    });
  }

  function onToggleClick() {
    var next = current() === 'light' ? 'dark' : 'light';
    apply(next);
    setStored(next);
    syncIcons();
  }

  // Inject the theme toggle into the top bar. Placement, in order of
  // preference: the .bar-tools cluster in the RIGHT corner, which is where
  // every control lives on the door bar; then the old .bar-left cluster beside
  // the logo; then straight after the brand. The first case is the one that
  // applies here, the other two only exist so nothing breaks if the bar is
  // ever reverted. Lifted verbatim from apex so the two cannot drift.
  function injectMobileToggle() {
    var bar = document.querySelector('.bar');
    if (!bar) return;
    if (bar.querySelector('.theme-toggle-mobile')) return;
    var tools = bar.querySelector('.bar-tools');
    var brand = bar.querySelector('.brand');
    if (!tools && !brand) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle theme-toggle-mobile';
    btn.appendChild(document.createElement('i'));
    if (tools) {
      tools.insertBefore(btn, tools.firstChild);        // left of the account button
    } else {
      var cluster = brand.closest('.bar-left');
      if (cluster) cluster.appendChild(btn);
      else brand.parentNode.insertBefore(btn, brand.nextSibling);
    }
  }

  function wire() {
    injectMobileToggle();
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      if (btn.dataset.wired) return;
      btn.dataset.wired = '1';
      btn.addEventListener('click', onToggleClick);
    });
    syncIcons();
  }

  // OS prefers-color-scheme auto-detect is intentionally OFF while the
  // light palette is provisional. To re-enable later, uncomment:
  //   if (window.matchMedia) {
  //     var mql = window.matchMedia('(prefers-color-scheme: light)');
  //     var handler = function (e) {
  //       if (getStored()) return;
  //       apply(e.matches ? 'light' : 'dark');
  //       syncIcons();
  //     };
  //     if (mql.addEventListener) mql.addEventListener('change', handler);
  //     else if (mql.addListener) mql.addListener(handler);
  //   }
  // And mirror in each page's anti-flash inline <script> in <head>.

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();

// ─── Video pause/play + mute controls ──────────────────────────────
// Every <video> on the page gets wrapped in a .video-wrap and gets a
// pause overlay + mini-controls overlay (play/pause + mute). Videos
// start paused — user clicks to play. At most ONE video can be unmuted
// at a time across the page (the videos all share Nathan's narration,
// so simultaneous unmute would overlap). Out-of-viewport pause kept
// for opt-in cases via `data-autoplay-on-view` (not used on the
// current promos but available for future videos).
(function () {
  'use strict';

  function muteAllOthers(except) {
    document.querySelectorAll('video').forEach(function (v) {
      if (v !== except && !v.muted) v.muted = true;
    });
  }

  // When THIS video starts playing, every other video pauses + mutes so
  // only one voice is ever on at a time.
  function pauseAllOthers(except) {
    document.querySelectorAll('video').forEach(function (v) {
      if (v !== except && !v.paused) v.pause();
      if (v !== except && !v.muted)  v.muted = true;
    });
  }

  function wrapAndControl(video) {
    // Opt-out: background/decorative videos (e.g. .hero-bg on /sportshome/)
    // shouldn't be wrapped or paused. Add class="hero-bg" OR
    // data-skip-controls="1" to opt out.
    if (video.classList.contains('hero-bg')) return;
    if (video.dataset.skipControls === '1') return;
    if (video.dataset.controlsWired === '1') return;
    video.dataset.controlsWired = '1';

    // Wrap in .video-wrap so absolute children can sit on top.
    var wrap = document.createElement('div');
    wrap.className = 'video-wrap is-paused';
    video.parentNode.insertBefore(wrap, video);
    wrap.appendChild(video);

    // Big centered play button (pause state).
    var bigPlay = document.createElement('button');
    bigPlay.type = 'button';
    bigPlay.className = 'video-bigplay';
    bigPlay.setAttribute('aria-label', 'play');
    bigPlay.innerHTML = '<i class="ph ph-play-fill"></i>';
    wrap.appendChild(bigPlay);

    // Corner controls (play/pause + mute).
    var ctrls = document.createElement('div');
    ctrls.className = 'video-controls';

    var playBtn = document.createElement('button');
    playBtn.type = 'button';
    playBtn.className = 'video-ctrl video-play';
    playBtn.setAttribute('aria-label', 'play');
    playBtn.innerHTML = '<i class="ph ph-play"></i>';

    var muteBtn = document.createElement('button');
    muteBtn.type = 'button';
    muteBtn.className = 'video-ctrl video-mute';
    muteBtn.setAttribute('aria-label', 'unmute');
    muteBtn.innerHTML = '<i class="ph ph-speaker-simple-x"></i>';

    ctrls.appendChild(playBtn);
    ctrls.appendChild(muteBtn);
    wrap.appendChild(ctrls);

    // Sync icon helpers.
    function syncPlay() {
      var paused = video.paused;
      wrap.classList.toggle('is-paused', paused);
      var i = playBtn.querySelector('i');
      if (i) i.className = paused ? 'ph ph-play' : 'ph ph-pause';
      playBtn.setAttribute('aria-label', paused ? 'play' : 'pause');
    }
    function syncMute() {
      var muted = video.muted;
      var i = muteBtn.querySelector('i');
      if (i) i.className = muted ? 'ph ph-speaker-simple-x' : 'ph ph-speaker-simple-high';
      muteBtn.setAttribute('aria-label', muted ? 'unmute' : 'mute');
    }

    function togglePlay() {
      if (video.paused) {
        // Starting playback — pause + mute all other videos, then unmute
        // THIS video so the user actually hears what they just hit play on.
        pauseAllOthers(video);
        video.muted = false;
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
      } else {
        video.pause();
      }
    }
    function toggleMute() {
      if (video.muted) {
        // Unmuting THIS video. If THIS video is actually playing, mute all
        // others so audio doesn't overlap. If THIS video is paused, just
        // queue the unmute state without yanking audio off whatever is
        // currently playing — the user is prepping, not switching focus.
        if (!video.paused) muteAllOthers(video);
        video.muted = false;
      } else {
        video.muted = true;
      }
    }

    bigPlay.addEventListener('click', function (e) { e.stopPropagation(); togglePlay(); });
    playBtn.addEventListener('click', function (e) { e.stopPropagation(); togglePlay(); });
    muteBtn.addEventListener('click', function (e) { e.stopPropagation(); toggleMute(); });
    // Swallow stray clicks on the controls bar so dead-space doesn't toggle play.
    ctrls.addEventListener('click', function (e) { e.stopPropagation(); });
    // Click anywhere on video to play/pause.
    video.addEventListener('click', togglePlay);

    video.addEventListener('play', syncPlay);
    video.addEventListener('pause', syncPlay);
    video.addEventListener('volumechange', syncMute);

    syncPlay();
    syncMute();
  }

  function wireOptInAutoplay() {
    var vids = document.querySelectorAll('video[data-autoplay-on-view]');
    if (!vids.length) return;
    if (!('IntersectionObserver' in window)) {
      vids.forEach(function (v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var v = entry.target;
        if (entry.isIntersecting) {
          var p = v.play();
          if (p && p.catch) p.catch(function () {});
        } else {
          v.pause();
        }
      });
    }, { threshold: 0.5 });
    vids.forEach(function (v) { io.observe(v); });
  }

  // Mobile A/B tab swap for the landing hero flanks. Follows the WAI-ARIA
  // tabs pattern: arrow keys cycle, Home/End jump to ends, only the
  // currently-selected tab has tabindex=0 (roving tabindex).
  function wireHeroTabs() {
    var row = document.querySelector('.hero-flank-row');
    if (!row) return;
    var tabs = Array.prototype.slice.call(row.querySelectorAll('.hero-tab'));
    if (!tabs.length) return;
    row.setAttribute('data-active-tab', 'sports');

    function select(tab, opts) {
      var target = tab.dataset.tab;
      row.setAttribute('data-active-tab', target);
      tabs.forEach(function (t) {
        var on = t === tab;
        t.classList.toggle('is-active', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.setAttribute('tabindex', on ? '0' : '-1');
      });
      row.querySelectorAll('.hero-flank').forEach(function (flank) {
        if (flank.dataset.product !== target) {
          flank.querySelectorAll('video').forEach(function (v) { v.pause(); });
        }
      });
      if (opts && opts.focus) tab.focus();
    }

    tabs.forEach(function (tab, idx) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (e) {
        var k = e.key;
        if (k === 'ArrowRight' || k === 'ArrowDown') {
          e.preventDefault();
          select(tabs[(idx + 1) % tabs.length], { focus: true });
        } else if (k === 'ArrowLeft' || k === 'ArrowUp') {
          e.preventDefault();
          select(tabs[(idx - 1 + tabs.length) % tabs.length], { focus: true });
        } else if (k === 'Home') {
          e.preventDefault();
          select(tabs[0], { focus: true });
        } else if (k === 'End') {
          e.preventDefault();
          select(tabs[tabs.length - 1], { focus: true });
        }
      });
    });
  }

  // ─── Skip-to-content link ───────────────────────────────────
  // Inject as first body child so it's the first focusable element on
  // Tab. Visible-on-focus per WCAG 2.4.1. Target is the first content
  // container we can find; we tag it with an id if it doesn't have one.
  function injectSkipLink() {
    if (document.querySelector('.skip-link')) return;
    var target = document.querySelector(
      'main, [role="main"], #main, #main-content, .container, main.col, main.wrap'
    );
    if (!target) return;
    if (!target.id) target.id = 'main-content';
    var link = document.createElement('a');
    link.className = 'skip-link';
    link.href = '#' + target.id;
    link.textContent = 'skip to content';
    document.body.insertBefore(link, document.body.firstChild);
  }

  // ─── Drawer a11y: focus trap + focus-return on close. ──────
  // The per-page inline script handles open/close (sets aria-hidden).
  // We layer a MutationObserver to watch the attribute and manage focus.
  function wireDrawerA11y() {
    var drawer = document.getElementById('mobile-drawer');
    if (!drawer) return;
    var hamburger = document.querySelector('.hamburger');

    function focusable() {
      return drawer.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
    }

    var obs = new MutationObserver(function (muts) {
      muts.forEach(function (m) {
        if (m.attributeName !== 'aria-hidden') return;
        var hidden = drawer.getAttribute('aria-hidden') === 'true';
        if (!hidden) {
          // Just opened — focus first item after the close button so the
          // first thing a keyboard user lands on is a nav link.
          var items = focusable();
          // Skip the close button (first item) if there's a real link after it.
          var target = items[1] || items[0];
          if (target) target.focus();
        } else {
          // Just closed — return focus to the hamburger.
          if (hamburger && hamburger.offsetParent !== null) hamburger.focus();
        }
      });
    });
    obs.observe(drawer, { attributes: true, attributeFilter: ['aria-hidden'] });

    // Trap Tab inside the drawer while it's open.
    drawer.addEventListener('keydown', function (e) {
      if (drawer.getAttribute('aria-hidden') !== 'false') return;
      if (e.key !== 'Tab') return;
      var items = focusable();
      if (!items.length) return;
      var first = items[0];
      var last  = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    });
  }

  // ─── Dropdown a11y: arrow-key navigation inside .menu. ────
  // Follows the WAI-ARIA menubar pattern lite: ArrowDown opens + focuses
  // first item; ArrowUp/Down cycles; Home/End jumps; Escape returns to
  // trigger; Tab closes the menu and lets focus flow naturally.
  function wireDropdownA11y() {
    var items = document.querySelectorAll('.nav-item');
    if (!items.length) return;

    items.forEach(function (item) {
      var btn  = item.querySelector('.nav-btn');
      var menu = item.querySelector('.menu');
      if (!btn || !menu) return;

      function menuLinks() {
        return Array.prototype.slice.call(menu.querySelectorAll('a, button'));
      }
      function openMenu() {
        // Close any sibling menus first (mirrors the inline-script behavior).
        items.forEach(function (other) {
          if (other !== item) {
            other.classList.remove('open');
            var ob = other.querySelector('.nav-btn');
            if (ob) ob.setAttribute('aria-expanded', 'false');
          }
        });
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
      function closeMenu() {
        item.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }

      // Trigger keyboard handling.
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          openMenu();
          requestAnimationFrame(function () {
            var first = menuLinks()[0];
            if (first) first.focus();
          });
        } else if (e.key === 'Escape' && item.classList.contains('open')) {
          e.preventDefault();
          closeMenu();
          btn.focus();
        }
      });

      // In-menu keyboard handling.
      menu.addEventListener('keydown', function (e) {
        var links = menuLinks();
        if (!links.length) return;
        var idx = links.indexOf(document.activeElement);
        var k = e.key;
        if (k === 'ArrowDown') {
          e.preventDefault();
          links[(idx + 1) % links.length].focus();
        } else if (k === 'ArrowUp') {
          e.preventDefault();
          links[(idx - 1 + links.length) % links.length].focus();
        } else if (k === 'Home') {
          e.preventDefault();
          links[0].focus();
        } else if (k === 'End') {
          e.preventDefault();
          links[links.length - 1].focus();
        } else if (k === 'Escape') {
          e.preventDefault();
          closeMenu();
          btn.focus();
        } else if (k === 'Tab') {
          // Let Tab flow naturally, but close the menu so it doesn't
          // stay open behind the user.
          closeMenu();
        }
      });
    });
  }

  function init() {
    injectSkipLink();
    document.querySelectorAll('video').forEach(wrapAndControl);
    wireOptInAutoplay();
    wireHeroTabs();
    wireDrawerA11y();
    wireDropdownA11y();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

// ─── Auth-aware nav ─────────────────────────────────────────────────
// Once the visitor has a live .resolveresearcher.com session cookie, the
// guest "log in" / "sign up" CTAs are pointless — hide log in and turn the
// sign-up CTA into a single "account" link → profile.resolveresearcher.com.
// The session cookie is HttpOnly (not readable in JS), so auth state needs a
// network round-trip: the guest CTAs paint first and flip on a confirmed 200
// from /v1/auth/me. Loaded on every page via this shared script, so any new
// page that copies the chrome inherits this behavior for free.
(function () {
  'use strict';

  var API = (window.PD_API_BASE || 'https://api.resolveresearcher.com').replace(/\/$/, '');
  var PROFILE = 'https://profile.resolveresearcher.com';

  function isLogin(a)  { var h = a.getAttribute('href') || ''; return h === '/login/'  || h === '/login'; }
  function isSignup(a) { var h = a.getAttribute('href') || ''; return h === '/signup/' || h === '/signup'; }

  function swap(scope, accountMarkup) {
    if (!scope) return;
    var signup = null, login = null;
    scope.querySelectorAll('a').forEach(function (a) {
      if (isSignup(a)) signup = a;
      else if (isLogin(a)) login = a;
    });
    if (signup) {
      signup.setAttribute('href', PROFILE);
      signup.setAttribute('aria-label', 'your account');
      signup.innerHTML = accountMarkup;
    }
    if (login) login.style.display = 'none';
    // Page with a log-in link but no sign-up CTA: repurpose log in instead.
    if (!signup && login) {
      login.setAttribute('href', PROFILE);
      login.setAttribute('aria-label', 'your account');
      login.innerHTML = accountMarkup;
      login.style.display = '';
    }
  }

  function applyAuthed() {
    if (document.documentElement.getAttribute('data-authed') === '1') return;
    document.documentElement.setAttribute('data-authed', '1');
    swap(document.querySelector('.nav'), '<i class="ph ph-user-circle"></i>account');
    swap(document.getElementById('mobile-drawer') || document.querySelector('.drawer'),
         '<i class="ph ph-user-circle"></i>account');
  }

  function check() {
    if (!window.fetch) return;
    fetch(API + '/v1/auth/me', { credentials: 'include' })
      .then(function (r) { if (r.ok) applyAuthed(); })
      .catch(function () {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', check);
  } else {
    check();
  }
})();
