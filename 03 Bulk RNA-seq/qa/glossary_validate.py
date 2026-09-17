"""Check scope, old links, course preservation, protected text and glossary data."""
from pathlib import Path
import collections, datetime, hashlib, json, re, sys
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from glossary import ProseTerms

errors = []
def check(ok, message):
    if not ok: errors.append(message)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
g = json.loads((ROOT/'content/glossary.json').read_text())
entries = g['entries']; ids = {e['id'] for e in entries}
anchors = {e['anchor'] for e in entries}
by_id = {e['id']: e for e in entries}
check(len(ids) == len(entries) == len(anchors), 'duplicate entry id or anchor')
for e in entries:
    for field in ['zh','en','summary','example','in_course','pitfall']:
        check(bool(e[field].strip()), f'empty {field}: {e["id"]}')
    check(set(e['related']) <= ids, 'unknown related: '+e['id'])
    check(e['category'] in g['categories'], 'unknown category: '+e['id'])
    check(bool(e['aliases']), 'no aliases: '+e['id'])

manifest = json.loads((ROOT/'qa/v2_backup_manifest.json').read_text())
publish_style_sha256 = '1f8ddd75ebc4ac1a8418bce8d26dc7d344b69ab7e7b126d8decc22aa2be241f5'
original = ROOT.parent/manifest['original']; backup = ROOT.parent/manifest['backup']
old = manifest['legacy_terms']
for n, name in enumerate(old, 1):
    e = next((e for e in entries if e.get('legacy_name') == name), None)
    check(e is not None and e['anchor'] == f'glossary-{n}' and name in e['aliases'], 'lost old term or anchor: '+name)

historical = {}
for directory in [original, backup]:
    historical[directory.name] = directory.is_dir()
    if directory.is_dir():
        actual = {str(p.relative_to(directory)): sha(p) for p in directory.rglob('*') if p.is_file()}
        check(actual == manifest['files'], 'V2 original or backup changed: '+directory.name)
old_zip = original.with_suffix('.zip')
if old_zip.is_file():
    check(sha(old_zip) == manifest['original_zip_sha256'], 'V2 ZIP changed')

# All old files except these narrow implementation / delivery / QA changes must stay identical.
allowed = {'01_海岛探险教案.html','02_完整教案_阅读与打印.html','tools/build.py',
           'tools/index.template.html','content/glossary.json','assets/app.js','assets/lessons.js',
           'assets/style.css','README.md','请先阅读_打开方式.txt','qa/print_validate.py','qa/README.md'}
changed = []
for name, digest in manifest['files'].items():
    p = ROOT/name
    check(p.is_file(), 'removed V2 file: '+name)
    if p.is_file() and sha(p) != digest:
        changed.append(name)
        check(name in allowed or name.startswith('qa/'), 'out-of-scope change: '+name)
check(sha(ROOT/'assets/style.css') == publish_style_sha256, 'published homepage styling changed')
check(sha(ROOT/'assets/figures.js') == manifest['files']['assets/figures.js'], 'figure behavior changed')

def lessons(path):
    s = path.read_text()
    return json.loads(s[len('window.LESSONS='):s.index(';\nwindow.FIGURES=')])
def strip_terms(s):
    return re.sub(r'<(?:a|button) class="term"(?=\s|>)[^>]*>(.*?)</(?:a|button)>', r'\1', s, flags=re.S)

