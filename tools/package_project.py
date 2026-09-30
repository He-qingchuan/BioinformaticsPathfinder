"""Package every tracked file from one Git snapshot, preserving all project modules."""
from pathlib import Path
import argparse
import hashlib
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(ref='HEAD', output=None):
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', ref + '^{commit}'], cwd=ROOT, text=True).strip()
    if re.fullmatch(r'v\d+\.\d+\.\d+', ref):
        label = ref
    else:
        value = subprocess.check_output(['git', 'show', commit + ':VERSION'], cwd=ROOT, text=True).strip()
        if not re.fullmatch(r'\d+\.\d+\.\d+', value):
            raise ValueError('Project VERSION must be major.minor.patch')
        label = 'v' + value
    dest = Path(output).resolve() if output else ROOT / 'dist' / label
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / 'BioinformaticsPathfinder.zip'
    subprocess.run(['git', 'archive', '--format=zip', '--prefix=BioinformaticsPathfinder/',
                    '--output', str(target), commit], cwd=ROOT, check=True)
    expected = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', commit], cwd=ROOT).decode().strip('\0').split('\0'))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        actual = {n[len('BioinformaticsPathfinder/'):] for n in z.namelist() if not n.endswith('/')}
        assert actual == expected, 'Archive differs from the Git snapshot'
    modules = sorted({n.split('/')[0] for n in expected if re.match(r'^\d{2}', n)})
    with target.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest + '  ' + target.name + '\n', encoding='utf-8')
    print(f'{label}: {commit}; {len(expected)} files; {len(modules)} module directories')
    print(' | '.join(modules))
    print(digest + '  ' + str(target))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='Commit or version tag to package')
    parser.add_argument('--output', help='Output directory; default: dist/<version>')
    args = parser.parse_args()
    package(args.ref, args.output)
