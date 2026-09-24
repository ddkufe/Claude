document.documentElement.classList.remove('no-js');

// Bundle savings tiers, sorted richest-first. Keep in sync with the
// GRIP10 / GRIP20 discount codes configured in Shopify admin.
var BUNDLE_TIERS = [
  { min: 3, pct: 20, code: 'GRIP20' },
  { min: 2, pct: 10, code: 'GRIP10' }
];
var BUNDLE_MAX_MARK = 3;

function formatMoney(cents) {
  return '$' + (Math.round(cents) / 100).toFixed(2);
}

function getBundleTier(qty) {
  for (var i = 0; i < BUNDLE_TIERS.length; i++) {
    if (qty >= BUNDLE_TIERS[i].min) return BUNDLE_TIERS[i];
  }
  return null;
}

function renderBundleWidget(widget) {
  var mode = widget.dataset.mode;
  var qty = parseInt(widget.dataset.qty, 10) || 0;
  var unitPrice = parseFloat(widget.dataset.unitPrice) || 0;
  var cartTotal = parseFloat(widget.dataset.cartTotal) || 0;
  var total = mode === 'cart' ? cartTotal : unitPrice * qty;
  var tier = getBundleTier(qty);

  var fill = widget.querySelector('[data-bundle-fill]');
  var text = widget.querySelector('[data-bundle-text]');
  var priceBlock = widget.querySelector('[data-bundle-price]');
  var original = widget.querySelector('[data-bundle-original]');
  var discounted = widget.querySelector('[data-bundle-discounted]');
  var codeEl = widget.querySelector('[data-bundle-code]');
  var note = widget.querySelector('[data-bundle-note]');

  if (fill) fill.style.width = Math.min(100, (qty / BUNDLE_MAX_MARK) * 100) + '%';

  if (tier) {
    widget.classList.add('is-unlocked');
    widget.dataset.activeCode = tier.code;
    var discountedTotal = total * (1 - tier.pct / 100);
    if (text) text.textContent = "You've unlocked " + tier.pct + '% off!';
    if (priceBlock) priceBlock.hidden = false;
    if (original) original.textContent = formatMoney(total);
    if (discounted) discounted.textContent = formatMoney(discountedTotal);
    if (codeEl) codeEl.textContent = 'Code ' + tier.code;
    if (note) {
      note.textContent = mode === 'cart'
        ? "We'll apply " + tier.code + ' automatically when you head to checkout.'
        : 'Add to cart, then use code ' + tier.code + ' at checkout.';
    }
  } else {
    widget.classList.remove('is-unlocked');
    delete widget.dataset.activeCode;
    var nextTier = BUNDLE_TIERS[BUNDLE_TIERS.length - 1];
    var remaining = Math.max(0, nextTier.min - qty);
    if (text) {
      text.textContent = remaining > 0
        ? 'Add ' + remaining + ' more to unlock ' + nextTier.pct + '% off'
        : 'Add more to unlock bundle savings';
    }
    if (priceBlock) priceBlock.hidden = true;
  }
}

