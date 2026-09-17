#!/usr/bin/env python3
"""Build pages from bundled materials only. Import new docs explicitly with import_docs.py."""
from pathlib import Path
import csv, html, json, re, os
from urllib.parse import unquote, urlsplit, quote
from markdown_it import MarkdownIt
from glossary import ProseTerms, render_entry, coverage_report

ROOT = Path(__file__).resolve().parents[1]
HOME_PAGE = '01_海岛探险教案.html'
READING_PAGE = '02_完整教案_阅读与打印.html'
LIBRARY_PAGE = '脚本与资料目录.html'
MD = MarkdownIt('commonmark', {'html': True}).enable('table')
def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

FIGURES = json.loads((ROOT/'content/figures.json').read_text())
GUIDES = json.loads((ROOT/'content/figure_guides.json').read_text())
ILLUSTRATIONS = json.loads((ROOT/'content/illustrations.json').read_text())
STATIONS = json.loads((ROOT/'content/stations.json').read_text())
GLOSSARY = json.loads((ROOT/'content/glossary.json').read_text())
TERMS = GLOSSARY['entries']
TERM_MAP = {entry['id']: entry for entry in TERMS}
TERM_OCCURRENCES = []
CONCEPT_NOTES = json.loads((ROOT/'content/concept_notes.json').read_text())

def prepare_data():
    facts=json.loads((ROOT/'case/teaching/facts.json').read_text())
    with (ROOT/'case/teaching/ZT4_vs_ZT0.de_result.tsv').open() as stream:
        de=list(csv.DictReader(stream, delimiter='\t'))
    compact=[{'id':r['gene_id'],'fc':r['log2FoldChange'],'padj':r['padj'],'p':r['pvalue'],'direction':r['direction']} for r in de]
    (ROOT/'assets/case.js').write_text('window.CASE='+json.dumps(facts,ensure_ascii=False,separators=(',',':'))+';\nwindow.DE='+json.dumps(compact,separators=(',',':'))+';\n')
    return facts

def esc(s): return html.escape(str(s),quote=True)
def figure_reading(key):
    f=FIGURES[key]; g=GUIDES[key]
    sections=''.join(f'<section class="guide-section"><h4>{esc(title)}</h4><div class="guide-body">{MD.render(body)}</div></section>' for title,body in g['sections'])
    sources=''.join(f'<a href="{esc(quote(url,safe="/:#%"))}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>' for label,url in g['sources'])
    return f'<div class="figure-reading"><div class="figure-summary"><span class="reading-label">先看摘要</span><strong>{esc(f["title"])}</strong><p>{esc(g["summary"])}</p></div><div class="figure-guide"><p class="reading-label">读图详解 · 按自己的节奏往下读</p>{sections}<div class="figure-sources"><strong>对照包内原表与实现</strong>{sources}</div></div></div>'

def figure(key):
    f=FIGURES[key]
    tips=''.join(f'<li><strong>{i+1} · {esc(t[2])}</strong><p>{esc(t[3])}</p></li>' for i,t in enumerate(f['tips']))
    markers=''.join(f'<button type="button" class="figure-marker" style="left:{t[0]}%;top:{t[1]}%" data-tip="{i}" aria-label="读图标注 {i+1}：{esc(t[2])}">{i+1}</button>' for i,t in enumerate(f['tips']))
    return f'''<figure class="real-figure" data-figure="{key}"><div class="figure-kicker">真实结果 · {esc(f['scope'])}</div>
    <div class="figure-stage"><img loading="lazy" src="case/{esc(f['path'])}" alt="{esc(f['title'])}"/>{markers}</div>
    <div class="figure-actions"><button type="button" data-zoom="{key}">放大读图 ↗</button><button type="button" data-annotations aria-pressed="true">隐藏图中标记</button><a href="case/{esc(f['path'])}" download>保存原图 ↓</a></div>
    <figcaption>{figure_reading(key)}</figcaption>
    <ol class="figure-notes" aria-label="图中数字定位提示">{tips}</ol></figure>'''

