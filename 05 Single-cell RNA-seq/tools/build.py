#!/usr/bin/env python3
"""功能：只用包内 Markdown、图解和素材重建两入口与资料馆。

目的：课程正文只有一个编辑源，地图、放大讲解与打印同步。
输入：content/*.md/json、case/、assets/；输出：HTML 与浏览器本地 JS。
不读取源研究项目，不执行 Notebook，不重新计算单细胞结果。
"""
from pathlib import Path
import html, json, re, os
from urllib.parse import quote, urlsplit, unquote
import mistune
from glossary import ProseTerms, render_entry, coverage_report

ROOT=Path(__file__).resolve().parents[1]
HOME='01_海岛探险教案.html'; READING='02_完整教案_阅读与打印.html'
MD=mistune.create_markdown(escape=False,plugins=['table'])
E=lambda x:html.escape(str(x),quote=True)
def read(name):return json.loads((ROOT/'content'/name).read_text())
def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
def dump(path,value):save(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def figure(key,figures):
    """原图保持原字节；数字标注和说明作为独立 HTML 层。"""
    f=figures[key]
    sections=''.join(f'<section class="guide-section"><h4>{E(t)}</h4><div class="guide-body">{MD(p)}</div></section>' for t,p in f['sections'])
    sources=''.join(f'<a href="{E(quote(url,safe="/:#%"))}" target="_blank" rel="noopener">{E(label)} ↗</a>' for label,url in f['sources'])
    markers=''.join(f'<button class="figure-marker" style="left:{t[0]}%;top:{t[1]}%" data-tip="{i}" aria-label="读图定位：{E(t[2])}">{i+1}</button>' for i,t in enumerate(f['tips']))
    notes=''.join(f'<li><strong>{i+1} · {E(t[2])}</strong><p>{E(t[3])}</p></li>' for i,t in enumerate(f['tips']))
    return f'''<figure class="real-figure" data-figure="{key}"><div class="figure-kicker">真实结果 · {E(f['scope'])}</div><div class="figure-stage"><img src="{E(f['path'])}" loading="lazy" alt="{E(f['title'])}">{markers}</div><div class="figure-actions"><button data-zoom="{key}">放大读图 ↗</button><button data-annotations aria-pressed="true">隐藏图中标记</button><a href="{E(f['path'])}" download>保存原图 ↓</a></div><figcaption><div class="figure-reading"><div class="figure-summary"><span class="reading-label">先看摘要</span><strong>{E(f['title'])}</strong><p>{E(f['summary'])}</p></div><div class="figure-guide"><p class="reading-label">读图详解 · 按自己的节奏往下读</p>{sections}<div class="figure-sources"><strong>对照原表与实现</strong>{sources}</div></div></div></figcaption><ol class="figure-notes">{notes}</ol></figure>'''

def illustration(key,art):
    a=art[key]
    return f'''<figure class="concept teaching-visual" data-illustration="{key}"><div class="figure-kicker">原理插画 · 教学示意，非测量结果</div><div class="concept-scroll"><img loading="lazy" src="assets/illustrations/{key}.svg" alt="{E(a['title'])}"></div><p class="art-scroll-hint">小屏可横向查看，也可放大阅读。</p><div class="figure-actions"><button data-zoom="{key}">放大原理插画 ↗</button><a href="assets/illustrations/{key}.svg" download>保存 SVG ↓</a></div><figcaption><div class="figure-reading"><div class="figure-summary"><strong>{E(a['title'])}</strong><p>{E(a['summary'])}</p></div><div class="visual-description">{MD(a['description'])}</div></div></figcaption></figure>'''

def flow(station):
    blocks=''
    for i,(title,sub) in enumerate(station['flow']):
        x=12+i*210
        blocks+=f'<g transform="translate({x},14)"><rect width="190" height="108" rx="16" fill="{["#e2eee2","#e1eff4","#f8e9ce","#f2e1d7"][i]}" stroke="#42717b"/><text x="95" y="43" text-anchor="middle" font-size="17">{E(title)}</text><text x="95" y="76" text-anchor="middle" font-size="13">{E(sub)}</text></g>'
        if i<3:blocks+=f'<path d="M{x+194} 66h13m-5-5 5 5-5 5" stroke="#42717b" fill="none"/>'
    return f'<figure class="concept process-visual"><div class="figure-kicker">本站数据流</div><div class="concept-scroll"><svg viewBox="0 0 850 136" role="img" aria-label="{E(station["flow_note"])}" fill="#233f46">{blocks}</svg></div><figcaption>{E(station["flow_note"])}</figcaption></figure>'

def lab(name,figures):
    """教学交互只读小型随包数据，浏览器中的选择不写回研究。"""
    if name=='qc':
        body='<label>线粒体比例上限：<output id="qc-value">20</output>%<input id="qc-slider" type="range" min="5" max="100" step="5" value="20"></label><p id="qc-count" class="lab-result" aria-live="polite"></p><p>仅对历史 cell_qc 表按当前百分比重新计数；不等于执行完整 QC、MAD 或双细胞流程，也不会改变原图和正式结果。</p>'
    elif name=='dot':
        body='<div class="lab-controls"><label>表达细胞比例 <input id="dot-fraction" type="range" min="0" max="100" value="60"></label><label>按基因缩放颜色 <input id="dot-mean" type="range" min="0" max="100" value="40"></label></div><svg width="160" height="140" aria-label="点图编码示意"><circle id="dot-demo" cx="80" cy="70" r="32" fill="#b75b60"/></svg><p id="dot-output" aria-live="polite"></p><p>教学示意：大小回答“多少细胞检测到”，颜色回答“这一基因在不同群体中相对多高”。本控件不模拟 Scanpy 的具体面积映射，也不产生真实表达量。</p>'
    elif name in ('integration','resolution'):
        keys=['int_raw','int_harmony','int_bbknn'] if name=='integration' else ['clusters']
        options=''.join(f'<option value="{figures[k]["path"]}">{E(figures[k]["title"])}</option>' for k in keys)
        if name=='integration':
            body=f'<label>切换已有真实路线图<select id="route-image">{options}</select></label><img id="route-preview" src="{figures[keys[0]]["path"]}" alt="整合方法对照" style="width:100%"><p>三条路线都来自同一历史案例。观察样本混合和结构是否保留；不同 UMAP 的旋转、位移和缩放不能直接比较。</p>'
        else:
            body='<label>查看已保存分辨率<select id="resolution-select"><option>0.02</option><option>0.50</option><option>1.00</option><option>2.00</option></select></label><p id="resolution-result" class="lab-result" aria-live="polite"></p><p>簇数读取历史 summary；没有重新聚类。回到上方四联图和 marker 图比较，簇数不是优劣评分。</p>'
    else:raise ValueError(name)
    return f'<section class="lab" data-lab="{name}"><span class="lab-label">动手读一读 · 不修改正式分析</span>{body}</section>'

def library():
    """保留原课件代码与注释，HTML 不执行代码，缺失本地资源显示解释。"""
    files=sorted(p for p in (ROOT/'case').rglob('*') if p.is_file() and p.suffix in {'.ipynb','.md','.py','.sh'} )
    mapping={p.resolve():ROOT/'library'/p.relative_to(ROOT/'case').with_suffix(p.suffix+'.html') for p in files}
    catalog=[]
    for src,dest in mapping.items():
        raw=src.read_text()
        if src.suffix=='.ipynb':
            nb=json.loads(raw);body=''.join(f'<section><small>单元格 {i}</small>'+ (MD(''.join(c['source'])) if c['cell_type']=='markdown' else '<pre><code>'+E(''.join(c['source']))+'</code></pre>')+'</section>' for i,c in enumerate(nb['cells']))
        elif src.suffix=='.md':body=MD(raw)
        else:body='<pre><code>'+E(raw)+'</code></pre>'
        def link(m):
            url=html.unescape(m[1]);parts=urlsplit(url)
            if parts.scheme in ('http','https','mailto'):return m[0]
            if not parts.path:return m[0]
            target=(src.parent/unquote(parts.path)).resolve();target=mapping.get(target,target)
            if target.is_relative_to(ROOT) and target.is_file():return 'href="'+E(quote(os.path.relpath(target,dest.parent),safe='/')+('#'+parts.fragment if parts.fragment else ''))+'"'
            if target in mapping.values():return 'href="'+E(quote(os.path.relpath(target,dest.parent),safe='/'))+'"'
            return 'data-unbundled="'+E(url)+'" title="该文件属于完整分析项目，未收入独立教程"'
        body=re.sub(r'href="([^"]*)"',link,body)
        # Notebook 的历史嵌入图在精选图解中提供，资料馆保留代码与原始下载。
        body=re.sub(r'<img\b[^>]*>', '<span class="document-note">原文插图请在完整项目或本站精选图解中查看。</span>',body)
        rel=lambda p:quote(os.path.relpath(p,dest.parent),safe='/')
        note='历史执行课件快照：用于核对当时的方法，不直接续跑。' if 'historical' in str(src) else '当前教学模板副本：保留完整代码与注释；本页不执行分析。'
        save(dest,f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(src.name)}</title><link rel="stylesheet" href="{rel(ROOT/"assets/style.css")}"><body class="document-page"><header class="document-header"><a href="{rel(ROOT/HOME)}">海岛地图</a><a href="{rel(ROOT/"library/脚本与资料目录.html")}">资料目录</a><a href="{rel(src)}" download>下载原文</a></header><main class="document-content"><p class="document-note">{note}</p><h1>{E(src.name)}</h1>{body}</main></body></html>')
        catalog.append({'name':src.name,'title':str(src.relative_to(ROOT/'case')),'url':str(dest.relative_to(ROOT)),'raw':str(src.relative_to(ROOT))})
    items=''.join(f'<li><a href="{quote(os.path.relpath(ROOT/c["url"],ROOT/"library"),safe="/")}">{E(c["title"])}</a> <a href="../{quote(c["raw"],safe="/")}" download>原文 ↓</a></li>' for c in catalog)
    save(ROOT/'library/脚本与资料目录.html',f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>单细胞脚本与资料馆</title><link rel="stylesheet" href="../assets/style.css"><body class="document-page"><header class="document-header"><a href="../{HOME}">返回地图</a><a href="../{READING}">全文阅读</a></header><main class="document-content"><h1>资料就在行囊里。</h1><p>{len(catalog)} 份包内资料。current 是当前操作模板，historical 是案例当时的执行快照。网页不执行代码；完整分析仍需要课程环境与输入。</p><ul class="library-list">{items}</ul></main></body></html>')
    return catalog

def main():
    stations=read('stations.json');figures=read('figures.json');art=read('illustrations.json');glossary=read('glossary.json')
    terms=glossary['entries'];term_map={e['id']:e for e in terms};occurrences=[];catalog=library();lessons=[]
    for s in stations:
        source=(ROOT/'content'/f'{s["id"]}.md').read_text()
        source=source.replace('{{flow}}',flow(s))
        source=re.sub(r'\{\{figure:(\w+)\}\}',lambda m:figure(m[1],figures),source)
        source=re.sub(r'\{\{illustration:(\w+)\}\}',lambda m:illustration(m[1],art),source)
        source=re.sub(r'\{\{lab:(\w+)\}\}',lambda m:lab(m[1],figures),source)
        rendered=MD(source);counter=[0]
        def heading(m):
            counter[0]+=1;return f'<h2 id="{s["id"]}-part-{counter[0]}">{m[1]}</h2>'
        rendered=re.sub(r'<h2>(.*?)</h2>',heading,rendered)
        q=s['quiz'];options=''.join(f'<label><input type="radio" name="quiz-{s["id"]}" value="{i}"><span>{E(x)}</span></label>' for i,x in enumerate(q['options']))
        rendered+=f'<section class="quiz" data-answer="{q["answer"]}"><span class="lab-label">本站自测</span><h3>{E(q["question"])}</h3><fieldset><legend class="sr-only">选择答案</legend>{options}</fieldset><button data-check-answer>检查答案</button><p class="quiz-feedback" aria-live="polite"></p><details><summary>查看答案与解析</summary><p>{E(q["explanation"])}</p></details></section>'
        rendered,found=ProseTerms(terms,READING,s['id']).annotate(rendered);occurrences.extend(found)
        lessons.append(dict(s,html=rendered,documents=[c for c in catalog if any(c['name'].startswith(ch+'_') for ch in s['chapters'])]))
    save(ROOT/'assets/lessons.js','window.LESSONS='+json.dumps(lessons,ensure_ascii=False)+';\nwindow.FIGURES='+json.dumps(figures,ensure_ascii=False)+';')
    save(ROOT/'assets/glossary-data.js','window.GLOSSARY='+json.dumps(dict(glossary,entries=[dict(e,html=render_entry(e,term_map,READING)) for e in terms]),ensure_ascii=False)+';')
    dump(ROOT/'content/术语覆盖.json',coverage_report(terms,occurrences))
    dialogs=''.join((ROOT/'tools'/p).read_text() for p in ['image-dialog.html','glossary-dialog.html'])
    text=''.join(f'<section class="print-lesson" id="{s["id"]}"><p class="eyebrow">{E(s["badge"])}</p><h1>{E(s["title"])}</h1>{s["html"]}</section>' for s in lessons).replace('<details>','<details open>')
    # 打印时标题与第一项放在一起，避免标题单独占一页。
    text+= '<section class="glossary-appendix" id="glossary"><div class="glossary-first"><h1>随身术语手册</h1>'+render_entry(terms[0],term_map,READING,appendix=True)+'</div>'+''.join(render_entry(e,term_map,READING,appendix=True) for e in terms[1:])+'</section>'
    nav=''.join(f'<a href="#{s["id"]}">{E(s["title"])}</a>' for s in lessons)+'<a href="#glossary">术语手册</a>'
    save(ROOT/READING,f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>单细胞海岛探险 · 完整教案</title><link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/glossary.css"><body class="document-page static-reading"><header class="document-header"><a href="{HOME}">返回地图</a><a href="library/脚本与资料目录.html">脚本与资料</a><button onclick="window.print()">打印完整教案</button><button id="reading-glossary">查询术语</button></header><main class="document-content"><h1>从一群细胞，读懂身份与差异。</h1><p>固定人类骨髓案例；真实结果与原理示意分开标明。交互实验请在地图中使用，本页保留说明与自测解析。</p><nav class="reading-directory">{nav}</nav>{text}</main>{dialogs}<script src="assets/glossary-data.js"></script><script src="assets/glossary.js"></script><script src="assets/figures.js"></script></body></html>')
    template=(ROOT/'tools/index.template.html').read_text();nodes='';cards=''
    for s in stations:
        icon=f'<svg viewBox="0 0 125 125" aria-hidden="true"><use href="#building-{s["icon"]}"/></svg>'
        label=f'<span class="station-badge">{E(s["badge"])}</span><strong>{E(s["title"])}</strong><small>{E(s["subtitle"])}</small>'
        nodes+=f'<a class="station-node" href="{READING}#{s["id"]}" data-station="{s["id"]}" style="left:{s["x"]/16}%;top:{s["y"]/10.4}%">{icon}<span class="station-caption">{label}</span></a>'
        cards+=f'<a class="station-card" href="{READING}#{s["id"]}" data-station="{s["id"]}">{icon}<div>{label}</div></a>'
    template=template.replace('<!-- SYMBOLS -->',(ROOT/'assets/symbols.svg').read_text()).replace('<!-- STATION NODES -->',nodes).replace('<!-- STATION LIST -->',cards).replace('<!-- IMAGE DIALOG -->',(ROOT/'tools/image-dialog.html').read_text()).replace('<!-- GLOSSARY DIALOG -->',(ROOT/'tools/glossary-dialog.html').read_text()).replace('index.html',HOME).replace('reading.html',READING).replace('library/'+HOME,'library/脚本与资料目录.html').replace('FIGURE_COUNT',str(len(figures)))
    save(ROOT/HOME,template)
    print(json.dumps(dict(stations=len(stations),figures=len(figures),illustrations=len(art),terms=len(terms),documents=len(catalog)),ensure_ascii=False))

if __name__=='__main__':main()
