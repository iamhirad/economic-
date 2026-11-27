# -*- coding: utf-8 -*-
"""Build the problem-set answer pages.

Usage:  python3 build_ps.py ps01          ->  ../ps01/index.html and ../ps01/<pdf>
        python3 build_ps.py fasl5-masahat ->  the chapter-5 areas guide (source: src/guides/)
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
        'short': 'سری اول',
    },
    'ps02': {
        'title': 'پاسخ تمرین سری دوم',
        'eyebrow': 'درس مبانی اقتصاد · تمرین سری دوم',
        'sub': 'پاسخ تشریحی هر شش سؤال: کشش و درآمد کل، بازار بنزین و کالاهای مرتبط، تعادل و کشش نقطه‌ای، کشش کوتاه‌مدت و بلندمدت، اثبات کشش ثابت، و بازگشت بازار به تعادل.',
        'meta': 'استاد: دکتر علی ابراهیم‌نژاد · نیم‌سال اول ۱۴۰۵–۱۴۰۶ · پاسخ پیشنهادی (دانشجویی و غیررسمی)',
        'pdf': 'ps02-pasokh.pdf',
        'header': 'پاسخ تمرین سری دوم · مبانی اقتصاد',
        'short': 'سری دوم',
    },
    'ps03': {
        'title': 'پاسخ تمرین سری سوم',
        'eyebrow': 'درس مبانی اقتصاد · تمرین سری سوم',
        'sub': 'پاسخ تشریحی هر پنج سؤال: کف قیمت و کشش تقاضا، مالیات و منحنی لافر، یارانه اجاره در برابر افزایش عرضه مسکن، انتخاب تعرفه تلفن همراه، و بیمه درمان و کژمنشی.',
        'meta': 'استاد: دکتر علی ابراهیم‌نژاد · نیم‌سال اول ۱۴۰۵–۱۴۰۶ · پاسخ پیشنهادی (دانشجویی و غیررسمی)',
        'pdf': 'ps03-pasokh.pdf',
        'header': 'پاسخ تمرین سری سوم · مبانی اقتصاد',
        'short': 'سری سوم',
    },
    'fasl5-masahat': {
        'src': 'guides/fasl5-masahat.html',
        'title': 'مساحت‌ها در فصل ۵',
        'eyebrow': 'درس مبانی اقتصاد · راهنمای تکمیلی فصل ۵',
        'sub': 'مازاد مصرف‌کننده، مازاد تولیدکننده، سهم دولت و زیان رفاهی را در همه موانع کارایی فصل ۵ از روی نمودار پیدا کنید: سقف و کف قیمت، مالیات، یارانه، سهمیه، تعرفه و پیامد خارجی، به‌اضافه حالت‌های کاملاً بی‌کشش و کاملاً باکشش.',
        'meta': 'همه مثال‌ها روی بازار پایه فصل ۴ و ۵ جزوه · راهنمای دانشجویی و غیررسمی',
        'pdf': 'fasl5-masahat.pdf',
        'header': 'مساحت‌ها در فصل ۵ · مبانی اقتصاد',
        'btn': 'راهنمای مساحت‌های فصل ۵',
        'toc': 'فهرست',
        'foot': 'راهنمای دانشجویی، غیررسمی، بر پایه جزوه و اسلایدهای درس. در صورت تفاوت، ملاک گفته‌های استاد و دستیار آموزشی است.',
    },
}

FOOT = 'پاسخ پیشنهادی دانشجویی، غیررسمی. در صورت تفاوت با پاسخ رسمی درس، ملاک پاسخ دستیار آموزشی و استاد است.'


def btn_label(cfg):
    return cfg.get('btn', f'پاسخ تمرین {cfg.get("short", "")}')


def render(src):
    html, items = B.extract_math(src)
    html = B.persian_digits(html)
    html = B.put_figs(html)
    html = B.put_math(html, items, B.render_math(items))
    return html


def head(cfg, extra=''):
    h = B.head_bits(extra)
    return h.replace(f'<title>{B.TITLE}</title>', f'<title>{cfg["title"]}</title>', 1)


def web(cfg, content, entries, name):
    toc = B.toc_web(entries)
    others = ''.join(f'<a class="btn" href="../{k}/">{btn_label(v)}</a>' for k, v in SETS.items() if k != name)
    toc_title = cfg.get('toc', 'فهرست پاسخ‌ها')
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
{others}
</div>
</div>
</header>'''
    return f'''<div class="book" dir="rtl" lang="fa">
{mast}
<div class="layout">
<nav class="toc" aria-label="فهرست"><h2>{toc_title}</h2>{toc}</nav>
<main>
<details class="toc-m"><summary>{toc_title}</summary>{toc}</details>
{content}
</main>
</div>
<footer class="foot">{cfg.get('foot', FOOT)}</footer>
</div>'''


def main(name, pdf_too=True):
    cfg = SETS[name]
    src = (B.ROOT / cfg.get('src', f'ps/{name}.html')).read_text(encoding='utf-8')
    content = render(src)
    entries = B.toc_entries(content)
    outdir = B.REPO / name
    outdir.mkdir(exist_ok=True)
    wcss = '@media screen { #%s > .ch-head { display: none; } }' % name.replace('ps0', 'ps')
    (outdir / 'index.html').write_text(B.full_doc(head(cfg, wcss), web(cfg, content, entries, name)), encoding='utf-8')
    # same page without <html>/<head>/<body> and with absolute links, for claude.ai Artifacts
    site = 'https://iamhirad.github.io/economic-/'
    art = (head(cfg, wcss) + web(cfg, content, entries, name)).replace('href="../', f'href="{site}')
    art = art.replace(f'href="{cfg["pdf"]}"', f'href="{B.REPO_URL}/blob/{B.BRANCH}/{name}/{cfg["pdf"]}"')
    (B.OUT / f'{name}-artifact.html').write_text(art, encoding='utf-8')

    # print version: no cover, own running header
    pcss = ('@page { @top-left { content: "%s"; } }\n'
            '.ps-meta { color: var(--ink-2); font-size: 9.5pt; margin: 4px 0 0; }\n'
            '@media print { #%s { break-before: auto; } }' % (cfg['header'], name.replace('ps0', 'ps')))
    body = f'<div class="book" dir="rtl" lang="fa"><div class="layout"><main>{content}</main></div></div>'
    if not pdf_too:
        print(f'{name}: web page only ({len(entries)} headings)')
        return
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
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    for nm in (args or list(SETS)):
        main(nm, pdf_too='--no-pdf' not in sys.argv)