function updateCartLine(key, quantity, lineEl) {
  fetch('/cart/change.js', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ id: key, quantity: quantity })
  })
    .then(function (res) { return res.json(); })
    .then(function (cart) {
      if (quantity === 0 || cart.item_count === 0) {
        window.location.reload();
        return;
      }

      if (lineEl) {
        var updatedItem = null;
        for (var i = 0; i < cart.items.length; i++) {
          if (cart.items[i].key === key) { updatedItem = cart.items[i]; break; }
        }
        if (updatedItem) {
          var priceEl = lineEl.querySelector('[data-line-price]');
          if (priceEl) priceEl.textContent = formatMoney(updatedItem.final_line_price);
        } else {
          lineEl.remove();
        }
      }

      var subtotalEl = document.querySelector('[data-cart-subtotal]');
      if (subtotalEl) subtotalEl.textContent = formatMoney(cart.total_price);

      var countEl = document.getElementById('CartCount');
      if (countEl) {
        countEl.textContent = cart.item_count;
        countEl.hidden = cart.item_count === 0;
        countEl.classList.remove('is-bumping');
        void countEl.offsetWidth;
        countEl.classList.add('is-bumping');
      }

      var cartWidget = document.querySelector('[data-bundle-progress][data-mode="cart"]');
      if (cartWidget) {
        cartWidget.dataset.qty = cart.item_count;
        cartWidget.dataset.cartTotal = cart.total_price;
        renderBundleWidget(cartWidget);
      }
    })
    .catch(function () {
      // Network hiccup — fall back to a normal full-page cart update.
      var form = lineEl && lineEl.closest('form');
      if (form) form.submit();
    });
}

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
      if (main && thumb.dataset.fullSrc) {
        main.removeAttribute('srcset');
        main.src = thumb.dataset.fullSrc;
        main.classList.remove('is-swapping');
        void main.offsetWidth;
        main.classList.add('is-swapping');
      }
      document.querySelectorAll('[data-thumb]').forEach(function (t) { t.classList.remove('is-active'); });
      thumb.classList.add('is-active');
    });
  });

  // Ripple feedback on tappable controls
  var rippleTargets = '.icon-btn, .btn, .copy-btn, .product-thumb, .qty-stepper button, .deal-summary';
  document.querySelectorAll(rippleTargets).forEach(function (el) {
    el.classList.add('ripple-host');
    el.addEventListener('pointerdown', function (e) {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      var rect = el.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      el.appendChild(ripple);
      ripple.addEventListener('animationend', function () { ripple.remove(); });
    });
  });

  // Cart line quantity changes go through the AJAX Cart API so totals and
  // the bundle-savings widget update live, without a full page reload.
  document.querySelectorAll('[data-cart-qty]').forEach(function (input) {
    input.addEventListener('change', function () {
      var line = input.closest('[data-cart-line]');
      var key = line && line.dataset.lineKey;
      var quantity = Math.max(0, parseInt(input.value, 10) || 0);
      if (!key) return;
      updateCartLine(key, quantity, line);
    });
  });

  // Product-page bundle widget: recompute purely client-side from the
  // known unit price whenever the quantity stepper changes.
  document.querySelectorAll('[data-bundle-progress][data-mode="product"]').forEach(function (widget) {
    var form = widget.closest('form');
    var qtyInput = form && form.querySelector('#Quantity');
    renderBundleWidget(widget);
    if (qtyInput) {
      qtyInput.addEventListener('change', function () {
        widget.dataset.qty = Math.max(1, parseInt(qtyInput.value, 10) || 1);
        renderBundleWidget(widget);
      });
      qtyInput.addEventListener('input', function () {
        widget.dataset.qty = Math.max(1, parseInt(qtyInput.value, 10) || 1);
        renderBundleWidget(widget);
      });
    }
  });

  // Cart-page bundle widget: render initial state from the cart totals
  // Liquid already embedded in its data attributes.
  document.querySelectorAll('[data-bundle-progress][data-mode="cart"]').forEach(function (widget) {
    renderBundleWidget(widget);
  });

  // If a bundle tier is unlocked when the shopper checks out, route them
  // through Shopify's code-application URL first so the discount is
  // already applied by the time they reach checkout.
  var cartForm = document.getElementById('CartForm');
  if (cartForm) {
    cartForm.addEventListener('submit', function (e) {
      var widget = document.querySelector('[data-bundle-progress][data-mode="cart"]');
      var code = widget && widget.dataset.activeCode;
      if (code) {
        e.preventDefault();
        window.location.href = '/discount/' + encodeURIComponent(code) + '?redirect=' + encodeURIComponent('/checkout');
      }
    });
  }

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

// ---------- AJAX add-to-cart + slide-out cart drawer ----------
// Hyper-style pattern: add to cart without a full page reload, and open
// a slide-out panel showing the real, current cart state (fetched fresh
// from Shopify's /cart.js each time, never assembled from stale data).

function bumpCartCount() {
  var count = document.querySelector('.cart-count');
  if (!count) return;
  count.classList.remove('is-bumping');
  void count.offsetWidth;
  count.classList.add('is-bumping');
}

function renderCartDrawer(cart) {
  var drawer = document.getElementById('CartDrawer');
  if (!drawer) return;

  var itemsEl = drawer.querySelector('[data-cart-drawer-items]');
  var footerEl = drawer.querySelector('[data-cart-drawer-footer]');
  var subtotalEl = drawer.querySelector('[data-cart-drawer-subtotal]');
  var countEl = document.getElementById('CartCount');

  if (countEl) {
    countEl.textContent = cart.item_count;
    countEl.hidden = cart.item_count === 0;
  }

  if (!cart.items.length) {
    itemsEl.innerHTML = '<p class="cart-drawer__empty">Your cart is empty.</p>';
    if (footerEl) footerEl.hidden = true;
  } else {
    itemsEl.innerHTML = cart.items.map(function (item) {
      var img = item.image ? '<img src="' + item.image.replace(/(\.[a-z]+)(\?|$)/i, '_100x$2') + '" alt="" loading="lazy">' : '';
      var variant = item.variant_title ? '<p class="cart-drawer__line-variant">' + item.variant_title + '</p>' : '';
      return (
        '<div class="cart-drawer__line" data-drawer-line data-line-key="' + item.key + '">' +
          img +
          '<div>' +
            '<p class="cart-drawer__line-title">' + item.product_title + '</p>' +
            variant +
            '<div class="cart-drawer__line-controls">' +
              '<span class="cart-drawer__line-qty">' +
                '<button type="button" data-drawer-qty-minus aria-label="Decrease quantity">&minus;</button>' +
                '<span>' + item.quantity + '</span>' +
                '<button type="button" data-drawer-qty-plus aria-label="Increase quantity">&plus;</button>' +
              '</span>' +
              '<button type="button" class="cart-drawer__line-remove" data-drawer-remove>Remove</button>' +
            '</div>' +
          '</div>' +
          '<span class="cart-drawer__line-price">' + formatMoney(item.final_line_price) + '</span>' +
        '</div>'
      );
    }).join('');
    if (footerEl) footerEl.hidden = false;
    if (subtotalEl) subtotalEl.textContent = formatMoney(cart.total_price);
  }

  var shipping = drawer.querySelector('[data-cart-shipping]');
  if (shipping) {
    var threshold = parseFloat(shipping.dataset.threshold) * 100;
    var fill = shipping.querySelector('[data-shipping-fill]');
    var text = shipping.querySelector('[data-shipping-text]');
    var pct = Math.min(100, (cart.total_price / threshold) * 100);
    if (fill) fill.style.width = pct + '%';
    if (text) {
      text.textContent = cart.total_price >= threshold
        ? "You've unlocked free shipping!"
        : 'Add ' + formatMoney(threshold - cart.total_price) + ' more for free shipping';
    }
  }
}