DIAGRAMS={
 'life': [('细胞中的 DNA','保存遗传信息'),('转录产生 RNA','不同基因有不同表达'),('建库与测序','得到序列片段'),('计算与解释','寻找表达变化')],
 'prepare':[('工具箱','Conda 环境'),('材料架','输入与参考'),('工作台','分析过程'),('实验记录本','参数、结果与日志')],
 'sample':[('第 2 天的叶片','同一发育阶段'),('7 个 ZT 时期','开灯后 0–20 小时'),('每组 3 个重复','21 个独立文库'),('每个文库读两端','42 个 FASTQ 文件')],
 'qc':[('原始 FASTQ','序列 + 质量值'),('FastQC','逐个测序端检查'),('MultiQC','汇总各样本'),('判断问题','结合实验与报告')],
 'filter':[('观察问题','接头 / 质量 / 长度'),('fastp 处理','按记录的规则执行'),('clean FASTQ','保存处理后的数据'),('重新质控','比较处理前后')],
 'quant':[('clean 片段','一次测序观察'),('参考转录本','可能的归属位置'),('Salmon 模型','分配有歧义的片段'),('quant.sf','估计丰度与计数')],
 'matrix':[('各样本 quant.sf','每份独立定量'),('转录本 → 基因','根据明确的 ID 映射'),('基因 × 样本','对齐列名与顺序'),('三类表达矩阵','按分析用途选择')],
 'pca':[('TMM 表达矩阵','使用同一数值口径'),('log2(TMM + 1)','压缩极端数值'),('相关性 / PCA','观察整体关系'),('回看实验记录','判断后续检查方向')],
 'de':[('counts + 分组','ZT4 相对 ZT0'),('低表达过滤','比较内 CPM 规则'),('DESeq2','大小因子与离散度'),('差异结果表','幅度、证据与方向')],
 'sets':[('每个比较的结果','采用一致候选阈值'),('候选基因集合','每个集合回答一个问题'),('交集 / 特有集合','共同与不同的候选'),('回到基因表','核对身份与方向')],
 'plots':[('同一份差异表','每个点 / 行有来源'),('火山图','幅度 × 统计证据'),('Top 基因选择','本例按 |log2FC| 排名'),('行标准化热图','观察样本间相对模式')],
 'ora':[('候选名单','如本例上调基因'),('有效背景','可检验且可注释'),('功能集合','GO 或 KEGG'),('比例比较','超几何检验 + BH')],
 'gsea':[('可检验、可排序基因','不按显著性截断'),('按 Wald stat 排队','正端 → 负端'),('沿队伍寻找命中','累积富集分数'),('NES 与校正 P 值','方向与统计证据')],
 'trend':[('7 时期的 TPM','每时期汇总重复'),('过滤与高变选择','本例选择 1,587 基因'),('标准化 + Mfuzz','本例划分 6 个模块'),('形状与功能线索','允许不同隶属程度')],
 'cycle':[('7 时期先过滤','组内中位数 TPM'),('6 个等间隔时期','ZT0 / 4 / 8 / 12 / 16 / 20'),('JTK 周期模板','保留 18 个重复观测'),('候选与诊断','BH.Q + 有效返回周期')],
 'nonmodel':[('代表蛋白','每基因一条查询'),('eggNOG / DIAMOND','从同源关系转移注释'),('自建 OrgDb / 映射','明确实际覆盖范围'),('ORA 与 GSEA','沿用同一差异结果')]
}

def diagram(name):
    steps=DIAGRAMS[name]
    blocks=''
    for i,(a,b) in enumerate(steps):
        x=15+i*210
        blocks+=f'<g transform="translate({x},22)"><rect width="190" height="112" rx="18" fill="{["#e2eee2","#e1eff4","#f8e9ce","#f2e1d7"][i]}" stroke="#42717b"/><circle cx="25" cy="27" r="13" fill="#315e65"/><text x="25" y="32" text-anchor="middle" fill="white" font-size="13">{i+1}</text><text x="95" y="65" text-anchor="middle" fill="#203e47" font-size="16" font-weight="600">{esc(a)}</text><text x="95" y="90" text-anchor="middle" fill="#49666e" font-size="12">{esc(b)}</text></g>'
        if i<3: blocks+=f'<path d="M{x+194} 78h12m-5-5 5 5-5 5" fill="none" stroke="#42717b" stroke-width="2"/>'
    return f'<figure class="concept process-visual"><div class="figure-kicker">原理示意 · 帮你连接概念</div><div class="concept-scroll"><svg viewBox="0 0 850 155" role="img" aria-label="{esc("；".join(a+"："+b for a,b in steps))}">{blocks}</svg></div><figcaption><strong>把步骤连起来看。</strong>{esc(CONCEPT_NOTES["diagrams"][name])}</figcaption></figure>'

