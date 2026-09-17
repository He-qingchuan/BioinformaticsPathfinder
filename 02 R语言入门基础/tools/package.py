"""Create a deterministic full textbook ZIP without caches, tests' artifacts or itself."""
from pathlib import Path
from build import archive

root=Path(__file__).resolve().parents[1]
dest=root/'dist';dest.mkdir(exist_ok=True)
version=(root/'VERSION').read_text().strip()
files=[(p,p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file() and not any(x in p.relative_to(root).parts for x in ['dist','node_modules','artifacts','__pycache__'])]
output=dest/f'r-v{version}.zip'
archive(output,files,prefix='R入门教材/')
print(output)
