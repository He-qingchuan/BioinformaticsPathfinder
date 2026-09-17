"""Independent checks of bundled data, copied bytes, coverage and local links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import csv,json,hashlib,math,re

ROOT=Path(__file__).resolve().parents[1]
errors=[]
def check(condition,message):
    if not condition: errors.append(message)
def read(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
manifest=json.loads((ROOT/'素材来源.json').read_text())['files']
for r in manifest:
    p=ROOT/r['file']
    check(p.is_file(),'missing '+r['file'])
    if p.is_file():
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        check(digest==r['sha256'],'delivery hash mismatch '+r['file'])
        if r['kind'] in ['copy','vendor']:check(digest==r['source_sha256'],'source copy mismatch '+r['file'])
stations=json.loads((ROOT/'content/stations.json').read_text())
figures=json.loads((ROOT/'content/figures.json').read_text())
check(len(stations)==16,'station count')
check(sorted(n for s in stations for n in s['chapters'])==list(range(1,21)),'chapter coverage')
check(len(figures)==23,'figure count')
guides=json.loads((ROOT/'content/figure_guides.json').read_text())
illustrations=json.loads((ROOT/'content/illustrations.json').read_text())
check(set(guides)==set(figures),'guides and figures must match')
check(len(illustrations)==14,'new illustration count')
for key,guide in guides.items():
    check(len(guide['sections'])>=6,'insufficient figure explanation '+key)
    check(len(''.join(body for title,body in guide['sections']))>=450,'figure guide too brief '+key)
for key,entry in illustrations.items():
    check((ROOT/'assets/illustrations'/f'{key}.svg').is_file(),'missing concept art '+key)
    check('{{illustration:'+key+'}}' in (ROOT/'content'/f'{entry['module']}.md').read_text(),'unplaced concept '+key)
check(len(list((ROOT/'case/0script').glob('*.md')))==27,'markdown snapshot count')
check(len(list((ROOT/'case/0script/scripts').glob('*')))==53,'implementation snapshot count')
check(len(list((ROOT/'case/0script/tools').glob('*')))==10,'tool snapshot count')
check((ROOT/'case/0script/04.5 分析前准备检查.md').is_file(),'missing preflight chapter')
for p in ROOT.rglob('*'):
    check(not p.is_symlink(),'symlink '+str(p.relative_to(ROOT)))

for s in stations:
    body=(ROOT/'content'/f'{s["id"]}.md').read_text()
    check(len(body)>850,'lesson too short '+s['id'])
    check(body.count('\n## ')>=4,'insufficient content sections '+s['id'])
    check(0<=s['quiz']['answer']<len(s['quiz']['options']),'invalid quiz '+s['id'])
de=read(ROOT/'case/teaching/ZT4_vs_ZT0.de_result.tsv')
count={'up':0,'down':0,'ns':0}
for r in de:
    check(r['contrast_id']=='ZT4_vs_ZT0','contrast contamination')
    try: p,fc=float(r['padj']),float(r['log2FoldChange'])
    except ValueError:p,fc=math.nan,math.nan
    direction=('up' if fc>0 else 'down') if math.isfinite(p) and math.isfinite(fc) and p<=.05 and abs(fc)>=1 else 'ns'
    count[direction]+=1
    check(direction==r['direction'],'classification differs '+r['gene_id'])
check(count=={'up':1087,'down':826,'ns':13399},'differential count regression')
g=next(r for r in de if r['gene_id']=='AT4G31073')
check(g['direction']=='ns' and float(g['padj'])>.05 and float(g['log2FoldChange'])<-7,'teaching gene example invalid')
qc=next(r for r in read(ROOT/'case/2data/cleandata/qc_summary.tsv') if r['sample_id']=='ZT4_rep_1')
mapping=next(r for r in read(ROOT/'case/3Salmon/quanti/mapping_summary.tsv') if r['sample_id']=='ZT4_rep_1')
check(int(qc['reads_after'])==2*int(mapping['num_processed']),'paired-end unit mismatch')
check(abs(float(qc['retention'])-int(qc['reads_after'])/int(qc['reads_before']))<1e-12,'retention mismatch')
go=next(r for r in read(ROOT/'case/9Enrichment_Analysis/ORA/ZT4_vs_ZT0/up/GO_BP_raw.tsv') if r['ID']=='GO:0019761')
check(go['GeneRatio']=='26/809' and go['BgRatio']=='41/11616','ORA numerator/denominator mismatch')
check(abs(float(go['FoldEnrichment'])-(26/809)/(41/11616))<1e-10,'ORA fold enrichment mismatch')
check(len(list((ROOT/'case/0script').glob('[0-9][0-9] *.md')))==20,'missing copied scripts')
check(len(list((ROOT/'case/0script').glob('附*.md')))==5,'missing appendices')

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set();self.duplicates=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:self.duplicates.append(attrs['id'])
            self.ids.add(attrs['id'])
        for key in ['href','src']:
            if key in attrs:self.links.append((tag,attrs[key]))
pages={}
for p in ROOT.rglob('*.html'):
    if p.is_relative_to(ROOT/'tools'):continue
    parser=Links();parser.feed(p.read_text());pages[p.resolve()]=parser
    if '/case/' not in str(p):check(not parser.duplicates,f'duplicate ids {p.relative_to(ROOT)} {parser.duplicates}')
references=0;online_references=0
for p,parser in pages.items():
    for tag,url in parser.links:
        parts=urlsplit(url)
        if parts.scheme in ['http','https']:
            online_references+=1
            check(tag not in ['img','script','link','iframe'],'remote runtime dependency '+url)
            continue
        if parts.scheme in ['data','mailto','javascript'] or not url:continue
        target=(p.parent/unquote(parts.path)).resolve() if parts.path else p
        references+=1
        check(target.is_relative_to(ROOT),'path leaves bundle '+str(p.relative_to(ROOT))+' '+url)
        check(target.exists(),'broken local link '+str(p.relative_to(ROOT))+' '+url)
        if parts.fragment and target in pages and not str(parts.fragment).startswith('station/'):
            # Legacy FastQC pages use named anchors in addition to IDs.
            if '/case/' not in str(target):check(unquote(parts.fragment) in pages[target].ids,'missing anchor '+str(p.relative_to(ROOT))+' '+url)
for js in ['assets/app.js','assets/figures.js','assets/lessons.js','assets/case.js']:
    check((ROOT/js).is_file(),'missing runtime '+js)
reading=(ROOT/'02_完整教案_阅读与打印.html').read_text()
check('{{' not in reading,'unexpanded lesson token')
check(len(re.findall('class="real-figure"',reading))==23,'rendered real figure count')
check(len(re.findall('class="quiz"',reading))==16,'rendered quiz count')
check(reading.count('class="figure-reading"')==37,'23 figure and 14 illustration explanations')
check(reading.count('class="guide-section"')==sum(len(g['sections']) for g in guides.values()),'missing full guide section')
check(reading.count('data-illustration=')==14,'rendered illustration count')
check(reading.count('class="concept process-visual"')==16,'process diagram count')
check(reading.count('class="concept science-visual"')==5,'existing illustration count')
check('assets/figures.js' in (ROOT/'01_海岛探险教案.html').read_text(),'map image reader missing')
for legacy in ['index.html','reading.html','教案.html','library/index.html']:
    check(not (ROOT/legacy).exists(),'ambiguous old entry '+legacy)

result={'pass':not errors,'stations':len(stations),'chapters':20,'figures':len(figures),'new_illustrations':len(illustrations),'guide_sections':sum(len(g['sections']) for g in guides.values()),'markdown':27,'implementation_scripts':53,'tools':10,'source_records':len(manifest),'html_pages':len(pages),'local_references_checked':references,'optional_online_references':online_references,'de_counts':count,'errors':errors}
(ROOT/'qa/static_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(1 if errors else 0)
