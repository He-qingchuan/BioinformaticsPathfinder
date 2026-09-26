"""Synchronize, verify and package the single project release. No network or publishing."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/He-qingchuan/BioinformaticsPathfinder'
COURSES = {
    'linux': '01 Linux入门基础',
    'r': '02 R语言入门基础',
    'python': '03 Python入门基础',
    'rnaseq': '04 Bulk RNA-seq',
    'scrna': '05 Single-cell RNA-seq',
}
BEGIN, END = '<!-- PROJECT RELEASE -->', '<!-- /PROJECT RELEASE -->'


def version():
    value = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('Root VERSION must contain major.minor.patch, without v')
    return value


def block(v, slug=None):
    suffix = f'-{slug}' if slug else ''
    label = '本课程离线包' if slug else '整个项目离线包'
    return (f'{BEGIN}\n\n**项目统一版本：v{v}** · '
            f'[版本说明]({REPO}/releases/tag/v{v}) · '
            f'[{label}]({REPO}/releases/download/v{v}/BioinformaticsPathfinder-v{v}{suffix}.zip)\n\n'
            '所有课程共享同一项目版本；分包名称中的课程名仅用于选择下载内容。\n\n'
            f'{END}')


def sync():
    v = version()
    for slug, directory in COURSES.items():
        course = ROOT / directory
        (course / 'VERSION').write_text(v + '\n', encoding='utf-8')
        config = course / 'content/course.json'
        if config.exists():
            data = json.loads(config.read_text(encoding='utf-8'))
            data['version'] = v
            config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for slug, directory in [(None, ''), *COURSES.items()]:
        readme = ROOT / directory / 'README.md'
        text = readme.read_text(encoding='utf-8')
        replacement = block(v, slug)
        if BEGIN in text:
            text = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: replacement, text, flags=re.S)
        else:
            head, tail = text.split('\n', 1)
            text = head + '\n\n' + replacement + '\n' + tail
        readme.write_text(text, encoding='utf-8')
    print(f'Synchronized project v{v}')


def build():
    check_versions()
    for directory in COURSES.values():
        source = ROOT / directory / 'tools/build.py'
        if source.exists():
            subprocess.run([sys.executable, str(source)], cwd=source.parent.parent, check=True)


def check_versions():
    v = version()
    assert f'## v{v} · ' in (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'), 'Missing changelog entry'
    for slug, directory in [(None, ''), *COURSES.items()]:
        course = ROOT / directory
        assert block(v, slug) in (course / 'README.md').read_text(encoding='utf-8'), f'Stale README: {directory}'
        assert (course / 'VERSION').read_text(encoding='utf-8').strip() == v, f'Stale VERSION: {directory}'
        config = course / 'content/course.json'
        if config.exists():
            assert json.loads(config.read_text(encoding='utf-8'))['version'] == v, f'Stale config: {directory}'


def check():
    check_versions()
    v = version()
    for slug, directory in COURSES.items():
        if slug == 'python':
            continue
        home = 'index.html' if slug in ('linux', 'r') else '01_海岛探险教案.html'
        text = (ROOT / directory / home).read_text(encoding='utf-8')
        assert f'项目 v{v}' in text, f'Stale rendered version: {directory}'
        target = ROOT / directory / ('library.html' if slug in ('linux', 'r') else home)
        expected = f'{REPO}/releases/download/v{v}/BioinformaticsPathfinder-v{v}-{slug}.zip'
        assert expected in target.read_text(encoding='utf-8'), f'Stale download: {directory}'
    print(f'Project v{v}: all five version snapshots, README blocks and four course websites match')


def tracked_files():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True, capture_output=True)
    files = [Path(p) for p in result.stdout.decode('utf-8').split('\0') if p]
    for p in files:
        assert (ROOT / p).is_file() and not (ROOT / p).is_symlink(), f'Missing/unsafe release file: {p}'
        assert not {'node_modules', '.git', '__pycache__', 'dist', '.cache'}.intersection(p.parts), p
    return sorted(files)


def archive(dest, files, prefix, relative_to=Path('.')):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as output:
        for p in files:
            name = prefix + '/' + p.relative_to(relative_to).as_posix()
            info = zipfile.ZipInfo(name, (2026, 9, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, (ROOT / p).read_bytes())
    with zipfile.ZipFile(dest) as output:
        assert output.testzip() is None, dest
        assert len(output.namelist()) == len(files), dest


def package():
    check()
    v = version()
    files = tracked_files()
    # Staging is required for newly added release sources; never silently omit them.
    assert {Path('VERSION'), Path('CHANGELOG.md'), Path('RELEASING.md'), Path('tools/project_release.py')} <= set(files)
    dest = ROOT / 'dist'
    dest.mkdir(exist_ok=True)
    outputs = []
    for slug, directory in [(None, ''), *COURSES.items()]:
        name = f'BioinformaticsPathfinder-v{v}' + (f'-{slug}' if slug else '')
        selected = [p for p in files if p.is_relative_to(directory)] if directory else files
        assert Path(directory) / 'VERSION' in selected
        target = dest / (name + '.zip')
        archive(target, selected, name, Path(directory))
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        outputs.append(f'{digest}  {target.name}\n')
        print(f'{target.name}: {len(selected)} files, {target.stat().st_size} bytes')
        print(outputs[-1].strip())
    (dest / 'SHA256SUMS').write_text(''.join(outputs), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sync', 'build', 'check', 'package'])
    args = parser.parse_args()
    globals()[args.command]()