new_lessons = lessons(ROOT/'assets/lessons.js')
check([e['id'] for e in new_lessons] == list(manifest['lesson_markup_sha256']), 'lesson order changed')
for new in new_lessons:
    raw_hash = hashlib.sha256(strip_terms(new['html']).encode()).hexdigest()
    meta_hash = hashlib.sha256(json.dumps({k:v for k,v in new.items() if k!='html'},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    check(raw_hash == manifest['lesson_markup_sha256'].get(new['id']), 'authored HTML changed: '+new['id'])
    check(meta_hash == manifest['lesson_metadata_sha256'].get(new['id']), 'station metadata changed: '+new['id'])

coverage = json.loads((ROOT/'qa/glossary_coverage.json').read_text())
records = coverage['occurrences']
counter = collections.Counter((r['scope'],r['term']) for r in records)
check(all(v == 1 for v in counter.values()), 'repeated mark in a first-occurrence scope')
check(set(coverage['station_coverage']) == {e['id'] for e in new_lessons}, 'station without term support')
linked = {r['term'] for r in records}
incoming = {tid for e in entries for tid in e['related']}
for e in entries:
    if e['id'] not in linked:
        check(bool(e.get('annotation_note')) and e['id'] in incoming, 'unexplained coverage gap: '+e['id'])

# Exercise real ambiguity and first-occurrence behavior, beyond mirroring the implementation.
def mark(source, station='de'):
    return ProseTerms(entries, g['reading_page'], station).annotate(source)
sample = ('<h2 id="one">RNA 与基因</h2><p>RNA RNA-seq RNA，转录本、转录、基因组、基因；'
          'counts Count BP bp；GO:0019761 ZT4_rep_1 sample.fastq.gz case/GO_BP.tsv log2(TMM + 1)</p>'
          '<figure><figcaption>RNA RNA</figcaption></figure><p>RNA</p>'
          '<h2 id="two">下一节</h2><p>RNA</p><pre><code>RNA counts</code></pre>'
          '<p><code>TPM / norm.factor</code><code>NumReads</code><a href="x">RNA</a></p>'
          '<svg><text>RNA</text></svg>')
marked, cases = mark(sample)
check(strip_terms(marked) == sample, 'annotation rewrites text/markup')
check(sum(r['term']=='rna' for r in cases) == 3, 'subsection / independent-figure scope regression')
check([r['term'] for r in cases if r['surface'] in ['counts','Count','BP','bp']] == ['counts','enrichment_count','go_bp','base'], 'field or case collision')
check(not any(r['surface'] in ['GO','TMM','FASTQ'] for r in cases), 'ID/path/formula annotated')
check('gene' in {r['term'] for r in cases} and 'genome' in {r['term'] for r in cases}, 'gene/genome longest match')
check('numreads' in {r['term'] for r in cases}, 'standalone field should have an explanation')
check('norm_factor' not in {r['term'] for r in cases}, 'formula must remain intact')
check(mark('<p>模块 背景</p>', 'qc')[1][0]['term'] == 'qc_module', 'FastQC module mislabeled')
check(not any(r['term']=='background' for r in mark('<p>变异的背景、红背景</p>', 'de')[1]), 'ordinary background mislabeled')

class Reading(HTMLParser):
    def __init__(self): super().__init__(); self.anchors=set(); self.entries=[]; self.terms=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.anchors.add(a['id'])
        if tag=='article' and 'data-entry' in a: self.entries.append(a['data-entry'])
        if a.get('class')=='term': self.terms.append(a)
reader = Reading();reader.feed((ROOT/g['reading_page']).read_text())
check(anchors <= reader.anchors, 'missing printable anchor')
check(set(reader.entries)==ids and len(reader.entries)==len(entries), 'print appendix missing or repeated entry')
for a in reader.terms:
    check(a['data-term'] in ids and a['href']=='#'+by_id[a['data-term']]['anchor'], 'invalid reading fallback')

result = {'pass':not errors,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'entries':len(entries),'legacy_anchors_preserved':len(old),'marked_occurrences':len(records),
          'stations':len(new_lessons),'v2_original_and_backup_files':len(manifest['files']),
          'historical_folders_available':historical,
          'unchanged_course_html_after_removing_term_wrappers':not any('authored HTML changed' in e for e in errors),
          'changed_existing_files':changed,
          'supplementary_terms':[e['id'] for e in entries if e['id'] not in linked],
          'errors':errors}
(ROOT/'qa/glossary_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(1 if errors else 0)
