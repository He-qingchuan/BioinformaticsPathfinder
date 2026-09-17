"""Check source coverage, local links/anchors, independence and deterministic build."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'__pycache__','artifacts','dist','node_modules'}


class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        for key in ('href','src'):
            if key in a:self.links.append((tag,key,a[key]))
        if tag=='img':self.images.append(a)


def manifest(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(root).parts)}


def main():
    course=json.loads((ROOT/'content/course.json').read_text());terms=json.loads((ROOT/'content/glossary.json').read_text())
    assert len(course['lessons'])==18 and len({t['id'] for t in terms})==len(terms)
    for t in terms:
        assert all(t[k] for k in ['zh','en','summary','example','pitfall','in_course']),t['id']
    pages={}
    for path in ROOT.rglob('*.html'):
        if EXCLUDED.intersection(path.relative_to(ROOT).parts):continue
        p=Page();content=path.read_text();p.feed(content)
        assert len(p.ids)==len(set(p.ids)),f'duplicate ids: {path}'
        assert '{{' not in content and '@@BLOCK' not in content,path
        assert not re.search(r'老师|学生版|全屏讲课|Biotrainee|转录组海岛',content),path
        assert all(i.get('alt') for i in p.images if i.get('src')),path
        pages[path.resolve()]=p
    references=0
    for path,p in pages.items():
        for tag,attr,url in p.links:
            parts=urlsplit(url)
            if parts.scheme in ['http','https']:
                assert tag=='a' and attr=='href',(path,url)
                continue
            if parts.scheme in ['data','mailto']:continue
            assert not parts.scheme,(path,url)
            target=(path.parent/unquote(parts.path)).resolve() if parts.path else path
            assert target.is_relative_to(ROOT.resolve()) and target.is_file(),(path,url)
            if parts.fragment and target in pages:assert unquote(parts.fragment) in pages[target].ids,(path,url)
            references+=1
    for i,l in enumerate(course['lessons']):
        assert l['prerequisites']==([] if i==0 else [f'{i:02d}'])
        body=(ROOT/'content/lessons'/f'{l["id"]}.md').read_text()
        assert '{{exercise:' in body and '{{answer:' in body and len(body)>650
    # Copy just this course, then rebuild while denying access to the original project.
    with tempfile.TemporaryDirectory(prefix='linux-independent-') as temp:
        moved=Path(temp)/'独立 教材';shutil.copytree(ROOT,moved,ignore=shutil.ignore_patterns(*EXCLUDED))
        before=manifest(moved)
        guard='''import pathlib,runpy,sys
root=pathlib.Path(sys.argv[1]).resolve(); forbidden=pathlib.Path(sys.argv[2]).resolve()
def audit(event,args):
 if event in ('socket.connect','socket.getaddrinfo'): raise RuntimeError('Network forbidden during build')
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=pathlib.Path(args[0]).resolve()
  if p.is_relative_to(forbidden): raise RuntimeError('Original workspace access forbidden: '+str(p))
sys.path.insert(0,str(root/'tools'));sys.addaudithook(audit)
runpy.run_path(str(root/'tools/build.py'),run_name='__main__')
'''
        subprocess.run([sys.executable,'-c',guard,str(moved),str(ROOT.parent)],cwd=temp,check=True,capture_output=True,text=True)
        after=manifest(moved);assert before==after,'Relocated build is not deterministic'
    report={'pages':len(pages),'local_references':references,'terms':len(terms),'lessons':18,'independent_rebuild':'passed','external_runtime_resources':0}
    dest=ROOT/'qa/artifacts';dest.mkdir(exist_ok=True);(dest/'static.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