def visual(name):
    if name=='life':
        label='DNA 信息经过转录形成 RNA，再经过建库测序得到片段；示意图不代表实际序列。'
        svg='''<ellipse cx="117" cy="134" rx="97" ry="105" fill="#dce8d4" stroke="#7c9f7b" stroke-width="2"/><circle cx="111" cy="124" r="60" fill="#f5f3d9" stroke="#8da78a"/><path d="M89 70C154 97 60 148 132 177M130 70C62 99 158 148 89 177" fill="none" stroke="#528993" stroke-width="5"/><path d="m96 78 28 0m-30 16 33 0m-27 17 21 0m-21 17 25 0m-29 17 28 0m-29 17 31 0" stroke="#b58460" stroke-width="3"/><text x="113" y="258" text-anchor="middle">细胞中的 DNA</text><path d="M227 121h54m-9-7 9 7-9 7" stroke="#5b8287" stroke-width="2" fill="none"/><text x="254" y="103" text-anchor="middle" font-size="14">转录</text><path d="M309 146q24-60 48-12t48-12t48 6" fill="none" stroke="#ca865e" stroke-width="7"/><text x="376" y="198" text-anchor="middle">RNA 转录本</text><path d="M469 121h54m-9-7 9 7-9 7" stroke="#5b8287" stroke-width="2" fill="none"/><text x="496" y="99" text-anchor="middle" font-size="14">建库 / 测序</text><g stroke="#75a5a0" stroke-width="9" stroke-linecap="round"><path d="M560 77h71m50 0h59M583 112h77m29 0h98M552 147h94m20 0h67M590 181h58m34 0h89"/></g><text x="670" y="230" text-anchor="middle">很多短片段 → 计算其来源</text>'''
    elif name=='read':
        label='一条教学示意 read 含待测序列和接头；低质量碱基与接头是不同概念。'
        svg='''<text x="25" y="40" font-size="17">一条 read，先辨认每一部分</text><rect x="28" y="74" width="492" height="56" rx="9" fill="#dbe9d4"/><rect x="520" y="74" width="281" height="56" rx="9" fill="#ead0b8"/><text x="49" y="109" font-family="monospace" font-size="24" letter-spacing="5">ACGT TCAA GCTT ACGT</text><text x="545" y="109" font-family="monospace" font-size="24" letter-spacing="5">AGAT CGGA AG</text><path d="M520 57v91" stroke="#b16a4f" stroke-width="2" stroke-dasharray="5 4"/><text x="244" y="164" text-anchor="middle">可能属于待测转录本的序列</text><text x="662" y="164" text-anchor="middle">读穿后出现的接头</text><g font-size="14" fill="#58757c"><text x="30" y="215">序列身份：这段信息来自哪里？</text><text x="30" y="245">碱基质量：这个字母判断有多确定？</text></g><text x="466" y="236" font-size="15" fill="#a26243">接头可以被测得很准确，仍需要处理。</text>'''
    elif name=='assignment':
        label='两条转录本共享一段序列；共享片段来源有歧义，特异片段提供归属信息。仅为原理示意。'
        svg='''<text x="25" y="40" font-size="17">同一片段，可能有不止一个来源</text><text x="20" y="99">转录本 A</text><text x="20" y="169">转录本 B</text><g stroke="#648b85" stroke-width="2"><path d="M136 94h510M136 164h510"/><rect x="154" y="76" width="150" height="36" rx="4" fill="#c1d9ae"/><rect x="368" y="76" width="190" height="36" rx="4" fill="#b1d4d7"/><rect x="154" y="146" width="150" height="36" rx="4" fill="#c1d9ae"/><rect x="368" y="146" width="115" height="36" rx="4" fill="#ebcd9c"/></g><path d="M191 220h87" stroke="#be7a55" stroke-width="12" stroke-linecap="round"/><path d="M222 211 213 185m30 26 43-94" stroke="#be7a55" stroke-width="2" stroke-dasharray="4 3" fill="none"/><path d="M425 219h87" stroke="#518b9d" stroke-width="12" stroke-linecap="round"/><path d="M507 207 521 117" stroke="#518b9d" stroke-width="2" stroke-dasharray="4 3"/><text x="234" y="260" text-anchor="middle" font-size="14">共享序列：归属有歧义</text><text x="471" y="260" text-anchor="middle" font-size="14">特异信息帮助分配</text><text x="644" y="114" font-size="16">一次观察</text><text x="644" y="145" font-size="16">不重复完整计数</text><text x="644" y="193" font-size="14" fill="#5a7479">Salmon 综合模型</text><text x="644" y="217" font-size="14" fill="#5a7479">估计各转录本丰度</text>'''
    elif name=='timeline':
        label='七个时期按真实小时定位，ZT1 仍参与初步表达过滤，但最终 JTK 只使用六个等间隔时期。'
        svg='<text x="23" y="37" font-size="17">把采样时间放回真正的小时刻度</text><path d="M65 100h710M65 200h710" stroke="#78999c" stroke-width="2"/>'
        for h in [0,1,4,8,12,16,20]:
            x=65+h*35.5
            svg+=f'<circle cx="{x}" cy="100" r="7" fill="{"#c8815b" if h==1 else "#538982"}"/><text x="{x}" y="{75 if h!=1 else 137}" text-anchor="middle" font-size="14">ZT{h}</text>'
            if h!=1:svg+=f'<circle cx="{x}" cy="200" r="7" fill="#538982"/>'
        svg+='<text x="65" y="165" font-size="13" fill="#5a7479">七时期先按表达过滤；ZT1 不属于等间隔子集。</text><text x="395" y="252" text-anchor="middle" font-size="15">JTK：每 4 小时一个时期 × 3 个生物学重复 = 18 列</text>'
    elif name=='branches':
        label='同一差异结果分别搭配已有注释或自建注释，通向 ORA 和 GSEA；自建注释由参考蛋白支持。'
        svg='''<rect x="22" y="93" width="190" height="79" rx="12" fill="#dbe8d3" stroke="#719279"/><text x="117" y="126" text-anchor="middle">同一差异结果</text><text x="117" y="151" text-anchor="middle" font-size="13">候选名单 / 完整排序</text><path d="M219 132h43V62h64M262 132v78h64" fill="none" stroke="#6d9599" stroke-width="2"/><rect x="334" y="27" width="225" height="74" rx="11" fill="#e4ecce" stroke="#8d9f76"/><text x="446" y="58" text-anchor="middle">已有物种注释</text><text x="446" y="83" text-anchor="middle" font-size="13">官方 OrgDb / KEGG</text><rect x="334" y="176" width="225" height="74" rx="11" fill="#ead7b7" stroke="#ba9166"/><text x="446" y="207" text-anchor="middle">自建功能注释</text><text x="446" y="233" text-anchor="middle" font-size="13">蛋白 → DIAMOND → OrgDb</text><path d="M565 63h65M565 211h65" stroke="#6d9599" stroke-width="2"/><text x="668" y="69">ORA / GSEA</text><text x="668" y="217">ORA / GSEA</text><text x="308" y="140" font-size="14" fill="#5a7479">改变功能映射，不重新制造表达差异。</text>'''
    else: raise KeyError(name)
    return f'<figure class="concept science-visual"><div class="figure-kicker">原理插图 · 教学示意</div><div class="concept-scroll"><svg viewBox="0 0 850 290" role="img" aria-label="{esc(label)}" fill="#254c52" font-family="sans-serif" font-size="18">{svg}</svg></div><figcaption><strong>这幅图怎样读。</strong>{esc(CONCEPT_NOTES["visuals"][name])}</figcaption></figure>'

