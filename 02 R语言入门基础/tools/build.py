"""Build a completely local, independent R textbook; never run its examples."""
from pathlib import Path
import html
import json
import re
import shutil
import zipfile
from markdown_it import MarkdownIt
from draw import FIGURES, main as draw
from atlas import render_atlas

ROOT = Path(__file__).resolve().parents[1]
MD = MarkdownIt('commonmark', {'html': True}).enable('table')
E = html.escape
COURSE = json.loads((ROOT/'content/course.json').read_text())
LESSONS = COURSE['lessons']
TERMS = json.loads((ROOT/'content/glossary.json').read_text())
TERM_MAP = {t['id']:t for t in TERMS}
PLOTS = json.loads((ROOT/'content/plots.json').read_text())


def link(path,base=''):
    return E(base+path,quote=True)


def codeblock(source,label='R · 在 r-lab 项目中运行',download=None,output=None):
    header=f'<div class="code-label"><span>{E(label)}</span><button type="button" class="copy-code">复制</button></div>'
    code=f'<div class="code-box">{header}<pre><code>{E(source.rstrip())}</code></pre></div>'
    if output is not None:
        code+=f'<div class="output-box"><span>参考输出</span><pre>{E(output.rstrip())}</pre></div>'
    if download:
        code+=f'<p class="source-link"><a href="{E(download)}" download>下载本节 R 脚本 ↓</a></p>'
    return code


def glossary_entry(t):
    backlinks=' · '.join(f'<a href="lessons/{ident}.html">第 {ident} 节</a>' for ident in t['lessons'])
    related=' · '.join(f'<a data-term="{ident}" href="#term-{ident}">{E(TERM_MAP[ident]["zh"])}</a>' for ident in t.get('related',[]))
    return (f'<article class="term-entry" id="term-{t["id"]}"><p class="eyebrow">{E(t["category"])}</p>'
            f'<h3>{E(t["zh"])} <span lang="en">{E(t["en"])}</span></h3><p>{E(t["summary"])}</p>'
            f'<h4>放进例子里</h4><p>{E(t["example"])}</p><h4>在本课里有什么用</h4><p>{E(t["in_course"])}</p><h4>容易混淆的地方</h4><p>{E(t["pitfall"])}</p><h4>接着理解</h4><p>{related}</p><p class="term-backlinks">回到使用处：{backlinks}</p></article>')


