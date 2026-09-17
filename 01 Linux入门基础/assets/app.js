'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const terms = window.GLOSSARY || [];
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const glossary = $('glossary-dialog');
  const image = $('image-dialog');
  const key = 'pathfinder-linux-read-v1';
  let read = new Set(), storageWorks = true, opener = null, toastTimer;
  function loadProgress(){
    try { const a=JSON.parse(localStorage.getItem(key)||'[]'); read=new Set(Array.isArray(a)?a.filter(x=>/^\d{2}$/.test(x)&&+x>=1&&+x<=18):[]);storageWorks=true; } catch { storageWorks=false; }
  }
  loadProgress();
  function toast(s){$('toast').textContent=s;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2600);}
  function progress(){
    const next=Array.from({length:18},(_,i)=>String(i+1).padStart(2,'0')).find(x=>!read.has(x));
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
    if($('progress-summary')) $('progress-summary').textContent=`已读 ${read.size} / 18 节${read.size===18?' · 随时回来看看':''}`;
    if($('continue-link')){$('continue-link').href=next?`lessons/${next}.html`:'lessons/18.html';$('continue-link').textContent=!read.size?'从营地出发 ↗':next?'继续阅读 →':'再看综合实践 →';}
    if($('mark-read')){$('mark-read').textContent=read.has(document.body.dataset.lesson)?'本节已读 ✓':'标记本节已读';$('mark-read').setAttribute('aria-pressed',String(read.has(document.body.dataset.lesson)));}
  }
  progress();
  window.addEventListener('pageshow',()=>{loadProgress();progress();});
  window.addEventListener('storage',event=>{if(event.key===key||event.key===null){loadProgress();progress();}});
  if($('mark-read')) $('mark-read').onclick=()=>{const id=document.body.dataset.lesson;read.has(id)?read.delete(id):read.add(id);try{localStorage.setItem(key,JSON.stringify([...read]));}catch{storageWorks=false;}progress();if(!storageWorks)toast('本次阅读已记录；浏览器限制了跨次保存。');};
  if($('focus-mode')) $('focus-mode').onclick=()=>{const on=document.body.classList.toggle('focus-reading');$('focus-mode').textContent=on?'退出专注阅读':'专注阅读';$('focus-mode').setAttribute('aria-pressed',String(on));};
  function renderTerms(exact){
    const q=$('term-query').value.trim().toLocaleLowerCase(), category=$('term-category').value;
    const shown=exact?terms.filter(t=>t.id===exact):terms.filter(t=>(!category||t.category===category)&&(!q||[t.zh,t.en,...t.aliases].some(s=>s.toLocaleLowerCase().includes(q))));
    $('term-results').innerHTML=shown.map(t=>t.html.replace(/ id="term-[^"]+"/g,'')).join('')||'<p class="term-entry">还没找到这个词。试试中文名、英文名，或查看全部术语。</p>';
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
    const copy=e.target.closest('.copy-code');if(copy){const text=copy.closest('.code-box').querySelector('code').textContent;try{await navigator.clipboard.writeText(text);toast('已复制命令。');}catch{const area=document.createElement('textarea');area.value=text;area.style.position='fixed';area.style.opacity='0';document.body.append(area);area.select();const ok=document.execCommand('copy');area.remove();copy.focus({preventScroll:true});toast(ok?'已复制命令。':'浏览器限制了复制，请直接选中代码复制。');}return;}
    const check=e.target.closest('.check-quiz');if(check){const box=check.closest('.quiz'), selected=box.querySelector('input:checked');box.querySelector('.quiz-status').textContent=selected?(selected.value===box.dataset.answer?'理解正确。再看解释，确认理由。':'再想一步，也可以展开解释核对。'):'先选一个答案，或直接查看解释。';if(selected)box.querySelector('details').open=true;}
    if(e.target.closest('.print-button'))window.print();
  });
  function paths(){
    const input=$('path-input').value.trim(), start=$('path-start').value;
    const parts=['linux-lab',...(start==='.'?[]:[start])];
    let outside=false;
    if(input.startsWith('/')||input.startsWith('~')){$('path-result').textContent='此处请试相对路径；以 / 或 ~ 开头的写法不在这个小演示范围内。';return;}
    for(const p of input.split('/')){if(!p||p==='.')continue;if(p==='..'){parts.pop();if(!parts.length)outside=true;}else parts.push(p);}
    const dest=parts.join('/'), rel=parts.slice(1).join('/')||'.';
    document.querySelectorAll('[data-node]').forEach(n=>n.classList.toggle('chosen',!outside&&n.dataset.node===rel));
    $('path-result').textContent=outside?'这条路径走出了 linux-lab。试试从 notes 出发。':`路径指向：${dest}${['.','notes','logs','tables'].includes(rel)?'':'（示意树中未列出这个位置）'}`;
  }
  if($('path-start')){$('path-start').onchange=paths;$('path-input').oninput=paths;paths();}
  function glob(){const names=['morning.txt','evening.txt','day-01.log','day-02.log','.hidden.txt'],pattern=$('glob-pattern').value;const re=new RegExp('^'+pattern.replace(/[.+^${}()|[\]\\]/g,'\\$&').replace(/\*/g,'.*').replace(/\?/g,'.')+'$');const matches=names.filter(n=>(pattern.startsWith('.')||!n.startsWith('.'))&&re.test(n));$('glob-files').innerHTML=names.map(n=>`<li class="${matches.includes(n)?'matched':''}">${escape(n)}</li>`).join('');$('glob-result').textContent=`选中 ${matches.length} 个名字：${matches.join('、')||'无'}`;}
  if($('glob-pattern')){$('glob-pattern').onchange=glob;glob();}
  function pipeline(){const input=['sparrow','magpie','sparrow','sparrow','magpie','sparrow'];const sorted=$('pipe-sort').checked;const data=sorted?[...input].sort():input;const groups=[];for(const value of data){if(groups.at(-1)?.name===value)groups.at(-1).count++;else groups.push({name:value,count:1});}$('pipe-middle').textContent=data.join('\n');$('pipe-middle-label').textContent=sorted?'sort':'保留原顺序';$('pipe-output').textContent=groups.map(g=>`${g.count} ${g.name}`).join('\n');$('pipe-result').textContent=sorted?'相同名称相邻：合并成两组，共六条记录。':'同名记录分散：uniq 只合并紧挨着的重复行。';}
  if($('pipe-sort')){$('pipe-sort').onchange=pipeline;pipeline();}
  function permissions(){let symbolic='',octal='';for(let i=0;i<3;i++){let sum=0;for(const box of document.querySelectorAll(`[data-perm="${i}"]`)){sum+=box.checked?+box.value:0;symbolic+=box.checked?({4:'r',2:'w',1:'x'}[box.value]):'-';}octal+=sum;}$('permission-result').textContent=`符号：${symbolic}　数字：${octal}`;}
  if($('permission-result')){document.querySelectorAll('[data-perm]').forEach(x=>x.onchange=permissions);permissions();}
  // Print includes the complete answers and scripts, regardless of screen disclosure state.
  let folded=[];window.addEventListener('beforeprint',()=>{folded=[...document.querySelectorAll('main details:not([open])')];folded.forEach(x=>x.open=true);});window.addEventListener('afterprint',()=>{folded.forEach(x=>x.open=false);folded=[];});
})();