def illustration(name):
    a=ILLUSTRATIONS[name]
    sources=''.join(f'<p><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a></p>' for label,url in a.get('sources',[]))
    return f'<figure class="concept teaching-visual" data-illustration="{name}"><div class="figure-kicker">原理插图 · 教学示意</div><div class="concept-scroll"><img src="assets/illustrations/{name}.svg" alt="{esc(a["title"])}" loading="lazy"></div><p class="art-scroll-hint">可左右滑动查看整张示意图，也可放大阅读。</p><div class="figure-actions"><button type="button" data-zoom="concept-{name}">放大原理插图 ↗</button><a href="assets/illustrations/{name}.svg" download>保存插图 ↓</a></div><figcaption><div class="figure-reading"><div class="figure-summary"><span class="reading-label">先看摘要</span><strong>{esc(a["title"])}</strong><p>{esc(a["summary"])}</p></div><div class="visual-description">{MD.render(a["description"])}{sources}</div></div></figcaption></figure>'

def lab(name):
    common='<span class="lab-label">动手想一想</span>'
    if name=='composition': return f'''<div class="lab" data-lab="composition">{common}<h3>它自己没变，为什么占比变了？</h3><p>简化示意：目标 RNA 始终是 50 份。只增加其他 RNA，观察目标的相对占比。这里省略了转录本长度，不是实际 TPM 计算器。</p><label>其他 RNA：<output id="other-value">50</output> 份<input type="range" id="other-rna" min="50" max="450" step="10" value="50"></label><div class="composition-bar"><span id="target-bar" style="width:50%">目标 RNA</span><span>其他 RNA</span></div><p class="lab-result">目标占比 <strong id="composition-output">50.0%</strong></p><p>总量从 100 变到 500 份时，目标仍是 50 份，占比会从 50% 降到 10%。所以相对表达降低，并不自动证明绝对 RNA 数量降低。</p></div>'''
    if name=='direction': return f'''<div class="lab" data-lab="direction">{common}<h3>交换比较方向</h3><p>教学示意：A 组为 20，B 组为 5。先理解比值，再理解对数。此处是简化数值，不是 DESeq2 模型拟合。</p><div class="direction-equation"><span id="direction-formula">log₂(20 / 5)</span><strong id="direction-value">+2</strong></div><button type="button" id="swap-direction">交换 A 与 B</button><p id="direction-meaning">A 相对 B 是 4 倍，log₂FC 为 +2。</p><p>换方向后幅度的绝对值不变、符号相反。真正的比较方向由比较表指定。</p></div>'''
    if name=='threshold': return f'''<div class="lab" data-lab="threshold">{common}<h3>用真实差异表调整候选筛选</h3><p>读取 ZT4_vs_ZT0 的 15,312 条已有结果。这里仅重新筛选名单，不重新拟合模型；原始火山图仍对应默认阈值。</p><div class="lab-controls"><label>校正 P 值上限<select id="fdr"><option value="0.01">0.01</option><option value="0.05" selected>0.05</option><option value="0.1">0.10</option></select></label><label>|log₂FC| 下限 <output id="fc-value">1.0</output><input id="fc-threshold" type="range" min="0.5" max="3" step="0.5" value="1"></label></div><div class="stat-strip"><span>上调 <strong id="up-count">1,087</strong></span><span>下调 <strong id="down-count">826</strong></span><span>其余 <strong id="ns-count">13,399</strong></span></div><button type="button" id="reset-threshold">恢复案例阈值</button><label class="gene-search">查一个基因（精确 ID）<input id="gene-query" value="AT4G31073" spellcheck="false"></label><p id="gene-answer" aria-live="polite">AT4G31073：log₂FC ≈ −7.47，padj ≈ 0.106；默认阈值下不属于显著候选。</p></div>'''
    if name=='ranking':
        dots=''.join(f'<span class="rank-gene {"hit" if i in [0,1,3,4,5,8] else ""}"></span>' for i in range(24))
        return f'''<div class="lab" data-lab="ranking">{common}<h3>把同一功能的成员放进队伍</h3><p>教学示意：24 个基因按变化方向排列，其中 6 个橙色成员属于同一功能集合。点击观察它们集中在一端或分散时的区别。</p><div class="rank-ends"><span>偏向上调端</span><span>偏向下调端</span></div><div class="rank-demo">{dots}</div><button type="button" id="shuffle-rank">改为分散分布</button><p id="rank-explanation">同一功能的成员聚在上调端，提示整体偏向。这只是直觉示意，真实 GSEA 还会考虑排序权重、集合大小和统计检验。</p></div>'''
    raise KeyError(name)

