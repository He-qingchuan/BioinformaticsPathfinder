"""Render one glossary source and annotate prose without rewriting authored text."""
from html import escape
from html.parser import HTMLParser
from collections import Counter
import re

E = lambda value: escape(str(value), quote=True)
FIELDS = [('summary', '先用一句话理解'), ('example', '放到例子里'),
          ('in_course', '在本课里有什么用'), ('pitfall', '容易混淆的地方')]


def render_entry(entry, entries, reading_page, appendix=False):
    """The popup and printable appendix use exactly the same four paragraphs."""
    destination = '' if appendix else reading_page
    anchor = f' id="{E(entry["anchor"])}"' if appendix else ''
    abbr = f' · 常用缩写／字段：{E(entry["abbr"])}' if entry['abbr'] else ''
    paragraphs = ''.join(f'<div class="glossary-part"><h4>{label}</h4><p>{E(entry[field])}</p></div>'
                         for field, label in FIELDS)
    related = ''.join(f'<a href="{E(destination)}#{E(entries[tid]["anchor"])}" data-term="{E(tid)}" aria-haspopup="dialog">{E(entries[tid]["zh"])}</a>'
                      for tid in entry['related'])
    aliases = '、'.join(dict.fromkeys(entry['aliases']))
    sources = ''.join(f'<a href="{E(s["url"])}" target="_blank" rel="noopener noreferrer">{E(s["label"])} ↗</a>' for s in entry.get('sources', []))
    if sources:
        sources = f'<div class="glossary-sources"><span>延伸核对（联网时可读）：</span>{sources}</div>'
    return (f'<article class="glossary-entry" data-entry="{E(entry["id"])}"{anchor}>'
            f'<p class="glossary-category">{E(entry["category"])}</p>'
            f'<h3>{E(entry["zh"])}</h3><p class="glossary-english"><span lang="en">{E(entry["en"])}</span>{abbr}</p>'
            f'{paragraphs}<p class="glossary-aliases">也可这样查：{E(aliases)}</p>'
            f'<div class="glossary-related"><span>接着理解：</span>{related}</div>{sources}</article>')


