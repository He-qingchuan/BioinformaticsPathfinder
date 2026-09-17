"""Final V3 checks; optional historical folders are never runtime dependencies."""
from pathlib import Path
import datetime, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/'qa/v2_backup_manifest.json').read_text())
publish_overrides = {
    'assets/style.css': '1f8ddd75ebc4ac1a8418bce8d26dc7d344b69ab7e7b126d8decc22aa2be241f5',
}
errors=[];checks={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for kind in ['original','backup']:
    folder=ROOT.parent/manifest[kind]
    if folder.is_dir():
        actual={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}
        checks[kind]={'available':True,'files':len(actual),'unchanged':actual==manifest['files']}
        if actual!=manifest['files']:errors.append(kind+' modified')
    else:checks[kind]={'available':False,'note':'Historical copies are optional after sharing.'}

protected={name:digest for name,digest in manifest['files'].items()
           if name.startswith(('case/','library/'))
           or name.startswith('content/') and name!='content/glossary.json'
           or name.startswith('assets/') and Path(name).suffix in {'.png','.svg'}
           or name in {'assets/style.css','assets/figures.js','assets/case.js','素材来源.json','素材来源.tsv'}}
protected.update(publish_overrides)
changed=[name for name,digest in protected.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=digest]
checks['protected_materials']={'files':len(protected),'unchanged':not changed,'differences':changed}
errors.extend(changed)
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
symlinks=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_symlink()]
shared=[]
source=ROOT.parent/manifest['original']
if source.is_dir():
    for p in files:
        q=source/p.relative_to(ROOT)
        if q.is_file() and (p.stat().st_dev,p.stat().st_ino)==(q.stat().st_dev,q.stat().st_ino):shared.append(str(p.relative_to(ROOT)))
checks['independent_copies']={'symlinks':symlinks,'shared_inodes_with_v2':shared}
errors+=symlinks+shared
for name in ['static_validation','glossary_validation','glossary_browser','browser_validation',
             'figures_review','responsive_review','print_review','independence_validation']:
    data=json.loads((ROOT/'qa'/f'{name}.json').read_text())
    checks[name]={'pass':data['pass']}
    if not data['pass']:errors.append(name+' failed')
glossary=json.loads((ROOT/'content/glossary.json').read_text())
checks['glossary']={'entries':len(glossary['entries']),'original_entries':26,
                    'new_entries':len(glossary['entries'])-26,'categories':len(glossary['categories'])}
old_zip=source.with_suffix('.zip')
if old_zip.is_file():
    unchanged=sha(old_zip)==manifest['original_zip_sha256']
    checks['v2_zip']={'unchanged':unchanged}
    if not unchanged:errors.append('original ZIP modified')
result={'pass':not errors,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'checks':checks,'errors':errors}
(ROOT/'qa/v3_delivery_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(errors))