def table(data,cols):
    return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+esc(label)+'</th>' for _,label in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(r[key])+'</td>' for key,_ in cols)+'</tr>' for r in data)+'</tbody></table></div>'

def fact_block(name,facts):
    if name=='matrix':
        data=[]
        for r in facts['matrices']['counts']:
            data.append({k: (v if k=='gene_id' else f'{float(v):.2f}') for k,v in r.items()})
        return '<div class="data-excerpt"><p class="figure-kicker">真实数据摘录 · estimated counts · 显示保留两位小数</p>'+table(data,[(k,k) for k in data[0]])+'<p><a href="case/teaching/matrix_counts_excerpt.tsv" download>下载原精度 counts 摘录</a> · <a href="case/teaching/matrix_TPM_excerpt.tsv" download>TPM 摘录</a> · <a href="case/teaching/matrix_TMM_excerpt.tsv" download>TMM 摘录</a></p></div>'
    if name=='qc':
        q=facts['qc'];return '<div class="stat-strip"><span>reads 保留率<strong>'+f'{float(q["retention"])*100:.2f}%</strong></span><span>碱基保留率<strong>{float(q["base_retention"])*100:.2f}%</strong></span><span>Q30 前 → 后<strong>{float(q["q30_before"])*100:.2f} → {float(q["q30_after"])*100:.2f}%</strong></span></div>'
    if name=='gene':
        data=[]
        for gid in ['AT1G13930','AT1G01060','AT4G31073']:
            r=next(x for x in facts['genes'] if x['gene_id']==gid)
            data.append({'gene_id':gid,'fc':f'{float(r["log2FoldChange"]):.3f}','padj':f'{float(r["padj"]):.3g}','direction':{'up':'上调','down':'下调','ns':'未达到候选阈值'}[r['direction']]})
        return table(data,[('gene_id','基因'),('fc','log₂FC'),('padj','padj（显示值）'),('direction','原表分类')])+'<p class="small">表中的 0 是极小概率在数值计算或导出中的表示，不表示已经获得绝对确定的证据。</p>'
    raise KeyError(name)

