"""Check a Chromium print proof using raw text order, plus record visual review pages."""
from pathlib import Path
import argparse, datetime, html, json, re, subprocess, unicodedata
from markdown_it import MarkdownIt
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('pdf',type=Path);args=p.parse_args()
md=MarkdownIt()
def norm(text):
    # PDF text contains real < and > comparisons; they are not HTML tags.
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',html.unescape(text)))
def plain_markdown(body):
    class Plain(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Plain();parser.feed(md.render(body));return ''.join(parser.parts)
raw=subprocess.check_output(['pdftotext','-raw',str(args.pdf),'-'],text=True)
whole=norm(raw);pages=raw.split('\f');errors=[];counts={};locations={}
def require(body,label,kind):
    if norm(plain_markdown(body)) not in whole:errors.append(label)
    else:counts[kind]=counts.get(kind,0)+1
for key,g in json.loads((ROOT/'content/figure_guides.json').read_text()).items():
    require(g['summary'],key+' summary','figure_summaries')
    locations[key]=[i+1 for i,page in enumerate(pages) if norm(g['summary']) in norm(page)]
    for title,body in g['sections']:require(body,key+' '+title,'full_guide_sections')
for key,g in json.loads((ROOT/'content/illustrations.json').read_text()).items():
    require(g['summary'],key+' summary','illustration_summaries')
    for i,body in enumerate(g['description'].split('\n\n')):require(body,key+f' explanation {i+1}','illustration_explanations')
for kind,group in json.loads((ROOT/'content/concept_notes.json').read_text()).items():
    for key,body in group.items():require(body,kind+' '+key,'existing_concept_notes')
for station in json.loads((ROOT/'content/stations.json').read_text()):
    require(station['quiz']['explanation'],station['id']+' quiz answer','quiz_explanations')
for entry in json.loads((ROOT/'content/glossary.json').read_text())['entries']:
    require(entry['zh'],entry['id']+' Chinese name','glossary_chinese_names')
    require(entry['en'],entry['id']+' English name','glossary_english_names')
    for field in ['summary','example','in_course','pitfall']:
        require(entry[field],entry['id']+' '+field,'glossary_explanations')
result={'pass':not errors,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'paper':'A4','pages':len(pages)-1,**counts,'errors':errors,'figure_summary_pages':locations,
        'method':'pdftotext -raw, NFKC and whitespace normalization. Full paragraph matches; visual layout reviewed separately.'}
(ROOT/'qa/print_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='figure_summary_pages'},ensure_ascii=False))
raise SystemExit(1 if errors else 0)
