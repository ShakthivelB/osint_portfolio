(() => {
  const menu = document.querySelector('#mobile-menu');
  const burger = document.querySelector('.burger');
  const closeMenu = () => {
    if (!menu || !burger) return;
    menu.hidden = true;
    burger.setAttribute('aria-expanded', 'false');
    burger.setAttribute('aria-label', 'Open menu');
    document.body.classList.remove('menu-open');
  };
  if (menu && burger) {
    burger.addEventListener('click', () => {
      const opening = burger.getAttribute('aria-expanded') !== 'true';
      burger.setAttribute('aria-expanded', String(opening));
      burger.setAttribute('aria-label', opening ? 'Close menu' : 'Open menu');
      menu.hidden = !opening;
      document.body.classList.toggle('menu-open', opening);
    });
    menu.addEventListener('click', e => { if (e.target === menu || e.target.closest('a,button')) closeMenu(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
    window.addEventListener('resize', () => { if (window.innerWidth > 720) closeMenu(); });
  }

  const counters = [...document.querySelectorAll('[data-count]')];
  const runCount = el => {
    if (el.dataset.counted) return;
    el.dataset.counted = '1';
    const target = Number(el.dataset.count);
    const decimals = Number(el.dataset.decimals || 0);
    const suffix = el.dataset.suffix || '';
    const start = performance.now() + Number(el.dataset.offset || 0);
    const duration = Number(el.dataset.duration || 1500);
    const tick = now => {
      if (now < start) { requestAnimationFrame(tick); return; }
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target.toFixed(decimals) + suffix;
    };
    requestAnimationFrame(tick);
  };
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { runCount(entry.target); observer.unobserve(entry.target); }
    }), { threshold: 0.25 });
    counters.forEach(el => observer.observe(el));
  } else counters.forEach(runCount);

  const form = document.querySelector('#contact-form');
  if (form) {
    const status = form.querySelector('.form-status');
    form.addEventListener('submit', event => {
      event.preventDefault();
      const data = new FormData(form);
      const name = String(data.get('name') || '').trim();
      const email = String(data.get('email') || '').trim();
      const comment = String(data.get('message') || '').trim();
      const nameField = form.elements.namedItem('name');
      const emailField = form.elements.namedItem('email');
      const commentField = form.elements.namedItem('message');

      nameField.setCustomValidity(name.length < 2 ? 'Please enter your name (at least 2 characters).' : '');
      emailField.setCustomValidity(email ? '' : 'Please enter your email address.');
      commentField.setCustomValidity(comment.length < 10 ? 'Please enter a comment of at least 10 characters.' : '');
      if (!form.reportValidity()) return;

      const body = `Name: ${name}\nEmail: ${email}\n\nComment:\n${comment}`;
      const mailtoUrl = `mailto:shakthisv29@gmail.com?subject=${encodeURIComponent(comment)}&body=${encodeURIComponent(body)}`;
      status.textContent = 'Opening your email app. Review the draft and press Send to contact me.';
      window.location.href = mailtoUrl;
    });
  }
})();
