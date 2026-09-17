'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const terms = window.GLOSSARY || [];
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const glossary = $('glossary-dialog');
  const image = $('image-dialog');
  const key = 'pathfinder-r-read-v1';
  const ids=document.body.dataset.lessonIds.split(',');
  let read = new Set(), storageWorks = true, opener = null, toastTimer;
  function loadProgress(){
    try { const a=JSON.parse(localStorage.getItem(key)||'[]'); read=new Set(Array.isArray(a)?a.filter(x=>ids.includes(x)):[]);storageWorks=true; } catch { storageWorks=false; }
  }
  loadProgress();
  function toast(s){$('toast').textContent=s;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2600);}
  function progress(){
    const next=ids.find(x=>!read.has(x));
    document.querySelectorAll('[data-course-lesson]').forEach(a=>{
      const done=read.has(a.dataset.courseLesson),suggested=a.dataset.courseLesson===next;
      a.classList.toggle('is-read',done);a.classList.toggle('is-next',suggested);
      const state=a.querySelector('.map-state'),symbol=a.querySelector('.map-lesson-status');
      if(state)state.textContent=done?'已读':suggested?'建议下一站':'未读';
      if(symbol)symbol.textContent=done?'✓':suggested?'→':'↗';
    });
    document.querySelectorAll('[data-zone-lessons]').forEach(zone=>{
      const ids=zone.dataset.zoneLessons.split(','),count=ids.filter(id=>read.has(id)).length;
      zone.querySelector('.zone-progress').textContent=`${count} / ${ids.length} 已读`;
      zone.classList.toggle('is-complete',count===ids.length);
    });
    if($('progress-summary')) $('progress-summary').textContent=`已读 ${read.size} / ${ids.length} 节${read.size===ids.length?' · 随时回来看看':''}`;
    if($('continue-link')){$('continue-link').href=next?`lessons/${next}.html`:`lessons/${ids.at(-1)}.html`;$('continue-link').textContent=!read.size?'走进小镇 ↗':next?'继续阅读 →':'再看综合实践 →';}
    if($('mark-read')){$('mark-read').textContent=read.has(document.body.dataset.lesson)?'本节已读 ✓':'标记本节已读';$('mark-read').setAttribute('aria-pressed',String(read.has(document.body.dataset.lesson)));}
    document.dispatchEvent(new CustomEvent('r:progress'));
  }
  progress();
  window.addEventListener('pageshow',()=>{loadProgress();progress();});
  window.addEventListener('storage',event=>{if(event.key===key||event.key===null){loadProgress();progress();}});
  if($('mark-read')) $('mark-read').onclick=()=>{const id=document.body.dataset.lesson;read.has(id)?read.delete(id):read.add(id);try{localStorage.setItem(key,JSON.stringify([...read]));}catch{storageWorks=false;}progress();if(!storageWorks)toast('本次阅读已记录；浏览器限制了跨次保存。');};
  if($('focus-mode')) $('focus-mode').onclick=()=>{const on=document.body.classList.toggle('focus-reading');$('focus-mode').textContent=on?'退出专注阅读':'专注阅读';$('focus-mode').setAttribute('aria-pressed',String(on));};
  function renderTerms(exact){
    const q=$('term-query').value.trim().toLocaleLowerCase(), category=$('term-category').value;
    const shown=exact?terms.filter(t=>t.id===exact):terms.filter(t=>(!category||t.category===category)&&(!q||[t.zh,t.en,...t.aliases].some(s=>s.toLocaleLowerCase().includes(q))));
    $('term-results').innerHTML=shown.map(t=>t.html.replace(/ id="term-[^"]+"/g,'').replaceAll('href="lessons/', 'href="'+(document.body.dataset.base||'')+'lessons/')).join('')||'<p class="term-entry">还没找到这个词。试试中文名、英文名，或查看全部术语。</p>';
    $('term-status').textContent=`找到 ${shown.length} 项解释`;
  }
  function openTerms(trigger,id){
    if(!glossary.open)opener=trigger;$('term-category').value='';$('term-query').value=id?(terms.find(t=>t.id===id)?.zh||''):'';renderTerms(id);
    if(!glossary.open)glossary.showModal();glossary.scrollTop=0;
    if(id){const h=glossary.querySelector('.term-entry h3');if(h){h.tabIndex=-1;h.focus({preventScroll:true});}}else $('term-query').focus({preventScroll:true});
  }
  $('term-query').oninput=()=>renderTerms();$('term-category').onchange=()=>renderTerms();
  $('all-terms').onclick=()=>{$('term-query').value='';$('term-category').value='';renderTerms();$('term-query').focus();};
  for(const dialog of [glossary,image]){dialog.addEventListener('close',()=>{if(opener?.isConnected)opener.focus({preventScroll:true});});}
  document.addEventListener('click',async e=>{
    const close=e.target.closest('[data-close]');if(close){$(close.dataset.close).close();return;}
    const term=e.target.closest('[data-term]');if(term){e.preventDefault();openTerms(term,term.dataset.term);return;}
    const book=e.target.closest('.open-glossary');if(book){e.preventDefault();openTerms(book);return;}
    const zoom=e.target.closest('.zoom-image');if(zoom){e.preventDefault();opener=zoom;$('zoom-target').src=zoom.href;$('zoom-target').alt=zoom.querySelector('img')?.alt||'课程图解';$('image-description').textContent=zoom.dataset.description;image.showModal();return;}
    const copy=e.target.closest('.copy-code');if(copy){const text=copy.closest('.code-box').querySelector('code').textContent;try{await navigator.clipboard.writeText(text);toast('已复制代码。');}catch{const area=document.createElement('textarea');area.value=text;area.style.position='fixed';area.style.opacity='0';document.body.append(area);area.select();const ok=document.execCommand('copy');area.remove();copy.focus({preventScroll:true});toast(ok?'已复制代码。':'浏览器限制了复制，请直接选中代码复制。');}return;}
    const check=e.target.closest('.check-quiz');if(check){const box=check.closest('.quiz'), selected=box.querySelector('input:checked');box.querySelector('.quiz-status').textContent=selected?(selected.value===box.dataset.answer?'理解正确。再看解释，确认理由。':'再想一步，也可以展开解释核对。'):'先选一个答案，或直接查看解释。';if(selected)box.querySelector('details').open=true;}
    if(e.target.closest('.print-button'))window.print();
  });
  // Print includes the complete answers and scripts, regardless of screen disclosure state.
  let folded=[];window.addEventListener('beforeprint',()=>{folded=[...document.querySelectorAll('main details:not([open])')];folded.forEach(x=>x.open=true);});window.addEventListener('afterprint',()=>{folded.forEach(x=>x.open=false);folded=[];});
})();
