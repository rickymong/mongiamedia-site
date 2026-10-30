// Small enhancements on top of pre-rendered pages: photo strip motion, photo viewer, copy buttons.
const $ = s => document.querySelector(s);
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

// old #gallery links from the previous version of the site
const oldLink = () => { const h = location.hash.slice(1); const t = h && document.querySelector(`[data-gallery="${h}"]`); if (t && !document.getElementById(h)) location.replace(t.getAttribute('href')); };
oldLink(); addEventListener('hashchange', oldLink);

// curved strip: slow constant drift; cards near the edges turn toward the viewer
(() => {
  const box = $('#strip'), track = $('#track'); if (!box) return;
  [...track.children].forEach(c => { const k = c.cloneNode(true); k.setAttribute('aria-hidden', 'true'); k.querySelector('img').alt = ''; track.append(k); });
  const cards = [...track.children]; let x = 0, half = 0, last = performance.now(), speed = 30, target = 30;
  const measure = () => { half = track.scrollWidth / 2 + 6; }; measure(); addEventListener('resize', measure); addEventListener('load', measure);
  box.addEventListener('mouseenter', () => target = 8); box.addEventListener('mouseleave', () => target = 30);
  (function frame(t) {
    const dt = Math.min(64, t - last) / 1000; last = t; speed += (target - speed) * 0.06;
    if (!reduce) x -= speed * dt; if (half && -x > half) x += half;
    track.style.transform = `translate3d(${x}px,0,0)`;
    const W = box.clientWidth, cx = W / 2;
    for (const c of cards) { const d = Math.max(-1.3, Math.min(1.3, (c.offsetLeft + x + c.offsetWidth / 2 - cx) / (W / 2)));
      c.style.transform = `translateZ(${Math.abs(d) * 70}px) rotateY(${-d * 18}deg)`; }
    requestAnimationFrame(frame);
  })(last);
})();

// photo viewer on gallery pages
(() => {
  const grid = $('#gGrid'), v = $('#viewer'); if (!grid || !v) return;
  const items = [...grid.querySelectorAll('a[data-full]')], title = grid.dataset.title;
  let vi = 0, lastFocus = null;
  const show = i => { vi = (i + items.length) % items.length; const a = items[vi];
    $('#vImg').src = a.dataset.full; $('#vImg').alt = a.querySelector('img').alt;
    $('#vCount').textContent = `${title}  ${vi + 1} / ${items.length}`; new Image().src = items[(vi + 1) % items.length].dataset.full; };
  const open = i => { lastFocus = document.activeElement; v.hidden = false; document.body.style.overflow = 'hidden'; show(i); $('#vClose').focus(); };
  const close = () => { v.hidden = true; document.body.style.overflow = ''; if (lastFocus) lastFocus.focus(); };
  items.forEach((a, i) => a.addEventListener('click', e => { if (e.metaKey || e.ctrlKey) return; e.preventDefault(); open(i); }));
  $('#vClose').onclick = close; $('#vPrev').onclick = () => show(vi - 1); $('#vNext').onclick = () => show(vi + 1);
  $('#vStage').addEventListener('click', e => { if (e.target.id === 'vStage') close(); });
  addEventListener('keydown', e => { if (v.hidden) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowRight') show(vi + 1); if (e.key === 'ArrowLeft') show(vi - 1); });
  let tx = null; v.addEventListener('touchstart', e => tx = e.touches[0].clientX, {passive: true});
  v.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) show(vi + (dx < 0 ? 1 : -1)); tx = null; });
})();

// copy buttons in the contact list
document.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', () => {
  const v = b.dataset.copy, done = () => { const t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); t.textContent = 'Copied ' + v; document.body.append(t); setTimeout(() => t.remove(), 1800); };
  try { navigator.clipboard.writeText(v).then(done); } catch (e) {}
}));