def render_lesson(s,facts):
    content=(ROOT/'content'/f'{s["id"]}.md').read_text()
    content=re.sub(r'\{\{illustration:(\w+)\}\}',lambda m:illustration(m[1]),content)
    content=re.sub(r'\{\{figure:(\w+)\}\}',lambda m:figure(m[1]),content)
    content=re.sub(r'\{\{diagram:(\w+)\}\}',lambda m:diagram(m[1]),content)
    content=re.sub(r'\{\{visual:(\w+)\}\}',lambda m:visual(m[1]),content)
    content=re.sub(r'\{\{lab:(\w+)\}\}',lambda m:lab(m[1]),content)
    content=re.sub(r'\{\{facts:(\w+)\}\}',lambda m:fact_block(m[1],facts),content)
    # Keep the author's original words; one prose pass supplies all term links.
    content=re.sub(r'\[\[([^\]]+)\]\]',lambda m:esc(m[1]),content)
    rendered=MD.render(content)
    idx=[0]
    def heading(m):
        idx[0]+=1;return f'<h2 id="{s["id"]}-part-{idx[0]}">{m[1]}</h2>'
    rendered=re.sub(r'<h2>(.*?)</h2>',heading,rendered)
    opts=''.join(f'<label><input type="radio" name="quiz-{s["id"]}" value="{i}"><span>{esc(t)}</span></label>' for i,t in enumerate(s['quiz']['options']))
    quiz=f'<section class="quiz" data-answer="{s["quiz"]["answer"]}"><span class="lab-label">本站自测 · 可以随时查看解析</span><h3>{esc(s["quiz"]["question"])}</h3><fieldset><legend class="sr-only">请选择一个答案</legend>{opts}</fieldset><button type="button" data-check-answer>检查答案</button><p class="quiz-feedback" aria-live="polite"></p><details><summary>查看答案与解释</summary><p>{esc(s["quiz"]["explanation"])}</p></details></section>'
    marked, occurrences = ProseTerms(TERMS, READING_PAGE, s['id']).annotate(rendered+quiz)
    TERM_OCCURRENCES.extend(occurrences)
    return marked

