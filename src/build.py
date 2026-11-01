# -*- coding: utf-8 -*-
"""Build the booklet.

Outputs:
  ../index.html            full web page (for GitHub Pages)
  build/artifact.html      same page without <html>/<head>/<body> (for claude.ai Artifacts)
  build/print.html         print version (cover + printed TOC) used to make the PDF

Usage:  python3 build.py            (HTML only)
        python3 build.py --pdf      (HTML + two-pass PDF with page numbers in the TOC)
"""
import base64
import html as htmllib
import json
import pathlib
import re
import subprocess
import sys

from figs import FIGS, fa

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / 'build'
OUT.mkdir(exist_ok=True)
CHAPTERS = ['00-front.html', '01-intro.html', '02-supply-demand.html', '03-elasticity.html',
            '04-surplus.html', '05-efficiency.html', '06-review.html']
PDF_NAME = 'jozve-mabani-eghtesad.pdf'
REPO_URL = 'https://github.com/iamhirad/economic-'
BRANCH = 'ccr-49b6c905-e6l1mr'
TITLE = 'جزوه مبانی اقتصاد'
FONTS = ('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;700;800'
         '&family=Markazi+Text:wght@500;700&display=swap')

FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
VOID = {'br', 'img', 'hr', 'input', 'meta', 'link', 'wbr', 'source', 'col', 'area', 'base', 'embed', 'track'}
SKIP_TAGS = {'svg', 'code', 'pre', 'script', 'style', 'math'}


# ---------------------------------------------------------------- math
MATH_RE = re.compile(r'\\\[(.+?)\\\]|\\\((.+?)\\\)', re.S)


