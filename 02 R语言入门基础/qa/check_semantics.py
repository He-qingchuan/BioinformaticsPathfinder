import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--rscript',default=shutil.which('Rscript'));a=p.parse_args()
if not a.rscript:raise SystemExit('Rscript not found')
with tempfile.TemporaryDirectory(prefix='r-semantics-') as temp:
 lab=Path(temp)/'独立 R 项目';shutil.copytree(root/'practice/r-lab',lab,ignore=shutil.ignore_patterns('results','.Rproj.user'))
 (lab/'results').mkdir();env=os.environ.copy();env['TZ']='UTC';env['XDG_CACHE_HOME']=str(lab/'.cache')
 done=subprocess.run([a.rscript,'--vanilla',str(root/'qa/check_semantics.R')],cwd=lab,env=env,text=True,encoding='utf-8',capture_output=True,timeout=300)
 if done.returncode or done.stderr.strip():raise SystemExit(done.stdout+'\n'+done.stderr)
 print(done.stdout.strip())
 dest=root/'qa/artifacts';dest.mkdir(exist_ok=True)
 (dest/'r-semantics.json').write_text(json.dumps(dict(status='passed',checks=done.stdout.strip()),ensure_ascii=False,indent=2)+'\n')
