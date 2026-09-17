"""Build a completely local, independent Linux textbook; never run its examples."""
from pathlib import Path
import html
import json
import re
import shutil
import zipfile
from markdown_it import MarkdownIt
from draw import FIGURES, main as draw

ROOT = Path(__file__).resolve().parents[1]
MD = MarkdownIt('commonmark', {'html': True}).enable('table')
E = html.escape
COURSE = json.loads((ROOT/'content/course.json').read_text())
LESSONS = COURSE['lessons']
TERMS = json.loads((ROOT/'content/glossary.json').read_text())
TERM_MAP = {t['id']:t for t in TERMS}


def link(path,base=''):
    return E(base+path,quote=True)


def codeblock(source,label='Bash · 输入命令',download=None,output=None):
    header=f'<div class="code-label"><span>{E(label)}</span><button type="button" class="copy-code">复制</button></div>'
    code=f'<div class="code-box">{header}<pre><code>{E(source.rstrip())}</code></pre></div>'
    if output is not None:
        code+=f'<div class="output-box"><span>参考输出</span><pre>{E(output.rstrip())}</pre></div>'
    if download:
        code+=f'<p class="source-link"><a href="{E(download)}" download>下载这段命令 ↓</a></p>'
    return code


def glossary_entry(t):
    related=' · '.join(f'<a data-term="{ident}" href="#term-{ident}">{E(TERM_MAP[ident]["zh"])}</a>' for ident in t.get('related',[]))
    return (f'<article class="term-entry" id="term-{t["id"]}"><p class="eyebrow">{E(t["category"])}</p>'
            f'<h3>{E(t["zh"])} <span lang="en">{E(t["en"])}</span></h3><p>{E(t["summary"])}</p>'
            f'<h4>放进例子里</h4><p>{E(t["example"])}</p><h4>在本课里有什么用</h4><p>{E(t["in_course"])}</p><h4>容易混淆的地方</h4><p>{E(t["pitfall"])}</p><h4>接着理解</h4><p>{related}</p></article>')


def lab(name):
    if name=='paths':
        return '''<section class="lab" data-lab="paths"><p class="eyebrow">动手看 · 路径会跟着出发点变化</p><h3>图钉现在在哪里？</h3><label>当前目录 <select id="path-start"><option value=".">linux-lab</option><option value="notes">linux-lab/notes</option><option value="logs">linux-lab/logs</option></select></label><label>输入相对路径 <input id="path-input" value="../tables" spellcheck="false"></label><div class="path-tree" aria-hidden="true"><span data-node=".">linux-lab</span><div><span data-node="notes">notes</span><span data-node="logs">logs</span><span data-node="tables">tables</span></div></div><p class="lab-result" id="path-result" aria-live="polite"></p><p>只演示目录路径解析，不运行命令。先选 notes，再观察 ../tables；回到 linux-lab 后，同一写法会走出练习目录。</p></section>'''
    if name=='glob':
        return '''<section class="lab" data-lab="glob"><p class="eyebrow">动手看 · 一张文件名筛网</p><h3>哪些名字会被选中？</h3><label>选择模式 <select id="glob-pattern"><option>*.txt</option><option>day-??.log</option><option>*</option><option>.*</option></select></label><ul class="filename-list" id="glob-files"></ul><p id="glob-result" class="lab-result" aria-live="polite"></p><p>这里演示固定的一组名字与四种 Bash 常见模式；每个 ? 匹配一个字符。默认 * 不包含以点开头的隐藏名字，不包含子目录中的文件。</p></section>'''
    if name=='pipeline':
        return '''<section class="lab" data-lab="pipeline"><p class="eyebrow">动手看 · 每一站的数据</p><h3>打开或关闭排序，再比较计数</h3><label class="check-label"><input type="checkbox" id="pipe-sort" checked> 先经过 sort</label><div class="pipe-panels"><div><strong>输入</strong><pre>sparrow\nmagpie\nsparrow\nsparrow\nmagpie\nsparrow</pre></div><div><strong id="pipe-middle-label">sort</strong><pre id="pipe-middle"></pre></div><div><strong>uniq -c</strong><pre id="pipe-output"></pre></div></div><p id="pipe-result" class="lab-result" aria-live="polite"></p><p>使用与随包 birds.txt 相同的六条记录；演示相邻行合并。关闭排序后，同一种名称会分散到多组。</p></section>'''
    if name=='permissions':
        rows=''.join('<fieldset><legend>'+label+'</legend>'+''.join(f'<label><input type="checkbox" data-perm="{i}" value="{v}" {"checked" if (i==0 and v in (4,2)) or (i==1 and v==4) else ""}> {name}</label>' for v,name in [(4,'r 读'),(2,'w 写'),(1,'x 执行')])+'</fieldset>' for i,label in enumerate(['所有者','所属组','其他人']))
        return f'<section class="lab" data-lab="permissions"><p class="eyebrow">动手看 · 普通文件的模式位</p><h3>给三组身份分配权限</h3><div class="permission-controls">{rows}</div><p class="lab-result" id="permission-result" aria-live="polite"></p><p>这里只演示普通文件的基本模式位，不修改真实文件，也不包含 ACL 或管理员能力。</p></section>'
    raise ValueError(name)