def render(source,base='',section=''):
    # Protect code blocks from glossary and authoring-marker transformations.
    saved=[]
    def stash(value):
        saved.append(value)
        return f'\n\n@@BLOCK{len(saved)-1}@@\n\n'
    def fence(m):
        lang=m[1].strip()
        label={'r':'R · 输入代码','bash':'终端 · 维护命令','text':'示意内容，不作为代码执行'}.get(lang,'示例')
        return stash(codeblock(m[2],label))
    source=re.sub(r'^```([^\n]*)\n(.*?)^```\s*$',fence,source,flags=re.M|re.S)
    def snippet(m):
        ident=m[1]
        src=ROOT/'practice/r-lab/lessons'/f'{ident}.R'
        out=ROOT/'practice/expected'/f'{ident}.txt'
        if not src.is_file() or not out.is_file():raise ValueError(f'Missing verified example: {ident}')
        return stash(codeblock(src.read_text(),download=base+f'practice/r-lab/lessons/{ident}.R',output=out.read_text()))
    source=re.sub(r'\{\{code:([a-z0-9-]+)\}\}',snippet,source)
    def fullsource(m):
        name=m[1]
        src=ROOT/'practice/r-lab/scripts'/name
        return stash(f'<details class="full-source"><summary>查看完整脚本：{E(name)}</summary>'+codeblock(src.read_text(),download=base+'practice/r-lab/scripts/'+name)+'</details>')
    source=re.sub(r'\{\{source:([a-zA-Z0-9.-]+)\}\}',fullsource,source)
    def fig(m):
        name=m[1]; title,desc=FIGURES[name]; url=base+f'assets/illustrations/{name}.svg'
        return stash(f'<figure class="concept"><p class="eyebrow">图解 · {E(title)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}"><img src="{url}" alt="{E(title)}" loading="lazy" width="920" height="440"></a><figcaption><strong>怎样读这幅图</strong><p>{E(desc)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}">放大查看 ↗</a> <a href="{url}" download>保存 SVG ↓</a></figcaption></figure>')
    source=re.sub(r'\{\{figure:([a-z]+)\}\}',fig,source)
    def plot(m):
        name=m[1]; info=PLOTS[name]; url=base+f'assets/plots/{name}.png'
        if not (ROOT/f'assets/plots/{name}.png').is_file(): raise ValueError(f'Missing R plot: {name}')
        title,desc=info['title'],info['description']
        return stash(f'<figure class="concept statistical-plot"><p class="eyebrow">R 实际生成 · {E(title)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}"><img src="{url}" alt="{E(title)}" loading="lazy"></a><figcaption><p>{E(desc)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}">放大查看 ↗</a> · <a href="{url}" download>下载图片 ↓</a></figcaption></figure>')
    source=re.sub(r'\{\{plot:([a-z0-9-]+)\}\}',plot,source)
    def exercise(m):
        title,task,hint,answer=m.groups()
        return stash(f'<section class="exercise"><p class="eyebrow">动手试试</p><h3>{E(title)}</h3>{MD.render(task)}<details><summary>给我一点提示</summary>{MD.render(hint)}</details><details><summary>查看参考解法与解释</summary>{MD.render(answer)}</details></section>')
    source=re.sub(r'\{\{exercise:([^}]+)\}\}(.*?)\{\{hint:([^}]+)\}\}\s*\{\{answer:([^}]+)\}\}',exercise,source,flags=re.S)
    def term(m):
        ident,label=m.groups()
        if ident not in TERM_MAP:raise ValueError(f'Unknown term: {ident}')
        return f'<a class="term" data-term="{ident}" href="{base}reading.html#term-{ident}">{E(label)}</a>'
    source=re.sub(r'\[\[([a-z]+)\|([^]]+)\]\]',term,source)
    rendered=MD.render(source)
    for i,value in enumerate(saved):rendered=rendered.replace(f'<p>@@BLOCK{i}@@</p>',value)
    if '{{' in rendered or '@@BLOCK' in rendered:raise ValueError('Unresolved content marker')
    n=[0]
    def heading(m):
        n[0]+=1
        return f'<h2 id="{section}-part-{n[0]}">{m[1]}</h2>'
    return re.sub(r'<h2>(.*?)</h2>',heading,rendered)


def quiz(lesson):
    q=lesson['quiz']; ident=lesson['id']
    opts=''.join(f'<label><input type="radio" name="quiz-{ident}" value="{i}"> <span>{E(v)}</span></label>' for i,v in enumerate(q['options']))
    return f'<section class="quiz" data-answer="{q["answer"]}"><p class="eyebrow">检查一下理解</p><h3>{E(q["question"])}</h3><fieldset><legend class="sr-only">选择一个答案</legend>{opts}</fieldset><button type="button" class="check-quiz">检查答案</button><p class="quiz-status" aria-live="polite"></p><details><summary>查看解释</summary><p>{E(q["explanation"])}</p></details></section>'


def page(title,body,base='',lesson=None,kind=''):
    ident=f' data-lesson="{lesson}"' if lesson else ''
    cats=''.join(f'<option>{E(c)}</option>' for c in dict.fromkeys(t['category'] for t in TERMS))
    asset_version='?v='+E(COURSE['version'],quote=True)
    atlas_style=f'<link rel="stylesheet" href="assets/atlas.css{asset_version}">' if kind=='home-page' else ''
    atlas_script=f'<script src="assets/atlas.js{asset_version}"></script>' if kind=='home-page' else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="独立的 R 入门教材。从对象、表格和图形走向抽样、检验与回归；包含完整数据、脚本与术语。"><title>{E(title)} · R 入门</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23256187'/%3E%3Ctext x='9' y='43' font-size='35' fill='white'%3ER%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="{base}assets/style.css{asset_version}">{atlas_style}</head>
