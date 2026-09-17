"""Validate content coverage, links, glossary fallbacks and isolated static rebuild."""
import hashlib,json,re,shutil,subprocess,sys,tempfile,zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
root=Path(__file__).resolve().parents[1]
excluded={'artifacts','dist','__pycache__','node_modules','.Rproj.user','.cache'}
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.append(d['id'])
  for a in ['href','src']:
   if a in d:self.links.append((tag,a,d[a]))
  if tag=='img':self.images.append(d)
def manifest(folder):return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(folder).parts)}
course=json.loads((root/'content/course.json').read_text());terms=json.loads((root/'content/glossary.json').read_text());ids=[l['id'] for l in course['lessons']]
assert len(ids)==36 and len(set(ids))==36
assert len(set(z['id'] for z in course['zones']))==8
termmap={t['id']:t for t in terms};assert len(termmap)==len(terms)
seen_terms=set()
for i,l in enumerate(course['lessons']):
 body=(root/'content/lessons'/f'{l["id"]}.md').read_text()
 assert l['prerequisites']==([] if i==0 else [ids[i-1]])
 assert len(body)>800 and '{{exercise:' in body and '{{answer:' in body,l['id']
 for term in re.findall(r'\[\[([a-z]+)\|',body):assert term in termmap;seen_terms.add(term)
 assert l['quiz']['answer'] in range(len(l['quiz']['options']))
 if i: assert (root/'practice/r-lab/lessons'/f'{l["id"]}.R').is_file() and (root/'practice/expected'/f'{l["id"]}.txt').is_file()
assert seen_terms==set(termmap)
for t in terms:
 assert all(t[k] for k in ['zh','en','summary','example','pitfall','in_course','lessons'])
 assert all(k in ids for k in t['lessons']) and all(k in termmap for k in t['related'])
pages={}
for f in root.rglob('*.html'):
 if excluded.intersection(f.relative_to(root).parts):continue
 source=f.read_text();p=Page();p.feed(source)
 assert len(p.ids)==len(set(p.ids)),f'duplicate ids: {f}'
 assert not re.search(r'\{\{|@@BLOCK|老师版|学生版|全屏讲课|linux-lab|Shell、标准输出',source),f
 assert all(i.get('alt') for i in p.images if i.get('src')),f
 pages[f.resolve()]=p
assert len(pages)==39,len(pages)
count=0
for f,p in pages.items():
 for tag,attr,link in p.links:
  u=urlsplit(link)
  if u.scheme in ['http','https']:
   assert tag=='a' and attr=='href',(f,link);continue
  if u.scheme in ['data','mailto']:continue
  assert not u.scheme,(f,link)
  target=(f.parent/unquote(u.path)).resolve() if u.path else f
  assert target.is_relative_to(root.resolve()) and target.is_file(),(f,link)
  if u.fragment and target in pages:assert unquote(u.fragment) in pages[target].ids,(f,link)
  count+=1
with zipfile.ZipFile(root/'practice/r-lab.zip') as z:
 names=z.namelist();assert 'r-lab/r-lab.Rproj' in names and 'r-lab/data/shade_trial.csv' in names
 assert not any('/.cache/' in n or n.endswith(('.RData','.Rhistory')) for n in names)
with tempfile.TemporaryDirectory(prefix='r-relocation-') as tmp:
 moved=Path(tmp)/'独立 R 教材';shutil.copytree(root,moved,ignore=shutil.ignore_patterns(*excluded))
 before=manifest(moved)
 guard='''import pathlib,runpy,sys
root=pathlib.Path(sys.argv[1]).resolve();forbidden=pathlib.Path(sys.argv[2]).resolve()
def audit(event,args):
 if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen'):raise RuntimeError('Network/process execution forbidden in static build')
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=pathlib.Path(args[0]).resolve()
  if p.is_relative_to(forbidden):raise RuntimeError('Original repo access forbidden')
sys.path.insert(0,str(root/'tools'));sys.addaudithook(audit)
runpy.run_path(str(root/'tools/build.py'),run_name='__main__')
'''
 subprocess.run([sys.executable,'-c',guard,str(moved),str(root.parent)],cwd=tmp,capture_output=True,text=True,check=True)
 assert before==manifest(moved),'Build is not deterministic after relocation'
report=dict(status='passed',lessons=len(ids),terms=len(terms),pages=len(pages),local_references=count,isolated_rebuild=True,external_runtime_resources=0)
(root/'qa/artifacts').mkdir(exist_ok=True)
(root/'qa/artifacts/static.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
