# Writes build/figs.html with every figure, and screenshots it (for checking charts quickly).
import pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figs import FIGS
import build
names = sys.argv[1:] or list(FIGS)
cells = ''.join(f'<div style="border:1px solid #ccc;padding:6px"><div style="font:12px monospace">{n}</div><figure>{FIGS[n]()}</figure></div>' for n in names)
html = build.full_doc(build.head_bits(), f'<div class="book" dir="rtl" lang="fa"><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:8px">{cells}</div></div>')
out = build.OUT / 'figs.html'
out.write_text(html, encoding='utf-8')
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1500,height:900}},deviceScaleFactor:1}});await p.goto('file://{out}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);await p.screenshot({{path:'{build.OUT}/figs.png',fullPage:true}});await b.close();}})();"""
subprocess.run(['node', '-e', js], check=True, cwd=build.ROOT)
print(build.OUT / 'figs.png')
