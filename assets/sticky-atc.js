document.addEventListener('DOMContentLoaded', function () {
  var stickyBar = document.querySelector('[data-sticky-atc]');
  var mainBtn = document.querySelector('[data-main-atc-btn]');
  var stickyBtn = document.querySelector('[data-sticky-atc-btn]');
  var form = document.getElementById('AddToCartForm');

  if (stickyBtn && form) {
    stickyBtn.addEventListener('click', function () {
      if (typeof form.requestSubmit === 'function') {
        form.requestSubmit();
      } else {
        form.submit();
      }
    });
  }

  if (stickyBar && mainBtn && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries[0].isIntersecting ? stickyBar.classList.remove('is-visible') : stickyBar.classList.add('is-visible');
    }, { threshold: 0 });
    observer.observe(mainBtn);
  }
});
