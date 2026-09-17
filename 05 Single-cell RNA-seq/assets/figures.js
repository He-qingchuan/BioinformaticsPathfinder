'use strict';
// Shared by the map lesson and the continuous reading page. No fetch or remote data.
(() => {
  document.documentElement.classList.add('js');
  const $ = id => document.getElementById(id);
  const dialog = $('image-dialog');
  if (!dialog) return;
  let origin = null;
  const syncBody = () => document.body.classList.toggle('modal-open', !!document.querySelector('dialog[open]'));
  document.addEventListener('click', event => {
    const zoom = event.target.closest('[data-zoom]');
    if (zoom) {
      const figure = zoom.closest('figure');
      const img = figure.querySelector('img');
      const reading = figure.querySelector('.figure-reading');
      origin = zoom;
      $('image-eyebrow').textContent = figure.classList.contains('real-figure') ? '真实结果 · 放大读图' : '原理插图 · 教学示意';
      $('image-title').textContent = figure.querySelector('.figure-summary strong')?.textContent || img.alt;
      $('large-image').src = img.src;
      $('large-image').alt = img.alt;
      $('image-download').href = img.src;
      $('image-caption').innerHTML = reading ? reading.innerHTML : '';
      $('image-scroll').classList.remove('original-size');
      if (!dialog.open) dialog.showModal();
      for (const el of dialog.querySelectorAll('.image-layout,.image-scroll,.image-caption')) el.scrollTop = 0;
      syncBody();
      $('close-image').focus({preventScroll:true});
      return;
    }
    const toggle = event.target.closest('[data-annotations]');
    if (toggle) {
      const hidden = toggle.closest('.real-figure').classList.toggle('annotations-hidden');
      toggle.textContent = hidden ? '显示图中标记' : '隐藏图中标记';
      toggle.setAttribute('aria-pressed', String(!hidden));
      return;
    }
    const marker = event.target.closest('[data-tip]');
    if (marker) {
      const figure = marker.closest('.real-figure');
      figure.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
      marker.classList.add('active');
      const note = figure.querySelectorAll('.figure-notes li')[Number(marker.dataset.tip)];
      if (note) {
        note.classList.add('active');
        note.scrollIntoView({block:'nearest', behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
      }
    }
  });
  $('close-image').onclick = () => dialog.close();
  dialog.addEventListener('cancel', event => {event.preventDefault(); event.stopPropagation(); dialog.close();});
  dialog.addEventListener('close', () => {
    syncBody();
    if (origin?.isConnected) origin.focus({preventScroll:true});
  });
  $('image-fit').onclick = () => $('image-scroll').classList.remove('original-size');
  $('image-original').onclick = () => $('image-scroll').classList.add('original-size');
})();
