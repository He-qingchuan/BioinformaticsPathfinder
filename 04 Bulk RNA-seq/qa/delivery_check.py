"""Final delivery audit. Historical folders are checked when present beside this package."""
from pathlib import Path
import datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
baseline=json.loads((ROOT/'qa/v1_backup_manifest.json').read_text())
checks={};errors=[]
for name in ['original','backup']:
    folder=ROOT.parent/baseline[name]
    if folder.is_dir():
        observed=hashes(folder)
        checks[name]={'files':len(observed),'unchanged':observed==baseline['files']}
        if not checks[name]['unchanged']:errors.append(name+' differs from original snapshot')
    else:checks[name]={'available':False,'note':'Historical folder is optional when sharing the independent V2 package.'}
old_zip=ROOT.parent/'转录组海岛教案.zip'
if old_zip.is_file():
    checks['original_zip']={'sha256':digest(old_zip),'unchanged':digest(old_zip)==baseline['original_zip_sha256']}
    if not checks['original_zip']['unchanged']:errors.append('original ZIP modified')
selected={key:value for key,value in baseline['files'].items() if key.startswith('case/') and not key.startswith('case/0script/')}
changed=[key for key,value in selected.items() if not (ROOT/key).is_file() or digest(ROOT/key)!=value]
checks['retained_case_results']={'files':len(selected),'unchanged':not changed,'differences':changed};errors+=changed
snapshot=json.loads((ROOT/'qa/docs_import.json').read_text())
source=Path(snapshot['source_project'])
local_mismatch=[row['file'] for row in snapshot['files'] if digest(ROOT/row['file'])!=row['sha256']]
source_mismatch=[row['source'] for row in snapshot['files'] if source.is_dir() and (not (source/row['source']).is_file() or digest(source/row['source'])!=row['source_sha256'])]
checks['documents_snapshot']={'counts':snapshot['counts'],'files':len(snapshot['files']),'local_matches':not local_mismatch,'source_available':source.is_dir(),'matches_current_source':not source_mismatch if source.is_dir() else None}
errors+=local_mismatch+source_mismatch
for name in ['static_validation','browser_validation','figures_review','responsive_review','print_review','independence_validation']:
    data=json.loads((ROOT/'qa'/f'{name}.json').read_text())
    checks[name]={'pass':data['pass']}
    if not data['pass']:errors.append(name+' failed')
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery_check.json']
checks['package']={'files_before_this_record':len(files),'bytes_before_this_record':sum(p.stat().st_size for p in files),'symlinks':[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_symlink()]}
errors+=checks['package']['symlinks']
result={'pass':not errors,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'errors':errors}
(ROOT/'qa/delivery_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(1 if errors else 0)
