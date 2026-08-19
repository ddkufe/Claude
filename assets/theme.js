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
});