def build_library():
    directory=ROOT/'library'; directory.mkdir(exist_ok=True)
    docs=sorted((ROOT/'case/0script').glob('*.md'))
    code_files=sorted(p for group in ['scripts','tools'] for p in (ROOT/'case/0script'/group).glob('*') if p.is_file() and p.suffix in ['.R','.sh','.py'])
    mapping={p.resolve():directory/(p.stem+'.html') for p in docs}
    mapping.update({p.resolve():directory/'源码'/p.parent.name/(p.name+'.html') for p in code_files})
    # A link to the old conceptual atlas opens this package's current map.
    mapping[(ROOT/'case/0script/转录组原理图谱.html').resolve()]=ROOT/HOME_PAGE
    def relative(target, dest):
        return quote(os.path.relpath(target, dest.parent),safe='/')
    def document(src, dest, body, note):
        dest.parent.mkdir(parents=True, exist_ok=True)
        nav=f'<a href="{relative(ROOT/HOME_PAGE,dest)}">← 返回海岛地图</a><a href="{relative(directory/LIBRARY_PAGE,dest)}">脚本与资料目录</a><a href="{relative(src,dest)}" download>下载原始文件 ↓</a>'
        dest.write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(src.stem)} · 随包资料</title><link rel="stylesheet" href="{relative(ROOT/"assets/style.css",dest)}"></head><body class="document-page"><header class="document-header">{nav}</header><main class="document-content"><p class="document-note">{note}</p>{body}</main></body></html>')
    catalog=[]
    for src in docs:
        dest=mapping[src.resolve()]
        body=MD.render(src.read_text())
        def rewrite(match):
            tag,attrs,label=match.group(1),match.group(2),match.group(3)
            hit=re.search(r'href="([^"]*)"',attrs)
            if not hit: return match.group(0)
            url=html.unescape(hit.group(1)); parts=urlsplit(url)
            if parts.scheme in ['http','https','mailto']:
                return match.group(0).replace('<a ', '<a target="_blank" rel="noopener noreferrer" ')
            if not parts.path: return match.group(0)
            target=(src.parent/unquote(parts.path)).resolve()
            if target in mapping: destination=mapping[target]
            elif target.is_file() and target.is_relative_to(ROOT): destination=target
            else: return f'<span class="unbundled">{label}<small>完整项目文件未收录：{esc(unquote(parts.path))}</small></span>'
            url=relative(destination,dest)
            if parts.fragment and target not in mapping: url+='#'+parts.fragment
            return match.group(0).replace(hit.group(1),esc(url))
        body=re.sub(r'<(a)\b([^>]*)>(.*?)</a>',rewrite,body,flags=re.S)
        def rewrite_img(match):
            attrs=match.group(1); hit=re.search(r'src="([^"]*)"',attrs); alt=re.search(r'alt="([^"]*)"',attrs)
            label=html.unescape(alt.group(1)) if alt else '原文图示'
            if not hit:return ''
            url=html.unescape(hit.group(1)); target=(src.parent/unquote(urlsplit(url).path)).resolve()
            if target.is_file() and target.is_relative_to(ROOT):return f'<img loading="lazy" src="{relative(target,dest)}" alt="{esc(label)}">'
            return f'<span class="unbundled">{esc(label)}<small>教学包未精选收录这张完整项目图形：{esc(unquote(url))}</small></span>'
        body=re.sub(r'<img\b([^>]*)/?>',rewrite_img,body)
        document(src,dest,body,'V9 最新资料的包内副本 · 原始文件按字节复制。网页适配本地链接；没有精选收录的结果显示说明。代码用于延伸阅读，实际分析需要完整输入与环境。')
        catalog.append({'name':src.name,'title':src.stem,'url':str(dest.relative_to(ROOT)),'raw':str(src.relative_to(ROOT))})
    for src in code_files:
        dest=mapping[src.resolve()]
        body=f'<h1>{esc(src.name)}</h1><p>可直接阅读以下完整源码，或下载原始文件。页面不会执行这些命令。</p><pre class="source-code"><code>{esc(src.read_text())}</code></pre>'
        document(src,dest,body,'最新实现源码 · 保留 V9 的说明与注释；此页只是阅读视图。原始源码仍在包内 case/0script 下。')
    links=''.join(f'<li><a href="{quote(Path(d["url"]).name)}">{esc(d["title"])}</a><a class="small" href="../{quote(d["raw"],safe="/")}" download>原始 MD ↓</a></li>' for d in catalog)
    code_links=''.join(f'<li><a href="{relative(mapping[src.resolve()],directory/LIBRARY_PAGE)}">{esc(src.parent.name+"/"+src.name)}</a><a class="small" href="{relative(src,directory/LIBRARY_PAGE)}" download>源码 ↓</a></li>' for src in code_files)
    snapshot=json.loads((ROOT/'素材来源.json').read_text()).get('documents_snapshot_utc','')[:10]
    (directory/LIBRARY_PAGE).write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>脚本与资料 · 转录组海岛探险</title><link rel="stylesheet" href="../assets/style.css"></head><body class="document-page"><header class="document-header"><a href="../{HOME_PAGE}">← 返回海岛地图</a><a href="../{READING_PAGE}">完整教案</a><a href="#source-library">实现源码</a></header><main class="document-content"><p class="eyebrow">随包资料馆 · 更新于 {snapshot}</p><h1>想再深入一点，<br>原文就在这里。</h1><p>20 个主章节、04.5 准备检查、5 份附录和目录说明，共 {len(docs)} 份 Markdown；另附 {len(code_files)} 个实现与工具文件。每个文件都是随包副本，离线可读。</p><p class="document-note">从章节读原理、参数与入口，再点击其中的实现链接看函数注释。案例图表沿用已经完成的精选结果；新脚本中的参数目录与重绘入口按最新原文说明使用。</p><h2>章节与附录</h2><ul class="library-list">{links}</ul><h2 id="source-library">实现脚本与共用工具</h2><ul class="library-list">{code_links}</ul></main></body></html>')
    obsolete=directory/'index.html'
    if obsolete.exists():obsolete.unlink()
    return catalog

