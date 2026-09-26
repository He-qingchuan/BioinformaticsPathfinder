"""Exercise a real next-patch release in an isolated copy, without touching this checkout."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from project_release import ROOT, tracked_files, version

with tempfile.TemporaryDirectory(prefix='project-next-release-') as temp:
    moved = Path(temp) / '下一版 项目'
    for relative in tracked_files():
        target = moved / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    major, minor, patch = map(int, version().split('.'))
    future = f'{major}.{minor}.{patch + 1}'
    (moved / 'VERSION').write_text(future + '\n', encoding='utf-8')
    changelog = moved / 'CHANGELOG.md'
    changelog.write_text(changelog.read_text(encoding='utf-8') + f'\n## v{future} · isolated test\n', encoding='utf-8')
    command = [sys.executable, str(moved / 'tools/project_release.py')]
    stale = subprocess.run(command + ['check'], cwd=moved, capture_output=True, text=True)
    assert stale.returncode != 0 and 'Stale README' in stale.stderr, 'Unpropagated release was not rejected'
    for action in ['sync', 'build', 'check']:
        subprocess.run(command + [action], cwd=moved, check=True)
    # Current repository remains at the original version, and no second checkout is retained.
    print(f'Next-patch migration to v{future} passed in a temporary copy; original project unchanged')