function fetchAndRenderCart() {
  return fetch('/cart.js', { headers: { Accept: 'application/json' } })
    .then(function (res) { return res.json(); })
    .then(function (cart) { renderCartDrawer(cart); return cart; });
}

function openCartDrawer() {
  var drawer = document.getElementById('CartDrawer');
  if (!drawer) { window.location.href = '/cart'; return; }
  drawer.classList.add('is-open');
  drawer.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}

function closeCartDrawer() {
  var drawer = document.getElementById('CartDrawer');
  if (!drawer) return;
  drawer.classList.remove('is-open');
  drawer.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', function () {
  var drawer = document.getElementById('CartDrawer');

  // Header cart icon opens the drawer instead of navigating (falls back
  // to a normal link to /cart if the drawer isn't on the page).
  document.querySelectorAll('[data-cart-drawer-open]').forEach(function (link) {
    if (!drawer) return;
    link.addEventListener('click', function (e) {
      e.preventDefault();
      fetchAndRenderCart().then(openCartDrawer);
    });
  });

  if (drawer) {
    drawer.querySelectorAll('[data-cart-drawer-close]').forEach(function (btn) {
      btn.addEventListener('click', closeCartDrawer);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) closeCartDrawer();
    });

    // Quantity +/- and remove inside the drawer
    drawer.addEventListener('click', function (e) {
      var line = e.target.closest('[data-drawer-line]');
      if (!line) return;
      var key = line.dataset.lineKey;
      var qtySpan = line.querySelector('.cart-drawer__line-qty span');
      var current = parseInt(qtySpan.textContent, 10) || 0;
      var next = null;

      if (e.target.closest('[data-drawer-qty-plus]')) next = current + 1;
      else if (e.target.closest('[data-drawer-qty-minus]')) next = Math.max(0, current - 1);
      else if (e.target.closest('[data-drawer-remove]')) next = 0;
      else return;

      fetch('/cart/change.js', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ id: key, quantity: next })
      })
        .then(function (res) { return res.json(); })
        .then(function (cart) { renderCartDrawer(cart); });
    });
  }

  // Intercept product-form add-to-cart submissions for an AJAX add, then
  // open the drawer instead of reloading to the cart page.
  document.addEventListener('submit', function (e) {
    if (!e.target.matches('form[action*="/cart/add"]')) return;
    if (!drawer) return; // no drawer on the page - let the form submit normally

    e.preventDefault();
    var form = e.target;
    var formData = new FormData(form);
    var submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    fetch('/cart/add.js', { method: 'POST', headers: { Accept: 'application/json' }, body: formData })
      .then(function (res) { return res.json(); })
      .then(function () {
        bumpCartCount();
        return fetchAndRenderCart();
      })
      .then(openCartDrawer)
      .catch(function () { form.submit(); }) // network hiccup - fall back to a normal submit
      .finally(function () { if (submitBtn) submitBtn.disabled = false; });
  });

  // ---------- Sticky add-to-cart bar (product pages) ----------
  var stickyBar = document.querySelector('[data-sticky-atc]');
  var sentinel = document.querySelector('[data-atc-sentinel]');
  if (stickyBar && sentinel && 'IntersectionObserver' in window) {
    var atcObserver = new IntersectionObserver(function (entries) {
      var entry = entries[0];
      var scrolledPast = !entry.isIntersecting && entry.boundingClientRect.top < 0;
      stickyBar.classList.toggle('is-visible', scrolledPast);
      stickyBar.setAttribute('aria-hidden', String(!scrolledPast));
    }, { threshold: 0 });
    atcObserver.observe(sentinel);
  }
});