def main():
    (ROOT/'assets').mkdir(exist_ok=True)
    from draw_map import make_art
    make_art()
    from draw_teaching import make_teaching_art
    make_teaching_art()
    facts=prepare_data();catalog=build_library()
    lessons=[]
    for s in STATIONS:
        entry=dict(s);entry['html']=render_lesson(s,facts)
        entry['documents']=[d for d in catalog if any(d['name'].startswith(f'{n:02d} ') for n in s['chapters']) or (s['id']=='prepare' and d['name'].startswith('04.5 '))]
        lessons.append(entry)
    (ROOT/'assets/lessons.js').write_text('window.LESSONS='+json.dumps(lessons,ensure_ascii=False,separators=(',',':'))+';\nwindow.FIGURES='+json.dumps(FIGURES,ensure_ascii=False,separators=(',',':'))+';\n')
    term_data = dict(GLOSSARY)
    term_data['entries'] = [dict(e, html=render_entry(e, TERM_MAP, READING_PAGE)) for e in TERMS]
    (ROOT/'assets/glossary-data.js').write_text('window.GLOSSARY='+json.dumps(term_data,ensure_ascii=False,separators=(',',':'))+';\n')
    if (ROOT/'qa').is_dir():
        dump(ROOT/'qa/glossary_coverage.json', coverage_report(TERMS, TERM_OCCURRENCES))
    image_dialog=(ROOT/'tools/image-dialog.html').read_text()
    glossary_dialog=(ROOT/'tools/glossary-dialog.html').read_text()
    text=''.join(f'<section class="print-lesson" id="{s["id"]}"><p class="eyebrow">{esc(s["badge"])} · {esc(s["subtitle"])}</p><h1>{esc(s["title"])}</h1>{s["html"]}</section>' for s in lessons).replace('<details>','<details open>')
    text=text.replace(f'href="{READING_PAGE}#glossary-', 'href="#glossary-')
    term_nav=''.join(f'<a href="#glossary-group-{i}">{esc(category)}</a>' for i,category in enumerate(GLOSSARY['categories'],1))
    term_groups=''.join(f'<section class="glossary-group" id="glossary-group-{i}"><h2>{esc(category)}</h2>'+''.join(render_entry(e,TERM_MAP,READING_PAGE,appendix=True) for e in TERMS if e['category']==category)+'</section>' for i,category in enumerate(GLOSSARY['categories'],1))
    text+=f'<section class="glossary-appendix" id="glossary"><h1>随身术语手册</h1><p>{len(TERMS)} 个概念，中英对照。每项都完整展开：先理解含义，再看例子、本课用途和容易混淆的地方。正文中带虚线的词可点击查看；关闭解释后继续原处阅读。禁用脚本时，链接直接跳到这里，浏览器返回可回到原位置。</p><nav class="glossary-directory" aria-label="术语主题目录">{term_nav}</nav>{term_groups}</section>'
    nav=''.join(f'<a href="#{s["id"]}">{esc(s["title"])}</a>' for s in lessons)
    nav+='<a href="#glossary">术语手册</a>'
    (ROOT/READING_PAGE).write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>完整教案 · 转录组海岛探险</title><link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/glossary.css"></head><body class="document-page static-reading"><header class="document-header"><a href="{HOME_PAGE}">← 返回海岛地图</a><a href="library/{LIBRARY_PAGE}">脚本与资料</a><button onclick="window.print()">打印完整教案</button><button class="glossary-open" id="reading-glossary" type="button">查询术语</button></header><main class="document-content"><p class="eyebrow">转录组海岛探险 · 全文阅读</p><h1>从一片叶，读懂表达的变化。</h1><p>本页包含所有课程正文与自测解析，适合连续阅读、浏览器打印。交互实验在地图课程窗口中使用；本页保留初始状态和静态解释。</p><nav class="reading-directory">{nav}</nav>{text}</main>{image_dialog}{glossary_dialog}<script src="assets/glossary-data.js"></script><script src="assets/glossary.js"></script><script src="assets/figures.js"></script></body></html>''')
    template=(ROOT/'tools/index.template.html').read_text()
    nodes='';cards=''
    for s in STATIONS:
        icon=f'<svg viewBox="0 0 125 125" aria-hidden="true"><use href="#building-{s["icon"]}"/></svg>'
        nodes+=f'<a class="station-node" href="{READING_PAGE}#{s["id"]}" data-station="{s["id"]}" style="left:{s["x"]/16}%;top:{s["y"]/10.4}%">{icon}<span class="station-caption"><span class="station-badge">{s["badge"]}</span><strong>{s["title"]}</strong><small>{s["subtitle"]}</small></span></a>'
        cards+=f'<a class="station-card" href="{READING_PAGE}#{s["id"]}" data-station="{s["id"]}">{icon}<div><span class="station-badge">{s["badge"]} · {s["zone"]}</span><strong>{s["title"]}</strong><span>{s["subtitle"]}</span></div></a>'
    template=template.replace('<!-- GLOSSARY DIALOG -->',glossary_dialog).replace('<!-- IMAGE DIALOG -->',image_dialog).replace('<!-- SYMBOLS -->',(ROOT/'assets/symbols.svg').read_text()).replace('<!-- STATION NODES -->',nodes).replace('<!-- STATION LIST -->',cards)
    template=template.replace('index.html',HOME_PAGE).replace('reading.html',READING_PAGE).replace('library/'+HOME_PAGE,'library/'+LIBRARY_PAGE)
    (ROOT/HOME_PAGE).write_text(template)
    for obsolete in ['index.html','教案.html','reading.html']:
        path=ROOT/obsolete
        if path.exists():path.unlink()
    print(json.dumps({'lessons':len(lessons),'figures':len(FIGURES),'documents':len(catalog),'source_records':len(json.loads((ROOT/'素材来源.json').read_text())['files']),'de_summary':facts['de_summary']},ensure_ascii=False))

if __name__=='__main__':main()