def render(source,base='',section=''):
    # Protect code blocks from glossary and authoring-marker transformations.
    saved=[]
    def stash(value):
        saved.append(value)
        return f'\n\n@@BLOCK{len(saved)-1}@@\n\n'
    def fence(m):
        lang=m[1].strip()
        label={'bash':'Bash · 输入命令','powershell':'PowerShell · 环境准备','text':'示意内容，不作为命令执行'}.get(lang,'示例')
        return stash(codeblock(m[2],label))
    source=re.sub(r'^```([^\n]*)\n(.*?)^```\s*$',fence,source,flags=re.M|re.S)
    def snippet(m):
        ident=m[1]
        src=ROOT/'practice/snippets'/f'{ident}.sh'
        out=ROOT/'practice/expected'/f'{ident}.txt'
        if not src.is_file() or not out.is_file():raise ValueError(f'Missing verified example: {ident}')
        return stash(codeblock(src.read_text(),download=base+f'practice/snippets/{ident}.sh',output=out.read_text()))
    source=re.sub(r'\{\{code:([a-z0-9-]+)\}\}',snippet,source)
    def fullsource(m):
        name=m[1]
        src=ROOT/'practice/scripts'/name
        return stash(f'<details class="full-source"><summary>查看完整脚本：{E(name)}</summary>'+codeblock(src.read_text(),download=base+'practice/scripts/'+name)+'</details>')
    source=re.sub(r'\{\{source:([a-z0-9.-]+)\}\}',fullsource,source)
    def fig(m):
        name=m[1]; title,desc=FIGURES[name]; url=base+f'assets/illustrations/{name}.svg'
        return stash(f'<figure class="concept"><p class="eyebrow">图解 · {E(title)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}"><img src="{url}" alt="{E(title)}" loading="lazy" width="850" height="370"></a><figcaption><strong>怎样读这幅图</strong><p>{E(desc)}</p><a class="zoom-image" href="{url}" data-description="{E(desc)}">放大查看 ↗</a> <a href="{url}" download>保存 SVG ↓</a></figcaption></figure>')
    source=re.sub(r'\{\{figure:([a-z]+)\}\}',fig,source)
    source=re.sub(r'\{\{lab:([a-z]+)\}\}',lambda m:stash(lab(m[1])),source)
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
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="独立的 Linux 入门教材。用一份观察记录学会路径、文件、文本、管道与简单脚本；含图解、术语和可下载练习。"><title>{E(title)} · Linux 入门</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23163d43'/%3E%3Ctext x='9' y='43' font-size='35' fill='white'%3E%26gt;_%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="{base}assets/style.css"></head>
<body class="{kind}"{ident}><a class="skip-link" href="#main">跳到正文</a><header class="site-header"><a class="brand" href="{base}index.html"><span class="brand-icon" aria-hidden="true">&gt;_</span><span>Linux 入门<small>观察站的工作台</small></span></a><nav aria-label="教材导航"><a href="{base}index.html#course">课程目录</a><a href="{base}library.html">代码与资料</a><a href="{base}reading.html">全文阅读</a><a class="open-glossary" href="{base}reading.html#glossary">术语手册</a></nav></header>{body}
<footer class="site-footer"><span>Linux 入门 · v{COURSE['version']}<br>从一份小记录，走向能解释的操作。</span><a href="{base}library.html#sources">资料与来源</a><a href="{base}README.md">使用与维护说明</a></footer>
<dialog id="glossary-dialog" aria-labelledby="glossary-title"><header class="dialog-header"><div><p class="eyebrow">随时查，接着读</p><h2 id="glossary-title">随身术语手册</h2></div><button type="button" data-close="glossary-dialog" aria-label="关闭术语手册">关闭 ×</button></header><div class="glossary-tools"><label>搜索中文、英文或别名<input type="search" id="term-query" placeholder="例如：路径、Shell、标准输出" autocomplete="off"></label><label>主题<select id="term-category"><option value="">全部主题</option>{cats}</select></label><button type="button" id="all-terms">查看全部</button></div><p id="term-status" aria-live="polite"></p><div id="term-results"></div></dialog>
<dialog id="image-dialog" aria-labelledby="image-title"><header class="dialog-header"><h2 id="image-title">放大图解</h2><button type="button" data-close="image-dialog" aria-label="关闭放大图解">关闭 ×</button></header><div class="zoom-stage"><img id="zoom-target" alt=""></div><p id="image-description"></p></dialog><p id="toast" role="status" aria-live="polite"></p><script src="{base}assets/glossary-data.js"></script><script src="{base}assets/app.js"></script></body></html>'''


def archive(path,files,prefix=''):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for src,name in sorted(files,key=lambda x:x[1]):
            info=zipfile.ZipInfo(prefix+name,(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            z.writestr(info,src.read_bytes())


def main():
    draw()
    for src in (ROOT/'practice/scripts').glob('*.sh'):
        shutil.copyfile(src,ROOT/'practice/linux-lab/tools'/src.name)
    archive(ROOT/'practice/linux-lab.zip',[(p,p.relative_to(ROOT/'practice').as_posix()) for p in (ROOT/'practice/linux-lab').rglob('*') if p.is_file()])
    termdata=[dict(t,html=glossary_entry(t)) for t in TERMS]
    (ROOT/'assets/glossary-data.js').write_text('window.GLOSSARY='+json.dumps(termdata,ensure_ascii=False,separators=(',',':'))+';\n')
    stages=list(dict.fromkeys(l['stage'] for l in LESSONS))
    intro='<main id="main"><section class="hero"><div class="hero-copy"><p class="eyebrow">从零开始 · 一份独立的 Linux 学习教材</p><h1>从一份观察记录，<br>学会和 Linux<br>打交道。</h1><p class="hero-intro">找到文件，读出线索，让小工具合作。<br>从第一条命令开始，把重复的事一点点交给脚本。</p><div class="hero-actions"><a class="primary" id="continue-link" href="lessons/01.html">从这里开始 <span>↗</span></a><a href="practice/linux-lab.zip" download>拿好练习材料 ↓</a></div><p class="hero-note">每一步都有解释、图解和可以亲手验证的小任务。</p></div><figure class="hero-art"><img src="assets/illustrations/workbench.svg" width="850" height="540" alt="观察站的文件柜与终端：从笔记、日志和表格开始练习"><figcaption>今天的工作台上，有一周的记录等你整理。</figcaption></figure></section>'
    intro+='<section class="course-section" id="course"><div class="section-heading"><div><p class="eyebrow">你的学习路线</p><h2>一步一步，把事情做成。</h2></div><p id="progress-summary">18 节短课 · 随时开始，随时回查</p></div><p class="route-intro">推荐按顺序阅读；已经熟悉的部分可以直接跳过。每一节都能用初始材料独立重做。</p>'
    for i,stage in enumerate(stages):
        selected=[l for l in LESSONS if l['stage']==stage]
        intro+=f'<section class="stage"><div class="stage-label"><span>{i+1:02d}</span><h3>{E(stage)}</h3></div><ol class="lesson-list">'
        for l in selected:
            intro+=f'<li><a href="lessons/{l["id"]}.html" data-course-lesson="{l["id"]}"><span class="lesson-number">{l["id"]}</span><div><h4>{E(l["title"])}</h4><p>{E(l["question"])}</p></div><span class="lesson-time">约 {l["minutes"]} 分钟 <b aria-hidden="true">↗</b></span></a></li>'
        intro+='</ol></section>'
    intro+='</section><section class="start-note"><h2>带走方法，也带走整份教材。</h2><p>所有图解、术语、代码和小数据都在包内。下载整个教材后，解压并打开 index.html，即可离线阅读。实际练习在自己的 Linux 环境中进行。</p><a href="library.html">查看练习、命令索引与选读资料 →</a></section></main>'
    (ROOT/'index.html').write_text(page('从一份记录开始',intro,kind='home-page'))
    reading='<main id="main" class="reading-page prose"><p class="eyebrow">Linux 入门 · 连续阅读</p><h1>从第一条命令，到一份观察简报。</h1><p>本页展开所有章节。打印时自动显示练习解析；交互演示附有文字说明。术语可点击查询，禁用脚本时跳到页末附录。</p><button type="button" class="print-button">打印这份教材</button><nav class="reading-directory">'+''.join(f'<a href="#lesson-{l["id"]}">{l["id"]} · {E(l["title"])}</a>' for l in LESSONS)+'</nav>'
    for i,l in enumerate(LESSONS):
        src=(ROOT/'content/lessons'/f'{l["id"]}.md').read_text()
        pre=f'<p class="eyebrow">第 {l["id"]} 节 · {E(l["stage"])}</p><h1>{E(l["title"])}</h1><p class="lesson-question">{E(l["question"])}</p><div class="objectives"><strong>这一节，带走什么</strong><p>{E(l["objectives"])}</p></div>'
        body=render(src,'../',l['id'])+quiz(l)
        toc=''.join(f'<a href="#{hid}">{re.sub("<[^>]+>","",label)}</a>' for hid,label in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body))
        prev=f'<a href="{LESSONS[i-1]["id"]}.html">← 上一节</a>' if i else '<a href="../index.html">← 课程首页</a>'
        nex=f'<a href="{LESSONS[i+1]["id"]}.html">下一节 →</a>' if i<len(LESSONS)-1 else '<a href="../index.html#course">回到课程目录 →</a>'
        controls=f'<nav class="lesson-navigation">{prev}<button type="button" id="mark-read">标记本节已读</button>{nex}</nav>'
        shell=f'<main id="main" class="lesson-layout"><aside class="lesson-aside"><a href="../index.html#course">← 全部课程</a><p class="eyebrow">本节路线</p><nav>{toc}</nav><a href="../practice/linux-lab.zip" download>练习材料 ↓</a><button type="button" id="focus-mode" aria-pressed="false">专注阅读</button></aside><article class="prose lesson-body">{pre}<details class="mobile-toc"><summary>本节目录</summary><nav>{toc}</nav></details>{body}{controls}</article></main>'
        (ROOT/'lessons'/f'{l["id"]}.html').write_text(page(l['title'],shell,'../',l['id'],'lesson-page'))
        reading+=f'<section id="lesson-{l["id"]}" class="print-lesson">{pre}{render(src,"",l["id"])}{quiz(l)}</section>'
    reading+='<section id="glossary"><h1>随身术语手册</h1>'+''.join(glossary_entry(t) for t in TERMS)+'</section></main>'
    (ROOT/'reading.html').write_text(page('连续阅读与打印',reading,kind='full-reading'))
    library='<main id="main" class="library-page prose"><p class="eyebrow">放在手边，随时回查</p><h1>代码、材料与工具索引。</h1><p>下载练习材料并保留原始副本。实际操作使用自己的副本，参考输出用于核对含义；个人路径和动态进程编号会不同。</p><p><a class="primary" href="practice/linux-lab.zip" download>下载练习材料 ZIP ↓</a></p><h2>逐节命令与参考输出</h2><ul class="resource-list">'
    for p in sorted((ROOT/'practice/snippets').glob('*.sh')):
        num=p.name[:2];l=next(x for x in LESSONS if x['id']==num)
        library+=f'<li><a href="lessons/{num}.html">{num} · {E(l["title"])}</a><a href="practice/snippets/{p.name}" download>命令 .sh ↓</a><a href="practice/expected/{p.stem}.txt">参考输出 ↗</a></li>'
    library+='</ul><h2>完整脚本与整本教材</h2><p><a href="practice/scripts/line-count.sh" download>line-count.sh ↓</a> · <a href="practice/scripts/summarize.sh" download>summarize.sh ↓</a></p><p><a href="https://github.com/He-qingchuan/BioinformaticsPathfinder/releases/download/linux-v1.0.0/linux-v1.0.0.zip">下载完整离线教材 ZIP ↗</a>（联网下载；解压后可离线阅读。）</p><h2>按任务找命令</h2><div class="command-index">'
    for name,desc,num in [('pwd / cd / ls','定位与浏览','04'),('mkdir / cp / mv / rm','整理文件','05'),('cat / head / tail / less / wc','查看文本','06'),('nano / > / >> / 2>','编辑与保存','07'),('find / * / ?','查文件名','08'),('grep','搜索文本','09'),('| / sort / uniq','组合工具','10'),('cut / sort -n','处理简单表格','11'),('tar / sha256sum','归档与核对','12'),('chmod / stat','查看与调整权限','13'),('command -v / PATH','查找程序','14'),('jobs / ps / top / df / du','观察运行与资源','15'),('bash / $1 / if / for','简单脚本','16')]:
        library+=f'<a href="lessons/{num}.html"><code>{E(name)}</code><span>{E(desc)}</span></a>'
    library+='</div><h2 id="sources">选读附录与原始资料</h2>'+render((ROOT/'content/appendix.md').read_text(),section='appendix')+'</main>'
    (ROOT/'library.html').write_text(page('代码与资料',library))
    print(json.dumps({'lessons':len(LESSONS),'glossary':len(TERMS),'figures':len(FIGURES)+1,'examples':len(list((ROOT/'practice/snippets').glob('*.sh')))},ensure_ascii=False))


if __name__=='__main__':
    main()
