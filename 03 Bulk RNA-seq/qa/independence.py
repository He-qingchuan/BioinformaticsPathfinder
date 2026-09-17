"""Rebuild a relocated copy while denying access to every original workspace file."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

with tempfile.TemporaryDirectory(prefix='rnaseq-v2-isolation-') as tmp:
    moved=Path(tmp)/'移动 后的独立教案'
    shutil.copytree(ROOT,moved,ignore=shutil.ignore_patterns('qa','__pycache__'))
    before=hashes(moved)
    runner=r'''
from pathlib import Path
import json,runpy,sys
root=Path(sys.argv[1]).resolve(); forbidden=Path(sys.argv[2]).resolve()
external=set(); denied=[]
def audit(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:
        denied.append(event);raise RuntimeError('Network unavailable in independent rebuild')
    if event not in ['open','os.listdir','os.scandir']:return
    value=args[0]
    if not isinstance(value,(str,bytes)):return
    path=Path(value).resolve()
    if path.is_relative_to(forbidden):
        denied.append(str(path));raise RuntimeError('Original workspace unavailable: '+str(path))
    if event=='open' and not path.is_relative_to(root):external.add(str(path))
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'tools'))
sys.addaudithook(audit)
runpy.run_path(str(root/'tools/build.py'),run_name='__main__')
print(json.dumps({'denied_attempts':denied,'external_runtime_reads':sorted(external)},ensure_ascii=False))
'''
    result=subprocess.run([sys.executable,'-B','-c',runner,str(moved),str(WORKSPACE)],cwd=moved,capture_output=True,text=True)
    if result.returncode:
        print(result.stdout);print(result.stderr);raise SystemExit(result.returncode)
    audit=json.loads(result.stdout.strip().splitlines()[-1])
    after=hashes(moved)
    changed=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    if changed:raise RuntimeError('Rebuild not reproducible: '+repr(changed))
    check={'pass':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'relocated_folder_name':moved.name,'original_workspace_denied':str(WORKSPACE),
           'bundled_files_unchanged_after_rebuild':len(after),'changes':changed,**audit,
           'scope':'Only the page generator ran. All original workspace files and network calls were unavailable; the Python interpreter and markdown-it-py remained available.'}
    (ROOT/'qa/independence_validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(check,ensure_ascii=False))