def tok(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(97 + r) + s
    return '' + s + ''


def extract_math(html):
    items = []

    def repl(m):
        display = m.group(1) is not None
        tex = htmllib.unescape((m.group(1) if display else m.group(2)).strip())
        items.append({'tex': tex, 'display': display})
        return tok(len(items) - 1)
    return MATH_RE.sub(repl, html), items


def render_math(items):
    if not items:
        return []
    res = subprocess.run(['node', str(ROOT / 'katex_render.js')], input=json.dumps(items),
                         capture_output=True, text=True, cwd=ROOT)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
        raise SystemExit('KaTeX failed')
    return json.loads(res.stdout)


def put_math(html, items, rendered):
    for i, (it, r) in enumerate(zip(items, rendered)):
        wrap = f'<div class="eq">{r}</div>' if it['display'] else f'<span class="m">{r}</span>'
        html = html.replace(tok(i), wrap)
    return html


# ---------------------------------------------------------------- Persian digits
def fa_text(s):
    s = re.sub(r'(?<=\d)\.(?=\d)', '٫', s)
    s = re.sub(r'(?<=\d),(?=\d{3})', '٬', s)
    s = re.sub(r'(?<=\d)%', '٪', s)
    return s.translate(FA_DIGITS)


def persian_digits(html):
    parts = re.split(r'(<[^>]+>)', html)
    stack = []  # list of (tag, skip)
    out = []
    for p in parts:
        if p.startswith('<'):
            m = re.match(r'<\s*(/)?\s*([a-zA-Z0-9]+)', p)
            if not m or p.startswith('<!'):
                out.append(p)
                continue
            closing, name = m.group(1), m.group(2).lower()
            if closing:
                while stack:
                    t, _ = stack.pop()
                    if t == name:
                        break
            elif name not in VOID and not p.rstrip().endswith('/>'):
                parent_skip = stack[-1][1] if stack else False
                cls = re.search(r'class="([^"]*)"', p)
                classes = cls.group(1).split() if cls else []
                skip = (parent_skip or name in SKIP_TAGS or 'ltr' in classes or 'en' in classes or 'ch-en' in classes
                        or 'keep' in classes or 'dir="ltr"' in p)
                stack.append((name, skip))
            out.append(p)
        else:
            skip = stack[-1][1] if stack else False
            out.append(p if skip else fa_text(p))
    return ''.join(out)


# ---------------------------------------------------------------- figures
FIG_RE = re.compile(r'<figure data-fig="([a-z0-9_]+)"([^>]*)>')


def put_figs(html):
    def repl(m):
        name = m.group(1)
        if name not in FIGS:
            raise SystemExit(f'unknown figure {name}')
        return f'<figure data-fig="{name}"{m.group(2)}>' + FIGS[name]()
    return FIG_RE.sub(repl, html)


# ---------------------------------------------------------------- TOC
HEAD_RE = re.compile(r'<h([12]) id="([^"]+)"([^>]*)>(.*?)</h\1>', re.S)


def strip_tags(s):
    s = re.sub(r'<span class="en">.*?</span>', '', s, flags=re.S)
    s = re.sub(r'<span class="ch-num">.*?</span>', '', s, flags=re.S)
    s = re.sub(r'<span class="ch-en">.*?</span>', '', s, flags=re.S)
    s = re.sub(r'<span class="slides">.*?</span>', '', s, flags=re.S)
    return re.sub(r'<[^>]+>', '', s).strip()


def toc_entries(html):
    out = []
    for m in HEAD_RE.finditer(html):
        level, hid, attrs, inner = m.groups()
        if 'notoc' in attrs:
            continue
        out.append((int(level), hid, strip_tags(inner)))
    return out


def toc_web(entries):
    items = []
    for lvl, hid, text in entries:
        items.append(f'<li class="l{lvl}"><a href="#{hid}">{text}</a></li>')
    return '<ol>' + ''.join(items) + '</ol>'


def toc_print(entries, pages=None):
    items = []
    for lvl, hid, text in entries:
        pg = fa(pages[hid]) if pages and hid in pages else '۰۰'
        items.append(f'<li class="l{lvl}"><a class="t" href="#{hid}">{text}</a><span class="dots"></span>'
                     f'<span class="pg">{pg}</span></li>')
    return '<ol>' + ''.join(items) + '</ol>'


# ---------------------------------------------------------------- KaTeX css with embedded fonts
KEEP_FONTS = ['KaTeX_AMS-Regular', 'KaTeX_Main-Regular', 'KaTeX_Main-Bold', 'KaTeX_Main-Italic',
              'KaTeX_Math-Italic', 'KaTeX_Size1-Regular', 'KaTeX_Size2-Regular', 'KaTeX_Size3-Regular',
              'KaTeX_Size4-Regular']


def katex_css():
    kdir = ROOT / 'node_modules' / 'katex' / 'dist'
    css = (kdir / 'katex.min.css').read_text()
    out_faces = []
    for face in re.findall(r'@font-face\{[^}]*\}', css):
        m = re.search(r'url\(fonts/([A-Za-z0-9_-]+)\.woff2\)', face)
        name = m.group(1) if m else None
        if name in KEEP_FONTS:
            data = base64.b64encode((kdir / 'fonts' / f'{name}.woff2').read_bytes()).decode()
            fam = re.search(r'font-family:([^;]+);', face).group(1)
            style = re.search(r'font-style:([^;}]+)', face)
            weight = re.search(r'font-weight:([^;}]+)', face)
            out_faces.append('@font-face{font-family:%s;font-style:%s;font-weight:%s;font-display:swap;'
                             'src:url(data:font/woff2;base64,%s) format("woff2")}' % (
                                 fam, style.group(1) if style else 'normal',
                                 weight.group(1) if weight else '400', data))
    css = re.sub(r'@font-face\{[^}]*\}', '', css)
    return ''.join(out_faces) + css


# ---------------------------------------------------------------- page pieces
MARK = ('<svg class="mast-mark" viewBox="0 0 92 92" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M10 4 V84 H90" fill="none" stroke="currentColor" stroke-width="3"/>'
        '<path class="d" d="M18 14 L82 74" fill="none" stroke-width="5" stroke-linecap="round"/>'
        '<path class="s" d="M18 74 L82 14" fill="none" stroke-width="5" stroke-linecap="round"/>'
        '<circle cx="50" cy="44" r="5" fill="currentColor"/></svg>')


def masthead(pdf_href):
    return f'''<header class="mast">
{MARK}
<div class="mast-text">
<p class="eyebrow">جزوه درس مبانی اقتصاد · بخش اول</p>
<h1>اقتصاد خرد</h1>
<p class="sub">توضیح کامل اسلایدها از کمیابی و ده اصل اقتصاد تا عرضه و تقاضا، کشش، مازاد، زیان رفاهی و دخالت دولت؛ با همه مثال‌ها، تمرین‌های حل‌شده و پاسخ به چراها و چگونه‌ها.</p>
<p class="meta">بر پایه اسلایدهای درس دکتر علی ابراهیم‌نژاد (دانشگاه صنعتی شریف) · جزوه دانشجویی و غیررسمی · آبان ۱۴۰۵</p>
<div class="actions web-only">
<a class="btn primary" href="{pdf_href}" target="_blank" rel="noopener">نسخه PDF</a>
<button class="btn" type="button" id="toggle-sol">باز کردن همه پاسخ‌ها</button>
</div>
</div>
</header>'''


COVER = f'''<section class="cover print-only" aria-label="جلد">
<div class="cover-band"></div>
<div class="cover-in">
<p class="eyebrow">جزوه درس مبانی اقتصاد · بخش اول</p>
<h1>اقتصاد خرد</h1>
<p class="sub">از کمیابی تا زیان رفاهی<br>توضیح کامل اسلایدها، مثال‌ها، تمرین‌های حل‌شده و پاسخ به چراها و چگونه‌ها</p>
<svg class="cover-fig g" viewBox="0 0 400 230" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
<polygon class="cs" points="40,30 190,105 40,105"/><polygon class="ps" points="40,180 190,105 40,105"/>
<path class="ax" d="M40 10 V210 H390"/>
<path class="d" d="M40 30 L340 180"/><path class="s" d="M40 180 L340 30"/>
<circle class="dot" cx="190" cy="105" r="5"/>
<text class="tsm" x="95" y="88">مازاد مصرف‌کننده</text><text class="tsm" x="95" y="132">مازاد تولیدکننده</text>
<text class="td" x="346" y="186">D</text><text class="ts" x="346" y="34">S</text>
</svg>
<ol class="cover-list">
<li><b>فصل ۱</b>مقدمه: کمیابی، ده اصل اقتصاد، علیت و همبستگی</li>
<li><b>فصل ۲</b>عرضه و تقاضا</li>
<li><b>فصل ۳</b>کشش</li>
<li><b>فصل ۴</b>مازاد مصرف‌کننده و تولیدکننده، زیان رفاهی</li>
<li><b>فصل ۵</b>موانع کارایی: کنترل قیمت، مالیات، یارانه، پیامد خارجی</li>
<li><b>فصل ۶</b>فرمول‌نامه، مسائل جامع و واژه‌نامه</li>
</ol>
<div class="cover-meta">
<b>بر پایه اسلایدهای درس مبانی اقتصاد</b> · دکتر علی ابراهیم‌نژاد، دانشگاه صنعتی شریف<br>
جزوه دانشجویی و غیررسمی؛ توضیحات، مثال‌های عددی و تمرین‌ها برای یادگیری کامل افزوده شده‌اند.<br>
نسخه آنلاین: {REPO_URL} · آبان ۱۴۰۵
</div>
</div>
</section>'''

SCRIPT = '''<script>
(function(){
  var btn = document.getElementById('toggle-sol');
  if (!btn) return;
  btn.addEventListener('click', function(){
    var all = document.querySelectorAll('details.sol');
    var anyClosed = Array.prototype.some.call(all, function(d){ return !d.open; });
    all.forEach(function(d){ d.open = anyClosed; });
    btn.textContent = anyClosed ? 'بستن همه پاسخ‌ها' : 'باز کردن همه پاسخ‌ها';
  });
})();
</script>'''


def head_bits(extra_css=''):
    return (f'<title>{TITLE}</title>\n'
            '<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<meta name="description" content="جزوه کامل فارسی مبانی اقتصاد (اقتصاد خرد) با توضیحات، مثال‌ها و تمرین‌های حل‌شده">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="{FONTS}">\n'
            f'<style>{KATEX_CSS}\n{STYLE}\n{extra_css}</style>\n')


def web_body(content, entries, pdf_href):
    toc = toc_web(entries)
    return f'''<div class="book" dir="rtl" lang="fa">
{masthead(pdf_href)}
<div class="layout">
<nav class="toc" aria-label="فهرست مطالب"><h2>فهرست مطالب</h2>{toc}</nav>
<main>
<details class="toc-m"><summary>فهرست مطالب</summary>{toc}</details>
{content}
</main>
</div>
<footer class="foot">این جزوه بر پایه اسلایدهای درس نوشته شده و برای یادگیری، توضیحات و مثال‌های بیشتری به آن افزوده شده است. سند رسمی درس نیست؛ در صورت تفاوت، ملاک گفته‌های استاد در کلاس است.</footer>
</div>
{SCRIPT}'''


def print_body(content, entries, pages=None):
    return f'''<div class="book" dir="rtl" lang="fa">
{COVER}
<section class="ptoc print-only"><h2 id="toc-print" class="notoc">فهرست مطالب</h2>{toc_print(entries, pages)}</section>
<div class="layout"><main>
{content}
</main></div>
</div>'''


def full_doc(head, body, html_class=''):
    cls = f' class="{html_class}"' if html_class else ''
    return (f'<!doctype html>\n<html lang="fa" dir="rtl"{cls}>\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{head}</head>\n<body>\n{body}\n</body>\n</html>\n')


# ---------------------------------------------------------------- main
def build_content():
    src = '\n'.join((ROOT / 'chapters' / c).read_text(encoding='utf-8') for c in CHAPTERS
                    if (ROOT / 'chapters' / c).exists())
    if '$' in re.sub(r'\\\(.+?\\\)|\\\[.+?\\\]', '', src, flags=re.S):
        bad = [l for l in src.splitlines() if '$' in re.sub(r'\\\(.+?\\\)', '', l)]
        print('WARNING: stray $ in:', bad[:5])
    html, items = extract_math(src)
    html = persian_digits(html)
    html = put_figs(html)
    rendered = render_math(items)
    html = put_math(html, items, rendered)
    return html, len(items)


STYLE = (ROOT / 'style.css').read_text(encoding='utf-8')
KATEX_CSS = katex_css()


def write_outputs(content, entries, pages=None):
    pdf_rel = PDF_NAME
    pdf_gh = f'{REPO_URL}/blob/{BRANCH}/{PDF_NAME}'
    index = full_doc(head_bits(), web_body(content, entries, pdf_rel))
    (REPO / 'index.html').write_text(index, encoding='utf-8')
    artifact = head_bits() + web_body(content, entries, pdf_gh)
    (OUT / 'artifact.html').write_text(artifact, encoding='utf-8')
    pr = full_doc(head_bits(), print_body(content, entries, pages), 'print')
    (OUT / 'print.html').write_text(pr, encoding='utf-8')


def make_pdf(out_pdf):
    subprocess.run(['node', str(ROOT / 'make_pdf.js'), str(OUT / 'print.html'), str(out_pdf)], check=True, cwd=ROOT)


def outline_pages(pdf_path):
    from pypdf import PdfReader
    r = PdfReader(str(pdf_path))
    res = []

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                try:
                    res.append((it.title, r.get_destination_page_number(it) + 1))
                except Exception:
                    pass
    walk(r.outline)
    return res, len(r.pages)


def words(s):
    """Multiset of letter runs. Chromium stores RTL outline titles in visual word order,
    so titles are matched as bags of words instead of strings."""
    toks = re.findall(r'[A-Za-z\u0621-\u064A\u067E\u0686\u0698\u06A9\u06AF\u06CC\u0622]+', s)
    out = {}
    for t in toks:
        out[t] = out.get(t, 0) + 1
    return out


def contains(big, small):
    return bool(small) and all(big.get(k, 0) >= v for k, v in small.items())


def rewrite_outline(pdf_path, entries, pages):
    """Replace Chromium's outline with one that has correct (logical-order) Persian titles."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter(clone_from=reader)
    if '/Outlines' in writer._root_object:
        del writer._root_object[NameObject('/Outlines')]
    parent = None
    for lvl, hid, text in entries:
        if hid not in pages:
            continue
        if lvl == 1:
            parent = writer.add_outline_item(text, pages[hid] - 1)
        else:
            writer.add_outline_item(text, pages[hid] - 1, parent=parent)
    writer.add_metadata({'/Title': 'جزوه مبانی اقتصاد · اقتصاد خرد',
                         '/Author': 'جزوه دانشجویی بر پایه اسلایدهای دکتر علی ابراهیم‌نژاد'})
    writer.page_mode = '/UseOutlines'
    with open(pdf_path, 'wb') as f:
        writer.write(f)


def main():
    content, nmath = build_content()
    entries = toc_entries(content)
    write_outputs(content, entries)
    print(f'built HTML: {len(entries)} TOC entries, {nmath} formulas')
    if '--pdf' in sys.argv:
        tmp = OUT / 'pass1.pdf'
        make_pdf(tmp)
        outline, npages = outline_pages(tmp)
        pages = {}
        titles = [(words(t), p) for t, p in outline]
        pos = 0
        for lvl, hid, text in entries:
            key = words(text)
            for i in range(pos, len(titles)):
                t, p = titles[i]
                if contains(t, key):
                    pages[hid] = p
                    pos = i + 1
                    break
        missing = [text for lvl, hid, text in entries if hid not in pages]
        if missing:
            print('WARNING: no page found for', missing[:8])
        write_outputs(content, entries, pages)
        make_pdf(REPO / PDF_NAME)
        rewrite_outline(REPO / PDF_NAME, entries, pages)
        print(f'PDF: {npages} pages -> {REPO / PDF_NAME}')


if __name__ == '__main__':
    main()
