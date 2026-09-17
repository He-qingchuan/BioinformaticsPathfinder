'use strict';
(() => {
  const map = document.getElementById('atlas-map');
  if (!map) return;
  const directory = document.getElementById('map-directory');
  const controls = document.getElementById('atlas-controls');
  const motion = document.getElementById('atlas-motion');
  const legend = document.getElementById('atlas-legend');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionKey = 'pathfinder-linux-motion-v1';
  let userPaused = false, inView = false, view = 'map';
  try { userPaused = localStorage.getItem(motionKey) === 'paused'; } catch { /* Static reading needs no storage. */ }

  function updateMotion() {
    const enabled = !userPaused && !reduced.matches;
    map.dataset.motion = enabled && inView && !document.hidden && view === 'map' ? 'playing' : 'paused';
    motion.disabled = reduced.matches;
    motion.textContent = reduced.matches ? '动态已关闭 · 系统' : userPaused ? '开启动态' : '暂停动态';
    motion.setAttribute('aria-pressed', String(!enabled));
    motion.setAttribute('aria-label', reduced.matches ? '系统已设置减少动态效果，地图保持静止' : userPaused ? '开启地图动态' : '暂停地图动态');
  }
  function setView(next) {
    view = next;
    map.hidden = view !== 'map';
    directory.hidden = view !== 'directory';
    legend.hidden = view !== 'map';
    motion.hidden = view !== 'map';
    document.querySelectorAll('[data-atlas-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.atlasView === view)));
    updateMotion();
  }
  controls.hidden = false;
  setView('map');
  document.querySelectorAll('[data-atlas-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.atlasView)));
  motion.addEventListener('click', () => {
    userPaused = !userPaused;
    try { localStorage.setItem(motionKey, userPaused ? 'paused' : 'playing'); } catch { /* Keep the preference for this visit. */ }
    updateMotion();
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; updateMotion(); }, {threshold: 0}).observe(map);
  } else { inView = true; updateMotion(); }
  document.addEventListener('visibilitychange', updateMotion);
  reduced.addEventListener('change', updateMotion);
  window.addEventListener('pageshow', updateMotion);
  window.addEventListener('storage', event => {
    if (event.key === motionKey || event.key === null) {
      try { userPaused = localStorage.getItem(motionKey) === 'paused'; } catch { /* Preserve current state. */ }
      updateMotion();
    }
  });
  for (const zone of map.querySelectorAll('[data-zone]')) {
    const routes = [...map.querySelectorAll(`[data-route-zone="${zone.dataset.zone}"]`)];
    const highlight = on => routes.forEach(route => route.classList.toggle('is-active', on));
    zone.addEventListener('pointerenter', () => highlight(true));
    zone.addEventListener('pointerleave', () => highlight(zone.contains(document.activeElement)));
    zone.addEventListener('focusin', () => highlight(true));
    zone.addEventListener('focusout', event => { if (!zone.contains(event.relatedTarget)) highlight(false); });
  }
})();
