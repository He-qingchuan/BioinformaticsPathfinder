"""Create a deterministic full textbook ZIP without caches, tests' artifacts or itself."""
from pathlib import Path
from hashlib import sha256
from build import archive

root=Path(__file__).resolve().parents[1]
dest=root/'dist';dest.mkdir(exist_ok=True)
version=(root/'VERSION').read_text().strip()
excluded={'dist','node_modules','artifacts','__pycache__','.cache','.Rproj.user','.Rhistory','.RData','.git'}
files=[(p,p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(root).parts)
       and ('results' not in p.relative_to(root).parts or p.name=='README.md')]
output=dest/f'r-v{version}.zip'
archive(output,files,prefix='R入门教材/')
checksum=output.with_suffix('.zip.sha256')
checksum.write_text(f'{sha256(output.read_bytes()).hexdigest()}  {output.name}\n',encoding='utf-8')
print(output)
print(checksum)
