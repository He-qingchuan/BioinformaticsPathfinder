"""Execute every lesson in a fresh R process and an isolated copy of the lab."""
import argparse, concurrent.futures, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--rscript',default=shutil.which('Rscript'))
parser.add_argument('--record',action='store_true')
parser.add_argument('--workers',type=int,default=3)
args=parser.parse_args()
if not args.rscript: raise SystemExit('Rscript not found. Install R or supply --rscript /path/to/Rscript.')
artifacts=ROOT/'qa/artifacts'; artifacts.mkdir(exist_ok=True)

def run(path):
    with tempfile.TemporaryDirectory(prefix='r-course-') as tmp:
        lab=Path(tmp)/'独立 R 练习';shutil.copytree(ROOT/'practice/r-lab',lab,ignore=shutil.ignore_patterns('results','.Rproj.user','.RData','.Rhistory'))
        (lab/'results').mkdir()
        command=[args.rscript,'--vanilla',str(lab/'lessons'/path.name)]
        env=os.environ.copy(); env['XDG_CACHE_HOME']=str(lab/'.cache'); env['TZ']='UTC'
        done=subprocess.run(command,cwd=lab,env=env,capture_output=True,text=True,encoding='utf-8',timeout=300)
        if done.returncode: raise AssertionError(f'{path.name}: {done.stdout}\n{done.stderr}')
        if done.stderr.strip(): raise AssertionError(f'Unexpected warning/message in {path.name}: {done.stderr}')
        output=done.stdout.replace('\r\n','\n')
        expected=ROOT/'practice/expected'/f'{path.stem}.txt'
        if args.record: expected.write_text(output,encoding='utf-8')
        elif expected.read_text(encoding='utf-8') != output:
            (artifacts/f'{path.stem}-actual.txt').write_text(output,encoding='utf-8')
            raise AssertionError(f'Reference output mismatch: {path.name}; see qa/artifacts/{path.stem}-actual.txt')
        plots=[]
        for image in sorted((lab/'results').rglob('*.png')):
            name=f'{path.stem}-{image.stem}.png' if image.parent.name in ('first-week','next-week') else image.name
            content=image.read_bytes()
            assert content[:8]==b'\x89PNG\r\n\x1a\n' and len(content)>5000,image
            if args.record: (ROOT/'assets/plots'/name).write_bytes(content)
            plots.append(name)
        if path.stem=='35' and args.record:
            shutil.copyfile(lab/'results/first-week/report.md',ROOT/'practice/expected/report.md')
        return dict(lesson=path.stem,output_sha256=hashlib.sha256(output.encode()).hexdigest(),plots=plots)

with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    results=list(pool.map(run,sorted((ROOT/'practice/r-lab/lessons').glob('*.R'))))
versions=subprocess.run([args.rscript,'--vanilla','-e','cat(R.version.string,"\\n"); for(p in c("dplyr","tidyr","stringr","ggplot2")) cat(p, as.character(packageVersion(p)),"\\n")'],capture_output=True,text=True,encoding='utf-8',check=True)
report=dict(status='passed',fresh_processes=len(results),platform=os.name,environment=versions.stdout,lessons=results)
(artifacts/'r-execution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='lessons'},ensure_ascii=False))