<body class="{kind}" data-base="{base}" data-lesson-ids="{",".join(l["id"] for l in LESSONS)}"{ident}><a class="skip-link" href="#main">跳到正文</a><header class="site-header"><a class="brand" href="{base}index.html"><span class="brand-icon" aria-hidden="true">R</span><span>R 入门<small>数据调查小镇</small></span></a><nav aria-label="教材导航"><a href="{base}index.html#course">学习地图</a><a href="{base}library.html">代码与资料</a><a href="{base}reading.html">全文阅读</a><a class="open-glossary" href="{base}reading.html#glossary">术语手册</a></nav></header>{body}
<footer class="site-footer"><span>R 入门 · v{COURSE['version']}<br>从一份记录，走向有依据的解释。</span><a href="{base}library.html#sources">资料与来源</a><a href="{base}README.md">使用与维护说明</a></footer>
<dialog id="glossary-dialog" aria-labelledby="glossary-title"><header class="dialog-header"><div><p class="eyebrow">随时查，接着读</p><h2 id="glossary-title">随身术语手册</h2></div><button type="button" data-close="glossary-dialog" aria-label="关闭术语手册">关闭 ×</button></header><div class="glossary-tools"><label>搜索中文、英文或别名<input type="search" id="term-query" placeholder="例如：缺失值、vector、置信区间" autocomplete="off"></label><label>主题<select id="term-category"><option value="">全部主题</option>{cats}</select></label><button type="button" id="all-terms">查看全部</button></div><p id="term-status" aria-live="polite"></p><div id="term-results"></div></dialog>
<dialog id="image-dialog" aria-labelledby="image-title"><header class="dialog-header"><h2 id="image-title">放大图解</h2><button type="button" data-close="image-dialog" aria-label="关闭放大图解">关闭 ×</button></header><div class="zoom-stage"><img id="zoom-target" alt=""></div><p id="image-description"></p></dialog><p id="toast" role="status" aria-live="polite"></p><script src="{base}assets/glossary-data.js{asset_version}"></script><script src="{base}assets/app.js{asset_version}"></script>{atlas_script}</body></html>'''


def archive(path,files,prefix=''):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for src,name in sorted(files,key=lambda x:x[1]):
            info=zipfile.ZipInfo(prefix+name,(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            z.writestr(info,src.read_bytes())


def main():
    draw()
    lab=ROOT/'practice/r-lab'
    archive(ROOT/'practice/r-lab.zip',[(p,'r-lab/'+p.relative_to(lab).as_posix()) for p in lab.rglob('*') if p.is_file() and not {'.Rproj.user','.cache'}.intersection(p.relative_to(lab).parts) and ('results' not in p.relative_to(lab).parts or p.name=='README.md')])
    (ROOT/'assets/glossary-data.js').write_text('window.GLOSSARY='+json.dumps([dict(t,html=glossary_entry(t)) for t in TERMS],ensure_ascii=False,separators=(',',':'))+';\n')
    intro='''<main id="main"><section class="atlas-intro"><div><p class="eyebrow">从零开始 / R · 数据 · 统计</p><h1>走进小镇，<br>用 R 读懂数据。</h1><p class="intro-description">从第一行 R 代码，到一张读得懂的图，<br>再到一份说得清依据的分析简报。</p><div class="hero-actions"><a class="primary" id="continue-link" href="lessons/01.html">走进小镇 ↗</a><a href="practice/r-lab.zip" download>领取调查材料 ↓</a></div></div><aside class="expedition-note" aria-label="这次的调查"><p class="eyebrow">一份公园记录，八个学习街区</p><strong>数据里有线索，<br>结论里要有依据。</strong><p>36 节循序渐进的短课<br>整理 · 绘图 · 抽样 · 检验 · 回归</p></aside></section><section class="atlas-section" id="course" aria-labelledby="atlas-title"><div class="atlas-toolbar"><div><p class="eyebrow">按编号前进，也可以随时回查</p><h2 id="atlas-title">数据调查小镇</h2></div><div class="atlas-controls" id="atlas-controls" hidden><div class="atlas-view-switch" role="group" aria-label="课程查看方式"><button type="button" data-atlas-view="map" aria-pressed="true" aria-controls="atlas-map">地图</button><button type="button" data-atlas-view="directory" aria-pressed="false" aria-controls="map-directory">目录</button></div><button type="button" id="atlas-motion" aria-pressed="false">暂停动态</button></div></div><div class="atlas-help"><p>选择街区，再从路牌进入课程。手机上沿纵向街道阅读。</p><p id="progress-summary" role="status">已读 0 / 36 节</p></div>'''
    intro+=render_atlas(LESSONS,COURSE['zones'])
    intro+='''<div class="atlas-legend" id="atlas-legend"><span><b class="legend-next">→</b>建议下一站</span><span><b class="legend-read">✓</b>已经读过</span><span><b>↗</b>随时可进入</span><span class="legend-note">阅读位置保存在当前浏览器</span></div><noscript><p class="atlas-noscript">现在显示静态地图和全部课程，仍可正常打开章节与查阅词条。</p></noscript><div id="map-directory" class="map-directory" aria-label="全部课程目录">'''
    for z in COURSE['zones']:
        intro+=f'<section class="stage"><div class="stage-label"><h3>{E(z["title"])}</h3><p>{E(z["subtitle"])}</p></div><ol class="lesson-list">'
        for l in LESSONS:
            if l['zone']!=z['id']:continue
            intro+=f'<li><a href="lessons/{l["id"]}.html" data-course-lesson="{l["id"]}"><span class="lesson-number">{l["id"]}</span><div><h4>{E(l["title"])}</h4><p>{E(l["question"])}</p></div><span class="lesson-time">约 {l["minutes"]} 分钟 ↗</span></a></li>'
        intro+='</ol></section>'
    intro+='</div></section><section class="start-note"><h2>把教材和整个练习项目一起带走。</h2><p>正文、图解、术语和参考结果都可离线阅读。实际练习在自己的 R 环境中运行，数据和脚本已随包提供。所有案例均为模拟教学资料；第 02 节从软件安装开始，不要求先学其他课程。</p><a href="library.html">查看完整下载、环境准备与资料来源 →</a></section></main>'
    (ROOT/'index.html').write_text(page('数据调查小镇',intro,kind='home-page'))
    reading='<main id="main" class="reading-page prose"><p class="eyebrow">R 入门 · 连续阅读</p><h1>从一份记录，到有依据的解释。</h1><p>36 节完整正文，术语在末尾可查。打印时自动展开练习解析。代码由真实 R 环境验证，网页不代替 R 执行代码。</p><button type="button" class="print-button">打印这份教材</button><nav class="reading-directory">'+''.join(f'<a href="#lesson-{l["id"]}">{l["id"]} · {E(l["title"])}</a>' for l in LESSONS)+'</nav>'
    for i,l in enumerate(LESSONS):
        src=(ROOT/'content/lessons'/f'{l["id"]}.md').read_text()
        pre=f'<p class="eyebrow">第 {l["id"]} 节 · {E(l["stage"])}</p><h1>{E(l["title"])}</h1><p class="lesson-question">{E(l["question"])}</p><div class="objectives"><strong>这一节，带走什么</strong><p>{E(l["objectives"])}</p></div>'
        body=render(src,'../',l['id'])+quiz(l)
        toc=''.join(f'<a href="#{hid}">{re.sub("<[^>]+>","",label)}</a>' for hid,label in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body))
        prev=f'<a href="{LESSONS[i-1]["id"]}.html">← 上一节</a>' if i else '<a href="../index.html#course">← 返回地图</a>'
        nxt=f'<a href="{LESSONS[i+1]["id"]}.html">下一节 →</a>' if i<len(LESSONS)-1 else '<a href="../index.html#course">返回地图 →</a>'
        controls=f'<nav class="lesson-navigation">{prev}<button type="button" id="mark-read">标记本节已读</button>{nxt}</nav>'
        note='<p class="runtime-note">运行位置：打开练习包内的 r-lab.Rproj，在项目根目录运行本节脚本。安装与准备见第 02—04 节；第 13 节说明扩展包。</p>' if i>=4 else ''
        shell=f'<main id="main" class="lesson-layout"><aside class="lesson-aside"><a href="../index.html#course">← 返回地图</a><p class="eyebrow">本节路线</p><nav>{toc}</nav><a href="../practice/r-lab.zip" download>练习材料 ↓</a><button type="button" id="focus-mode" aria-pressed="false">专注阅读</button></aside><article class="prose lesson-body">{pre}<details class="mobile-toc"><summary>本节目录</summary><nav>{toc}</nav></details>{note}{body}{controls}</article></main>'
        (ROOT/'lessons'/f'{l["id"]}.html').write_text(page(l['title'],shell,'../',l['id'],'lesson-page'))
        reading+=f'<section id="lesson-{l["id"]}" class="print-lesson">{pre}{render(src,"",l["id"])}{quiz(l)}</section>'
    reading+='<section id="glossary"><h1>随身术语手册</h1>'+''.join(glossary_entry(t) for t in TERMS)+'</section></main>'
    (ROOT/'reading.html').write_text(page('连续阅读与打印',reading,kind='full-reading'))
    version=COURSE['version']
    library=f'''<main id="main" class="library-page prose"><p class="eyebrow">资料馆 · 放在手边，随时回查</p><h1>代码、数据与整份教材。</h1><p>先下载练习项目，保留 data 原始文件，在 results 中生成新结果。全部数据为原创模拟资料，数字只用于学习，不代表真实研究发现。</p><p><a class="primary" href="practice/r-lab.zip" download>下载练习项目 ZIP ↓</a></p><p><a href="https://github.com/He-qingchuan/BioinformaticsPathfinder/releases/download/r-v{version}/r-v{version}.zip">下载完整离线教材 ZIP ↗</a> · <a href="practice/r-lab/README.md">练习说明与数据字典</a> · <a href="practice/expected/report.md">查看已运行的分析简报</a></p><h2>逐课脚本与参考输出</h2><p>脚本和网页代码来自同一份源文件。基础安装检查从第 02 节开始；完整脚本需要在 r-lab 项目根目录运行。R 原生帮助链接用于核对接口，扩展包安装需要联网。</p><ul class="resource-list">'''
    for p in sorted((ROOT/'practice/r-lab/lessons').glob('*.R')):
        l=next(l for l in LESSONS if l['id']==p.stem)
        library+=f'<li><a href="lessons/{p.stem}.html">{p.stem} · {E(l["title"])}</a><a href="practice/r-lab/lessons/{p.name}" download>R 脚本 ↓</a><a href="practice/expected/{p.stem}.txt">参考输出 ↗</a></li>'
    library+='</ul><h2>完整流程与数据来源</h2><p><a href="practice/r-lab/scripts/analyse.R" download>完整分析函数 ↓</a> · <a href="practice/r-lab/scripts/make_data.R" download>模拟数据生成脚本 ↓</a> · <a href="practice/r-lab/setup.R" download>扩展包安装脚本 ↓</a></p><h2 id="sources">选读附录与原始资料</h2>'+render((ROOT/'content/appendix.md').read_text(),section='appendix')+'</main>'
    (ROOT/'library.html').write_text(page('代码与资料',library))
    print(json.dumps(dict(lessons=len(LESSONS),terms=len(TERMS),concept_figures=len(FIGURES),displayed_R_plots=len(PLOTS),zones=len(COURSE['zones'])),ensure_ascii=False))

if __name__=='__main__':main()