class ProseTerms(HTMLParser):
    """Longest aliases; first occurrence per subsection or independent figure.

    Source HTML is emitted verbatim except for added anchors. SVG, controls,
    existing links, commands and paths are left alone. A short inline-code
    token is eligible only when the complete token is a known alias.
    """
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
            'meta', 'param', 'source', 'track', 'wbr'}
    SKIP_TAGS = {'svg', 'math', 'script', 'style', 'pre', 'a', 'button', 'input',
                 'select', 'textarea', 'output', 'label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
    SKIP_CLASSES = {'figure-kicker', 'figure-actions', 'figure-sources', 'lab',
                    'quiz', 'resource-links', 'art-scroll-hint', 'reading-label'}
    # Protect full filenames/paths, identifiers and intact formulas before matching.
    PROTECTED = re.compile(
        r'(?:https?://|(?:\.\.?/))[\w./:%?=#&+~-]+|'
        r'[A-Za-z0-9_./-]+\.(?:tsv|csv|gz|fasta|fastq|fq|fa|gtf|sf|html|json|R|sh|py|svg|png|pdf|zip)\b|'
        r'\b(?:AT\dG\d+|GO:\d+|K\d{5}|ath\d{5}|ZT\d+(?:_rep_\d+|_vs_ZT\d+)?)\b|'
        r'\blog(?:[₂2]|10)\s*\([^\n)]*\)')

    def __init__(self, entries, reading_page, station):
        super().__init__(convert_charrefs=False)
        self.entries = {e['id']: e for e in entries}
        self.reading_page, self.station = reading_page, station
        self.aliases = {}
        for e in entries:
            for alias in e['aliases']:
                if alias in self.aliases and self.aliases[alias] != e['id']:
                    raise ValueError('Ambiguous prose alias: ' + alias)
                self.aliases[alias] = e['id']
        # A FastQC report module is a check, not a time-expression cluster.
        if station in {'qc', 'filter'}:
            self.aliases['模块'] = 'qc_module'
        # Auto-marking is case-sensitive: bp / BP and counts / Count differ.
        parts = []
        for a in sorted(self.aliases, key=lambda a: (-len(a), a)):
            left = r'(?<![A-Za-z0-9_])' if re.match('[A-Za-z0-9_]', a) else ''
            right = r'(?![A-Za-z0-9_])' if re.search('[A-Za-z0-9_]$', a) else ''
            parts.append(left + re.escape(a) + right)
        self.pattern = re.compile('|'.join(parts))
        self.stack, self.output, self.records = [], [], []
        self.scope = self.new_scope('opening')
        self.figure_scopes = []
        self.section_number = self.figure_number = 0

    def new_scope(self, name):
        return {'name': f'{self.station}/{name}', 'seen': set()}

    def annotate(self, source):
        self.source = source
        self.offsets = [0]
        self.offsets.extend(m.end() for m in re.finditer('\n', source))
        self.feed(source)
        self.close()
        assert not self.stack, [e['tag'] for e in self.stack]
        return ''.join(self.output), self.records

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        self.output.append(raw)
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        parent_skip = bool(self.stack and self.stack[-1]['skip'])
        if tag in {'h2', 'h3'} and not self.figure_scopes and not parent_skip:
            self.section_number += 1
            self.scope = self.new_scope(attrs.get('id', f'subsection-{self.section_number}'))
        if tag == 'figure':
            self.figure_number += 1
            self.figure_scopes.append(self.new_scope('figure-' + attrs.get('data-figure', attrs.get('data-illustration', str(self.figure_number)))))
        skip = parent_skip or tag in self.SKIP_TAGS or bool(classes & self.SKIP_CLASSES)
        if tag == 'strong' and self.stack and 'figure-summary' in self.stack[-1]['classes']:
            skip = True  # caption title, not the first explanatory sentence
        if tag not in self.VOID:
            self.stack.append({'tag': tag, 'classes': classes, 'skip': skip})

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        line, col = self.getpos()
        start = self.offsets[line - 1] + col
        end = self.source.index('>', start) + 1
        self.output.append(self.source[start:end])
        if self.stack:
            frame = self.stack.pop()
            assert frame['tag'] == tag, (frame['tag'], tag, self.station)
        if tag == 'figure':
            self.figure_scopes.pop()

    def handle_data(self, data):
        if not data.strip() or (self.stack and self.stack[-1]['skip']):
            self.output.append(data)
            return
        if any(e['tag'] == 'code' for e in self.stack) and data.strip() not in self.aliases:
            self.output.append(data)
            return
        protected = [(m.start(), m.end()) for m in self.PROTECTED.finditer(data)]
        scope = self.figure_scopes[-1] if self.figure_scopes else self.scope

        def mark(match):
            term = match.group(0)
            tid = self.aliases[term]
            if any(match.start() < b and match.end() > a for a, b in protected):
                return term
            # These ordinary phrases do not refer to enrichment background/annotation.
            if term == '背景':
                if self.station not in {'ora', 'gsea', 'trend', 'nonmodel'}:
                    return term
                if data[max(0, match.start()-2):match.start()] in {'研究', '实验', '颜色', '功能'}:
                    return term
            if tid in scope['seen']:
                return term
            scope['seen'].add(tid)
            e = self.entries[tid]
            self.records.append({'station': self.station, 'scope': scope['name'], 'term': tid,
                                 'surface': term, 'context': data[max(0, match.start()-28):match.end()+45]})
            return (f'<a class="term" data-term="{E(tid)}" href="{E(self.reading_page)}#{E(e["anchor"])}" '
                    f'aria-haspopup="dialog" title="{E(e["zh"])} · {E(e["en"])}">{term}</a>')
        self.output.append(self.pattern.sub(mark, data))

    def handle_entityref(self, name):
        self.output.append('&' + name + ';')

    def handle_charref(self, name):
        self.output.append('&#' + name + ';')

    def handle_comment(self, data):
        self.output.append('<!--' + data + '-->')

    def handle_decl(self, decl):
        self.output.append('<!' + decl + '>')


def coverage_report(entries, records):
    count = Counter(r['term'] for r in records)
    by_station = {}
    for r in records:
        by_station.setdefault(r['station'], set()).add(r['term'])
    return {'terms': len(entries), 'marked_occurrences': len(records),
            'first_occurrence_rule': 'Each prose h2/h3 subsection; each independent figure has its own scope. Headings, controls, SVG and protected strings are excluded.',
            'station_coverage': {k: sorted(v) for k, v in by_station.items()},
            'entries': [{'id': e['id'], 'zh': e['zh'], 'en': e['en'], 'anchor': e['anchor'],
                         'marked_occurrences': count[e['id']]} for e in entries],
            'occurrences': records}
