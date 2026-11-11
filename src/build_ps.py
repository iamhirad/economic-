# -*- coding: utf-8 -*-
"""Build the problem-set answer pages.

Usage:  python3 build_ps.py ps01          ->  ../ps01/index.html and ../ps01/<pdf>
Reuses the booklet's style, KaTeX rendering, figures and Persian-digit pass (build.py).
"""
import re
import subprocess
import sys

import build as B

SETS = {
    'ps01': {
        'title': 'پاسخ تمرین سری اول',
        'eyebrow': 'درس مبانی اقتصاد · تمرین سری اول',
        'sub': 'پاسخ تشریحی هر پنج سؤال: گزاره‌های توصیفی و دستوری، ارزش‌ها در سیاست‌گذاری، دست نامرئی و شکست بازار، ده اصل منکیو، و مرز امکانات تولید.',
        'meta': 'استاد: دکتر علی ابراهیم‌نژاد · نیم‌سال اول ۱۴۰۵–۱۴۰۶ · پاسخ پیشنهادی (دانشجویی و غیررسمی)',
        'pdf': 'ps01-pasokh.pdf',
        'header': 'پاسخ تمرین سری اول · مبانی اقتصاد',
    },
}


def render(src):
    html, items = B.extract_math(src)
    html = B.persian_digits(html)
    html = B.put_figs(html)
    html = B.put_math(html, items, B.render_math(items))
    return html


def head(cfg, extra=''):
    h = B.head_bits(extra)
    return h.replace(f'<title>{B.TITLE}</title>', f'<title>{cfg["title"]}</title>', 1)


def web(cfg, content, entries):
    toc = B.toc_web(entries)
    mast = f'''<header class="mast">
{B.MARK}
<div class="mast-text">
<p class="eyebrow">{cfg['eyebrow']}</p>
<h1>{cfg['title']}</h1>
<p class="sub">{cfg['sub']}</p>
<p class="meta">{cfg['meta']}</p>
<div class="actions web-only">
<a class="btn primary" href="{cfg['pdf']}" target="_blank" rel="noopener">نسخه PDF</a>
<a class="btn" href="../">جزوه اقتصاد خرد</a>
</div>
</div>
</header>'''
    return f'''<div class="book" dir="rtl" lang="fa">
{mast}
<div class="layout">
<nav class="toc" aria-label="فهرست"><h2>فهرست پاسخ‌ها</h2>{toc}</nav>
<main>
<details class="toc-m"><summary>فهرست پاسخ‌ها</summary>{toc}</details>
{content}
</main>
</div>
<footer class="foot">پاسخ پیشنهادی دانشجویی، غیررسمی. در صورت تفاوت با پاسخ رسمی درس، ملاک پاسخ دستیار آموزشی و استاد است.</footer>
</div>'''


def main(name):
    cfg = SETS[name]
    src = (B.ROOT / 'ps' / f'{name}.html').read_text(encoding='utf-8')
    content = render(src)
    entries = B.toc_entries(content)
    outdir = B.REPO / name
    outdir.mkdir(exist_ok=True)
    wcss = '@media screen { #%s > .ch-head { display: none; } }' % name.replace('ps0', 'ps')
    (outdir / 'index.html').write_text(B.full_doc(head(cfg, wcss), web(cfg, content, entries)), encoding='utf-8')

    # print version: no cover, own running header
    pcss = ('@page { @top-left { content: "%s"; } }\n'
            '.ps-meta { color: var(--ink-2); font-size: 9.5pt; margin: 4px 0 0; }\n'
            '@media print { #%s { break-before: auto; } }' % (cfg['header'], name.replace('ps0', 'ps')))
    body = f'<div class="book" dir="rtl" lang="fa"><div class="layout"><main>{content}</main></div></div>'
    prn = B.OUT / f'{name}-print.html'
    prn.write_text(B.full_doc(head(cfg, pcss), body, 'print'), encoding='utf-8')
    pdf = outdir / cfg['pdf']
    subprocess.run(['node', str(B.ROOT / 'make_pdf.js'), str(prn), str(pdf)], check=True, cwd=B.ROOT)

    # replace Chromium's visual-order outline with correct Persian titles
    outline, npages = B.outline_pages(pdf)
    titles = [(B.words(t), p) for t, p in outline]
    pages, pos = {}, 0
    for lvl, hid, text in entries:
        key = B.words(text)
        for i in range(pos, len(titles)):
            if B.contains(titles[i][0], key):
                pages[hid] = titles[i][1]
                pos = i + 1
                break
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
    w = PdfWriter(clone_from=PdfReader(str(pdf)))
    if '/Outlines' in w._root_object:
        del w._root_object[NameObject('/Outlines')]
    parent = None
    for lvl, hid, text in entries:
        if hid in pages:
            if lvl == 1:
                parent = w.add_outline_item(text, pages[hid] - 1)
            else:
                w.add_outline_item(text, pages[hid] - 1, parent=parent)
    w.add_metadata({'/Title': cfg['title'] + ' · مبانی اقتصاد'})
    w.page_mode = '/UseOutlines'
    with open(pdf, 'wb') as f:
        w.write(f)
    print(f'{name}: {len(entries)} headings, PDF {npages} pages -> {pdf}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'ps01')
