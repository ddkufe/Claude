document.documentElement.classList.remove('no-js');

document.addEventListener('DOMContentLoaded', function () {
  // Mobile nav drawer
  var nav = document.getElementById('MobileNav');
  var openBtn = document.querySelector('[data-nav-open]');
  var closeBtn = document.querySelector('[data-nav-close]');

  function openNav() {
    if (!nav) return;
    nav.classList.add('is-open');
    nav.setAttribute('aria-hidden', 'false');
  }
  function closeNav() {
    if (!nav) return;
    nav.classList.remove('is-open');
    nav.setAttribute('aria-hidden', 'true');
  }
  if (openBtn) openBtn.addEventListener('click', openNav);
  if (closeBtn) closeBtn.addEventListener('click', closeNav);
  if (nav) nav.addEventListener('click', function (e) { if (e.target === nav) closeNav(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });

  // Quantity steppers (product page + cart)
  document.querySelectorAll('[data-qty-wrapper]').forEach(function (wrapper) {
    var input = wrapper.querySelector('input[type="number"]');
    var minus = wrapper.querySelector('[data-qty-minus]');
    var plus = wrapper.querySelector('[data-qty-plus]');
    if (!input) return;
    minus && minus.addEventListener('click', function () {
      var val = Math.max(parseInt(input.min || '1', 10), (parseInt(input.value, 10) || 1) - 1);
      input.value = val;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
    plus && plus.addEventListener('click', function () {
      var val = (parseInt(input.value, 10) || 1) + 1;
      input.value = val;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  // Product gallery thumbnails
  document.querySelectorAll('[data-thumb]').forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      var main = document.querySelector('[data-main-image]');
      if (main && thumb.dataset.fullSrc) main.src = thumb.dataset.fullSrc;
      document.querySelectorAll('[data-thumb]').forEach(function (t) { t.style.borderColor = 'transparent'; });
      thumb.style.borderColor = 'var(--color-primary)';
    });
  });

  // Cart line quantity auto-submit
  document.querySelectorAll('[data-cart-qty]').forEach(function (input) {
    input.addEventListener('change', function () {
      var form = input.closest('form');
      if (form) form.submit();
    });
  });

  // Scroll-reveal animations (skipped entirely for reduced-motion users)
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealEls = document.querySelectorAll('.reveal');
  if (!prefersReducedMotion && 'IntersectionObserver' in window && revealEls.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el, i) {
      el.style.setProperty('--reveal-index', i % 6);
      observer.observe(el);
    });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // Copy-to-clipboard for deal/bundle codes
  document.querySelectorAll('[data-copy-code]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.getAttribute('data-copy-code');
      var reset = function () {
        btn.classList.remove('is-copied');
        btn.querySelector('[data-copy-label]').textContent = btn.dataset.defaultLabel;
      };
      var showCopied = function () {
        btn.classList.add('is-copied');
        btn.querySelector('[data-copy-label]').textContent = 'Copied!';
        clearTimeout(btn._copyTimeout);
        btn._copyTimeout = setTimeout(reset, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code).then(showCopied);
      } else {
        var temp = document.createElement('textarea');
        temp.value = code;
        temp.style.position = 'fixed';
        temp.style.opacity = '0';
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
        showCopied();
      }
    });
  });
});

// Bump the cart icon whenever Shopify's cart count updates via a product form submit
document.addEventListener('submit', function (e) {
  if (e.target.matches('form[action*="/cart/add"]')) {
    var count = document.querySelector('.cart-count');
    if (count) {
      setTimeout(function () {
        count.classList.remove('is-bumping');
        void count.offsetWidth;
        count.classList.add('is-bumping');
      }, 50);
    }
  }
});
