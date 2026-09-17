#!/usr/bin/env python3
"""Explicitly copy a V9 documentation snapshot. Never run analysis or import results."""
from pathlib import Path
import argparse, csv, datetime, hashlib, json

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path, help='V9 案例根目录，内含 0script')
    args = parser.parse_args()
    source = args.project.resolve()
    directory = source / '0script'
    if not (directory / '04.5 分析前准备检查.md').is_file():
        parser.error('来源缺少新版 04.5 文档；没有复制文件。')
    paths = sorted(set(directory.glob('*.md')) | set(directory.glob('*.tsv')) |
                   {directory / 'project.env'} |
                   {p for folder in ['scripts', 'tools'] for p in (directory/folder).rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts})
    if any(not p.is_file() or not p.resolve().is_relative_to(source) for p in paths):
        parser.error('来源文件缺失或指向项目外；没有复制文件。')
    # Read and fingerprint the entire snapshot before replacing any local document.
    snapshot = [(p, p.read_bytes()) for p in paths]
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = json.loads((ROOT/'素材来源.json').read_text())
    old = {r['file']: r for r in manifest['files']}
    copied = []
    for src, data in snapshot:
        relative = src.relative_to(source)
        dst = ROOT/'case'/relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        assert digest(dst) == checksum
        row = {'source': str(relative), 'file': str(dst.relative_to(ROOT)), 'kind': 'copy',
               'detail': 'V9 资料快照；按字节复制；'+timestamp,
               'source_sha256': checksum, 'sha256': checksum, 'bytes': len(data)}
        old[row['file']] = row
        copied.append(row)
    manifest['files'] = list(old.values())
    manifest['documents_snapshot_utc'] = timestamp
    manifest['note'] = '源路径仅用于追溯。网页浏览与默认构建只读取包内素材；本次仅复制最新文档、源码和小型入口表，既有案例结果未重新计算。'
    (ROOT/'素材来源.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    with (ROOT/'素材来源.tsv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['source','file','kind','detail','source_sha256','sha256','bytes'], delimiter='\t', lineterminator='\n')
        writer.writeheader(); writer.writerows(manifest['files'])
    record = {'source_project': str(source), 'snapshot_utc': timestamp, 'files': copied,
              'counts': {'markdown': len(list(directory.glob('*.md'))),
                         'scripts': sum(p.parent.name == 'scripts' for p in paths),
                         'tools': sum(p.parent.name == 'tools' for p in paths)}}
    (ROOT/'qa/docs_import.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'copied':len(copied), **record['counts']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
