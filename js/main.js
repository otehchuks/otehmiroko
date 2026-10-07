/* =============================================================================
   OTEH MIROKO ALUMINUM — main.js
   -----------------------------------------------------------------------------
   Vanilla ES2020. No build step, no dependencies.
   Every module fails soft: if an element is missing, the module exits quietly.
   That keeps this file safe to reuse across sub-pages (e.g. a real blog).

   Contents
   01. Helpers
   02. Header: sticky shadow, scroll progress, scroll spy
   03. Mobile drawer + services accordion + focus management
   04. Reveal on scroll (IntersectionObserver)
   05. Animated counters
   06. Gallery filter
   07. Lightbox (focus trap, keyboard, swipe)
   08. Testimonials carousel (dots, autoplay, keyboard)
   09. Quote form (validation + async submit + toast)
   10. Lazy map loader
   11. Back to top + smooth-scroll fallback
   12. Footer year
   ============================================================================= */

(() => {
  'use strict';

  /* ==========================================================================
     01. HELPERS
     ========================================================================== */
  const $  = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  const prefersReducedMotion = () =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /** Trailing-edge throttle — used for scroll handlers so we don't thrash layout. */
  function throttle(fn, wait = 120) {
    let last = 0, timer = null;
    return function throttled(...args) {
      const now = Date.now();
      const remaining = wait - (now - last);
      if (remaining <= 0) {
        clearTimeout(timer);
        timer = null;
        last = now;
        fn.apply(this, args);
      } else if (!timer) {
        timer = setTimeout(() => {
          last = Date.now();
          timer = null;
          fn.apply(this, args);
        }, remaining);
      }
    };
  }

  /** Small toast with a polite live region — used for form feedback. */
  const toastEl = $('#toast');
  let toastTimer = null;
  function showToast(message, state = 'info', ms = 5200) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.dataset.state = state;
    toastEl.hidden = false;
    // Force a frame so the transform transition actually runs
    requestAnimationFrame(() => toastEl.classList.add('is-open'));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove('is-open');
      setTimeout(() => { toastEl.hidden = true; }, 340);
    }, ms);
  }

  /** Toggle an inert-ish scroll lock on <body> without exposing scrollbar jump. */
  let lockCount = 0;
  function lockScroll(lock) {
    lockCount = Math.max(0, lockCount + (lock ? 1 : -1));
    document.body.classList.toggle('is-locked', lockCount > 0);
  }

  /* ==========================================================================
     02. HEADER — shadow, progress bar, scroll spy
     ========================================================================== */
  const header = $('#siteHeader');
  const progress = $('#scrollProgress');

  const onScrollChrome = throttle(() => {
    const y = window.scrollY;
    if (header) header.dataset.scrolled = y > 8 ? 'true' : 'false';

    if (progress) {
      const doc = document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      const pct = max > 0 ? Math.min(100, (y / max) * 100) : 0;
      progress.style.width = pct + '%';
    }
  }, 60);

  window.addEventListener('scroll', onScrollChrome, { passive: true });
  onScrollChrome();

  /* Scroll spy: highlight the nav link for the section in view.
     Uses IntersectionObserver with a band around the middle of the viewport. */
  const navLinks = $$('.nav__link[href^="#"]');
  const spiedSections = navLinks
    .map(link => {
      const id = link.getAttribute('href').slice(1);
      const el = id ? document.getElementById(id) : null;
      return el ? { link, el } : null;
    })
    .filter(Boolean);

  if (spiedSections.length && 'IntersectionObserver' in window) {
    const spy = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const match = spiedSections.find(s => s.el === entry.target);
        if (!match) return;
        navLinks.forEach(l => l.removeAttribute('aria-current'));
        $$('.nav__menu a').forEach(l => l.removeAttribute('aria-current'));
        match.link.setAttribute('aria-current', 'page');
      });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });

    spiedSections.forEach(s => spy.observe(s.el));
  }

  /* ==========================================================================
     03. MOBILE DRAWER + SERVICES ACCORDION
     ========================================================================== */
  const nav = $('#primaryNav');
  const navToggle = $('#navToggle');

  function isDrawerMode() {
    return window.matchMedia('(max-width: 56.24em)').matches;
  }

  function setDrawer(open) {
    if (!nav || !navToggle) return;
    nav.classList.toggle('is-open', open);
    navToggle.setAttribute('aria-expanded', String(open));
    navToggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    lockScroll(open);

    // Move focus into the drawer so keyboard users land in the menu
    if (open && isDrawerMode()) {
      const first = $('.nav__link', nav);
      if (first) first.focus({ preventScroll: true });
    }
  }

  navToggle?.addEventListener('click', () => {
    setDrawer(navToggle.getAttribute('aria-expanded') !== 'true');
  });

  // Close the drawer when a link is followed (single-page anchors).
  // Capture phase on purpose: body.is-locked sets overflow:hidden, so the drawer
  // must release the scroll lock BEFORE the anchor's own handler calls
  // scrollIntoView, otherwise the scroll is swallowed.
  nav?.addEventListener('click', e => {
    if (e.target.closest('a[href^="#"]')) {
      // Let the accordion toggle handle its own click first
      if (e.target.closest('.nav__has-menu > .nav__link')) return;
      setDrawer(false);
    }
  }, true);

  // Esc closes the drawer and returns focus to the trigger
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && nav?.classList.contains('is-open')) {
      setDrawer(false);
      navToggle?.focus();
    }
  });

  // Reset drawer state when crossing into desktop layout
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (!isDrawerMode() && nav?.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        navToggle?.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('is-locked');
        lockCount = 0;
      }
    }, 150);
  });

  /* Services submenu: hover works on desktop via CSS; on touch/narrow screens
     the parent link toggles an accordion instead of navigating immediately. */
  const menuParents = $$('.nav__has-menu');
  menuParents.forEach(parent => {
    const trigger = $('.nav__link', parent);
    const menu = $('.nav__menu', parent);
    if (!trigger || !menu) return;

    trigger.addEventListener('click', e => {
      if (!isDrawerMode()) return;      // desktop: CSS hover handles it
      e.preventDefault();               // first tap opens the submenu
      const open = menu.dataset.open !== 'true';
      menu.dataset.open = String(open);
      trigger.setAttribute('aria-expanded', String(open));
    });

    // Keyboard: close submenu on Esc, keep focus sane
    parent.addEventListener('keydown', e => {
      if (e.key === 'Escape' && menu.dataset.open === 'true') {
        menu.dataset.open = 'false';
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }
    });
  });

  /* ==========================================================================
     04. REVEAL ON SCROLL
     Content is visible by default in CSS; the inline <head> script adds
     .js-ready to <html> to arm the animation. This module only needs to add
     .is-visible as elements enter the viewport — and to short-circuit entirely
     for reduced-motion users.
     ========================================================================== */
  const revealEls = $$('.reveal');
  if (revealEls.length) {
    if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
      revealEls.forEach(el => el.classList.add('is-visible'));
    } else {
      const revealObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);      // one-shot: never re-animate
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

      revealEls.forEach(el => revealObserver.observe(el));
    }
  }

  /* ==========================================================================
     05. ANIMATED COUNTERS (hero stats)
     ========================================================================== */
  function animateCounter(el) {
    const target = Number(el.dataset.countTo || 0);
    const suffix = el.dataset.suffix || '';
    if (prefersReducedMotion() || !target) {
      el.textContent = target + suffix;
      return;
    }
    const duration = 1400;
    const start = performance.now();

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);          // easeOutCubic
      const value = Math.round(target * eased);
      el.textContent = value.toLocaleString('en-NG') + suffix;
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  const counters = $$('[data-count-to]');
  if (counters.length && 'IntersectionObserver' in window) {
    const cObs = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        animateCounter(entry.target);
        obs.unobserve(entry.target);
      });
    }, { threshold: 0.4 });
    counters.forEach(c => cObs.observe(c));
  } else {
    counters.forEach(animateCounter);
  }

  /* ==========================================================================
     06. GALLERY FILTER
     ========================================================================== */
  const gallery = $('#gallery');
  const filterButtons = $$('.filter');
  const galleryItems = gallery ? $$('.gallery__item', gallery) : [];
  const galleryEmpty = $('#galleryEmpty');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;

      filterButtons.forEach(b => {
        const active = b === btn;
        b.classList.toggle('is-active', active);
        b.setAttribute('aria-pressed', String(active));
      });

      let shown = 0;
      galleryItems.forEach(item => {
        const matches = filter === 'all' || item.dataset.category === filter;
        if (matches) {
          shown++;
          item.hidden = false;
          // Next frame: fade/slide in
          requestAnimationFrame(() => item.classList.remove('is-fading'));
        } else {
          item.classList.add('is-fading');
          // Wait for the transition before removing from layout
          setTimeout(() => { if (item.classList.contains('is-fading')) item.hidden = true; },
            prefersReducedMotion() ? 0 : 240);
        }
      });

      if (galleryEmpty) galleryEmpty.hidden = shown !== 0;
    });
  });

  /* ==========================================================================
     07. LIGHTBOX
     Follows the ARIA dialog pattern: modal semantics, focus trap,
     Esc to close, ←/→ to navigate, swipe on touch, focus restored on close.
     ========================================================================== */
  const lightbox = $('#lightbox');
  const lbImage = $('#lbImage');
  const lbCaption = $('#lbCaption');
  const lbCounter = $('#lbCounter');
  const overlay = $('#overlay');
  const triggers = $$('[data-lightbox]');

  if (lightbox && lbImage && triggers.length) {
    let index = 0;
    let lastFocused = null;

    const visibleTriggers = () =>
      triggers.filter(a => {
        const li = a.closest('.gallery__item');
        return !li || !li.hidden;             // respect the active filter
      });

    const focusables = () => $$('button, [href], input, [tabindex]:not([tabindex="-1"])', lightbox)
      .filter(el => el.offsetParent !== null);

    /**
     * Resolve the image a trigger should show. Prefers the link target (a
     * full-size image); falls back to the thumbnail's own resolved source, which
     * is what lets the single-file build embed each image only once.
     * Used by both render() and the neighbour preloader so they can't drift.
     */
    function srcFor(trigger) {
      const href = trigger.getAttribute('href');
      if (href && href !== '#') return href;
      const thumb = $('img', trigger);
      return thumb ? (thumb.currentSrc || thumb.src) : '';
    }

    function render(list) {
      const trigger = list[index];
      if (!trigger) return;
      const thumb = $('img', trigger);
      const fullSrc = srcFor(trigger);
      if (!fullSrc) return;

      lbImage.src = fullSrc;
      // Reuse the thumbnail's alt text so the lightbox image stays described
      lbImage.alt = thumb ? thumb.alt : '';
      lbCaption.textContent = trigger.dataset.caption || '';
      lbCaption.id = 'lbCaption';
      if (lbCounter) lbCounter.textContent = `${index + 1} / ${list.length}`;

      // Keep prev/next usable when there is only one image
      const single = list.length < 2;
      $('#lbPrev')?.toggleAttribute('disabled', single);
      $('#lbNext')?.toggleAttribute('disabled', single);
    }

    function open(trigger) {
      const list = visibleTriggers();
      index = Math.max(0, list.indexOf(trigger));
      lastFocused = document.activeElement;

      lightbox.hidden = false;
      overlay.hidden = false;
      lockScroll(true);

      render(list);
      requestAnimationFrame(() => {
        lightbox.classList.add('is-open');
        overlay.classList.add('is-open');
      });
      $('#lbClose')?.focus();
    }

    function close() {
      lightbox.classList.remove('is-open');
      overlay.classList.remove('is-open');
      lockScroll(false);
      setTimeout(() => {
        lightbox.hidden = true;
        overlay.hidden = true;
        lbImage.src = '';
      }, 220);
      // Return focus to the thumbnail that opened the viewer (WCAG 2.4.3)
      if (lastFocused instanceof HTMLElement) lastFocused.focus({ preventScroll: true });
    }

    function step(delta) {
      const list = visibleTriggers();
      if (list.length < 2) return;
      index = (index + delta + list.length) % list.length;
      render(list);
    }

    triggers.forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();                 // don't hard-navigate to the JPG
        open(a);
      });
    });

    $('#lbClose')?.addEventListener('click', close);
    $('#lbPrev')?.addEventListener('click', () => step(-1));
    $('#lbNext')?.addEventListener('click', () => step(1));

    // Click the backdrop (but not the image/caption) to dismiss
    lightbox.addEventListener('click', e => {
      if (e.target === lightbox || e.target.classList.contains('lightbox__inner')) close();
    });
    overlay.addEventListener('click', close);

    // Keyboard: Esc / arrows / Home / End, with a focus trap on Tab
    lightbox.addEventListener('keydown', e => {
      switch (e.key) {
        case 'Escape': e.preventDefault(); close(); break;
        case 'ArrowRight': e.preventDefault(); step(1); break;
        case 'ArrowLeft': e.preventDefault(); step(-1); break;
        case 'Home': e.preventDefault(); { const l = visibleTriggers(); index = 0; render(l); } break;
        case 'End': e.preventDefault(); { const l = visibleTriggers(); index = l.length - 1; render(l); } break;
        case 'Tab': {
          const f = focusables();
          if (!f.length) return;
          const first = f[0], last = f[f.length - 1];
          if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
          else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
          break;
        }
        default: break;
      }
    });

    // Touch swipe
    let touchStartX = 0, touchStartY = 0;
    lightbox.addEventListener('touchstart', e => {
      touchStartX = e.changedTouches[0].clientX;
      touchStartY = e.changedTouches[0].clientY;
    }, { passive: true });

    lightbox.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - touchStartX;
      const dy = e.changedTouches[0].clientY - touchStartY;
      // Horizontal intent only, and far enough to be deliberate
      if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.6) step(dx < 0 ? 1 : -1);
    }, { passive: true });

    // Preload neighbours for snappy navigation
    lbImage.addEventListener('load', () => {
      const list = visibleTriggers();
      [list[index + 1], list[index - 1]].forEach(t => {
        if (!t) return;
        const src = srcFor(t);
        if (!src) return;                    // nothing to warm up
        const img = new Image();
        img.src = src;
      });
    });
  }

  /* ==========================================================================
     08. TESTIMONIALS CAROUSEL
     One slide per view; dots + arrows + keyboard; autoplay pauses on
     hover, focus, tab-hidden, and when the user prefers reduced motion.
     ========================================================================== */
  const carousel = $('#testimonialCarousel');
  const track = $('#carouselTrack');

  if (carousel && track) {
    const slides = $$('.carousel__slide', track);
    const dotsWrap = $('#carouselDots');
    let current = 0;
    let autoplayId = null;

    // Build dots from the slide count so content and controls can't drift apart
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.type = 'button';
      dot.className = 'carousel__dot';
      dot.setAttribute('role', 'tab');
      dot.setAttribute('aria-label', `Show testimonial ${i + 1} of ${slides.length}`);
      dot.setAttribute('aria-selected', String(i === 0));
      dot.addEventListener('click', () => goTo(i));
      dotsWrap?.appendChild(dot);
    });
    const dots = dotsWrap ? $$('.carousel__dot', dotsWrap) : [];

    function goTo(i) {
      current = (i + slides.length) % slides.length;
      track.style.transform = `translateX(-${current * 100}%)`;
      dots.forEach((d, di) => d.setAttribute('aria-selected', String(di === current)));
      slides.forEach((s, si) => s.toggleAttribute('inert', si !== current));
      // Don't leave focus on a hidden slide's content
      slides.forEach((s, si) => { if (si !== current) s.setAttribute('aria-hidden', 'true'); });
      slides[current].removeAttribute('aria-hidden');
    }

    function startAutoplay() {
      if (prefersReducedMotion() || autoplayId) return;
      autoplayId = setInterval(() => goTo(current + 1), 7000);
    }
    function stopAutoplay() {
      clearInterval(autoplayId);
      autoplayId = null;
    }

    $('#carouselNext')?.addEventListener('click', () => { goTo(current + 1); stopAutoplay(); });
    $('#carouselPrev')?.addEventListener('click', () => { goTo(current - 1); stopAutoplay(); });

    // Pause while the user is engaging with it
    ['mouseenter', 'focusin'].forEach(ev => carousel.addEventListener(ev, stopAutoplay));
    ['mouseleave', 'focusout'].forEach(ev => carousel.addEventListener(ev, startAutoplay));
    carousel.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight') { goTo(current + 1); stopAutoplay(); }
      if (e.key === 'ArrowLeft') { goTo(current - 1); stopAutoplay(); }
    });
    // Stop cycling when the tab is hidden (saves battery, avoids jarring jumps)
    document.addEventListener('visibilitychange', () =>
      document.hidden ? stopAutoplay() : startAutoplay());

    // Touch swipe support
    let sx = 0;
    carousel.addEventListener('touchstart', e => { sx = e.changedTouches[0].clientX; }, { passive: true });
    carousel.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 50) { goTo(current + (dx < 0 ? 1 : -1)); stopAutoplay(); }
    }, { passive: true });

    goTo(0);
    startAutoplay();
  }

  /* ==========================================================================
     09. QUOTE FORM
     Custom validation with inline, announced errors. Submits via fetch to the
     endpoint in the form's action attribute so the user never leaves the page.
     Swap `action` for your own handler (Formspree / Netlify / API route) or set
     data-demo="true" to simulate a successful send.
     ========================================================================== */
  const form = $('#quoteForm');
  const statusBox = $('#formStatus');

  if (form) {
    const submitBtn = $('#submitBtn', form);
    const isDemo = form.dataset.demo === 'true' ||
      (form.getAttribute('action') || '').includes('your-endpoint-id');

    /** Rule set: each field declares how it should be judged. */
    const rules = {
      fullName: v => v.trim().length >= 2 || 'Please enter your full name.',
      phone:    v => /^[+()\d\s-]{7,20}$/.test(v.trim()) || 'Enter a reachable phone number (7–20 digits).',
      email:    v => /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(v.trim()) || 'Enter a valid email address.',
      service:  v => v !== '' || 'Choose the service you need.',
      details:  v => v.trim().length >= 20 || 'Please add a little more detail (at least 20 characters).',
      consent:  (v, el) => el.checked || 'Please tick the consent box so we can reply.'
    };

    function fieldWrapper(input) {
      return input.closest('.field');
    }

    function setError(input, message) {
      const wrap = fieldWrapper(input);
      const errorEl = document.getElementById('err-' + input.id);
      if (!wrap || !errorEl) return;
      wrap.classList.add('has-error');
      errorEl.textContent = message;
      errorEl.hidden = false;
      input.setAttribute('aria-invalid', 'true');
    }

    function clearError(input) {
      const wrap = fieldWrapper(input);
      const errorEl = document.getElementById('err-' + input.id);
      if (!wrap || !errorEl) return;
      wrap.classList.remove('has-error');
      errorEl.hidden = true;
      errorEl.textContent = '';
      input.removeAttribute('aria-invalid');
    }

    /** Validate one field. Returns true when valid. */
    function validateField(input, { announce = false } = {}) {
      const rule = rules[input.name];
      if (!rule) return true;
      const result = rule(input.value, input);
      if (result === true) {
        clearError(input);
        return true;
      }
      setError(input, result);
      if (announce) input.focus({ preventScroll: false });
      return false;
    }

    // Validate on blur and on input (clearing errors as soon as they're fixed)
    Object.keys(rules).forEach(name => {
      const input = form.elements[name];
      if (!input) return;
      input.addEventListener('blur', () => {
        // Only nag once the user has actually typed something
        if (input.type !== 'checkbox' && input.value.trim() === '') return;
        validateField(input);
      });
      input.addEventListener('input', () => {
        if (fieldWrapper(input)?.classList.contains('has-error')) validateField(input);
      });
      input.addEventListener('change', () => {
        if (input.type === 'checkbox') validateField(input);
      });
    });

    // Enforce the same attachment rules shown beside the file picker.
    const fileInput = form.elements.attachments;
    const maxFiles = 3;
    const maxBytes = 5 * 1024 * 1024;
    const allowedFile = /\.(?:jpe?g|png|pdf|dwg)$/i;

    function validateAttachments() {
      if (!fileInput) return true;
      const files = Array.from(fileInput.files || []);
      const errors = [];
      const unsupported = files.filter(file => !allowedFile.test(file.name));
      const oversized = files.filter(file => file.size > maxBytes);

      if (files.length > maxFiles) {
        errors.push(`Choose no more than ${maxFiles} files.`);
      }
      if (unsupported.length) {
        errors.push(`Unsupported file type: ${unsupported.map(file => file.name).join(', ')}. Use JPEG, PNG, PDF or DWG.`);
      }
      if (oversized.length) {
        errors.push(`Files must be 5 MB or smaller: ${oversized.map(file => file.name).join(', ')}.`);
      }

      if (errors.length) setError(fileInput, errors.join(' '));
      else clearError(fileInput);
      return errors.length === 0;
    }

    fileInput?.addEventListener('change', validateAttachments);

    form.addEventListener('submit', async e => {
      e.preventDefault();

      // 1. Honeypot check — silently swallow bot submissions
      if (form.elements.company_url?.value) return;

      // 2. Validate everything, then focus the first offender
      const names = Object.keys(rules);
      let firstBad = null;
      names.forEach(name => {
        const input = form.elements[name];
        if (!input) return;
        const ok = validateField(input);
        if (!ok && !firstBad) firstBad = input;
      });
      if (!validateAttachments() && !firstBad) firstBad = fileInput;

      if (firstBad) {
        if (statusBox) {
          statusBox.hidden = false;
          statusBox.dataset.state = 'error';
          statusBox.textContent = 'Some details need attention. Please review the highlighted fields.';
        }
        firstBad.focus({ preventScroll: false });
        firstBad.scrollIntoView({ block: 'center', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
        return;
      }

      // 3. Loading state
      submitBtn?.classList.add('is-loading');
      submitBtn?.setAttribute('aria-busy', 'true');
      if (submitBtn) submitBtn.disabled = true;
      if (statusBox) {
        statusBox.hidden = false;
        statusBox.dataset.state = '';
        statusBox.textContent = 'Sending your request…';
      }

      try {
        if (isDemo) {
          // Demo mode: no endpoint configured yet.
          await new Promise(r => setTimeout(r, 900));
        } else {
          const response = await fetch(form.action, {
            method: form.method || 'POST',
            body: new FormData(form),
            headers: { Accept: 'application/json' }
          });
          if (!response.ok) throw new Error(`Request failed (${response.status})`);
        }

        form.reset();
        $$('.field', form).forEach(f => f.classList.remove('has-error'));
        $$('.field__error', form).forEach(el => { el.hidden = true; el.textContent = ''; });

        if (statusBox) {
          statusBox.hidden = false;
          statusBox.dataset.state = 'success';
          statusBox.innerHTML =
            '<strong>Thank you — your request is in.</strong><br>' +
            'A member of our team will call you within one business day to arrange the site visit. ' +
            'For anything urgent, WhatsApp <a href="https://wa.me/2348167859034">+234 816 785 9034</a>.';
        }
        showToast('Quote request sent. We\'ll be in touch within one business day.', 'success');
      } catch (err) {
        if (statusBox) {
          statusBox.hidden = false;
          statusBox.dataset.state = 'error';
          statusBox.innerHTML =
            '<strong>We couldn\'t send that just now.</strong><br>' +
            'Please try again, or reach us directly on <a href="tel:+2348167859034">+234 816 785 9034</a> ' +
            'or <a href="mailto:hello@otehmirokoaluminum.com">hello@otehmirokoaluminum.com</a>.';
        }
        showToast('Sending failed. Please try again or call us.', 'error');
        console.error('[quote form]', err);
      } finally {
        submitBtn?.classList.remove('is-loading');
        submitBtn?.removeAttribute('aria-busy');
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  /* ==========================================================================
     10. LAZY MAP LOADER
     The Google iframe is only injected on demand — keeps third-party JS,
     cookies and ~700 KB of payload off first paint.
     ========================================================================== */
  const loadMapBtn = $('#loadMap');
  const mapFrame = $('#mapFrame');
  const mapPoster = $('#mapPoster');

  // Paste the client's real embed URL here (Google Maps → Share → Embed a map)
  const MAP_EMBED_SRC =
    'https://www.google.com/maps?q=Ikeja%2C%20Lagos%2C%20Nigeria&output=embed';

  loadMapBtn?.addEventListener('click', () => {
    if (!mapFrame) return;
    const iframe = document.createElement('iframe');
    iframe.src = MAP_EMBED_SRC;
    iframe.title = 'Map showing the Oteh Miroko Aluminum workshop in Ikeja, Lagos';
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'no-referrer-when-downgrade';
    iframe.setAttribute('allowfullscreen', '');
    mapFrame.appendChild(iframe);
    mapPoster?.remove();
    showToast('Loading map…', 'info', 1800);
  });

  /* ==========================================================================
     11. BACK TO TOP + SMOOTH-SCROLL FALLBACK
     ========================================================================== */
  const backToTop = $('#backToTop');
  const toggleTop = throttle(() => {
    if (!backToTop) return;
    const show = window.scrollY > window.innerHeight * 0.9;
    backToTop.hidden = !show;
  }, 200);
  window.addEventListener('scroll', toggleTop, { passive: true });
  toggleTop();

  backToTop?.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
    // Send focus to the top of the document for keyboard users
    $('.skip-link')?.focus({ preventScroll: true });
  });

  /* Anchor links: smooth where supported, instant where not.
     CSS scroll-behavior does most of this; this handler adds the focus move
     so screen-reader users land inside the target section. */
  $$('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const href = link.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.getElementById(href.slice(1));
      if (!target) return;

      // Let the browser handle scroll (CSS smooth); we only manage focus.
      if (e.defaultPrevented) return;
      e.preventDefault();
      target.scrollIntoView({
        behavior: prefersReducedMotion() ? 'auto' : 'smooth',
        block: 'start'
      });
      // Make the section programmatically focusable and focus it
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      // Update the address bar so the section is linkable and the back button
      // behaves sanely. Wrapped because pushState throws a SecurityError inside
      // sandboxed iframes and some file:// contexts — the scroll must still work.
      try {
        history.pushState(null, '', href);
      } catch {
        /* non-fatal: URL just won't reflect the section */
      }
    });
  });

  /* ==========================================================================
     12. FOOTER YEAR
     ========================================================================== */
  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

})();
