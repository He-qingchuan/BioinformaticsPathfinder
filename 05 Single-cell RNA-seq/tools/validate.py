"""功能：核对素材摘要、内容覆盖、本地链接；不修改课程文件。
目的：在离线分享或重建后确认独立性；浏览器视觉验收另行执行。
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,re,csv
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[];self.ids=set()
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if t in ('a','img','script','link','use'):
            self.urls.extend((t,d[k]) for k in ('src','href') if k in d)
def validate():
    errors=[];sources=json.loads((ROOT/'素材来源.json').read_text())['files']
    with (ROOT/'素材来源.tsv').open(newline='') as stream:table=list(csv.DictReader(stream,delimiter='\t'))
    assert [{**r,'bytes':int(r['bytes'])} for r in table]==sources,'JSON/TSV 素材来源不一致'
    for r in sources:
        p=(ROOT/r['path']).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:errors.append('素材改变 '+r['path'])
    parsed={};links=0
    for p in ROOT.rglob('*.html'):
        if p.relative_to(ROOT).parts[0]=='tools':continue  # 模板按成品位置渲染，不是独立入口。
        v=Links();v.feed(p.read_text());parsed[p.resolve()]=v
    for p,v in parsed.items():
        for tag,url in v.urls:
            u=urlsplit(url)
            if u.scheme or url.startswith('//'):
                if tag in ('img','script','link'):errors.append('外部运行资源 '+url)
                continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if not target.is_relative_to(ROOT) or not target.is_file():errors.append(str(p.relative_to(ROOT))+' -> '+url);continue
            if u.fragment and target in parsed and u.fragment not in parsed[target].ids:errors.append('锚点缺失 '+url)
            links+=1
    read=lambda x:json.loads((ROOT/'content'/x).read_text())
    stations=read('stations.json');figures=read('figures.json');art=read('illustrations.json');terms=read('glossary.json')['entries']
    assert len(stations)==16 and len(figures)==34 and len(art)==16
    for s in stations:
        text=(ROOT/'content'/f'{s["id"]}.md').read_text()
        assert '{{flow}}' in text and '{{illustration:' in text and text.count('## ')>=4
    for key,f in figures.items():
        assert len(f['sections'])>=6 and all(len(v)>=20 for _,v in f['sections'])
        assert sum(len(v) for _,v in f['sections'])>300
    for t in terms:assert all(t.get(f) for f in ('zh','en','summary','example','in_course','pitfall','category'))
    if errors:raise AssertionError('\n'.join(errors[:40]))
    print(json.dumps(dict(materials=len(sources),local_links=links,html=len(parsed),stations=len(stations),figures=len(figures),illustrations=len(art),terms=len(terms),status='passed'),ensure_ascii=False))
if __name__=='__main__':validate()
