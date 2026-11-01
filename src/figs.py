# -*- coding: utf-8 -*-
"""SVG figures for the booklet.

Every chart is drawn from the same equations that the worked examples use,
so the numbers on the figures always match the text.
Colors come from CSS classes (see style.css), so figures follow light/dark themes.
"""
import math
import re

FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def fa(x):
    """Format a number with Persian digits (thousands separator ٬, decimal ٫)."""
    if isinstance(x, str):
        s = x
    else:
        if abs(x - round(x)) < 1e-9:
            s = f"{int(round(x)):,}"
        else:
            s = f"{x:,.2f}".rstrip('0').rstrip('.')
    s = s.replace(',', '٬').replace('.', '٫')
    return s.translate(FA_DIGITS)


def mi(sym, sub=None, sup=None):
    """Math-italic label for SVG text (e.g. P with subscript 0)."""
    out = f'<tspan class="mi">{sym}</tspan>'
    if sub is not None:
        out += f'<tspan class="msub" dy="4">{sub}</tspan><tspan dy="-4"> </tspan>'
    if sup is not None:
        out += f'<tspan class="msub" dy="-7">{sup}</tspan><tspan dy="7"> </tspan>'
    return out


def _has_fa_letters(s):
    plain = re.sub(r'<[^>]+>', '', s)
    return any('\u0600' <= ch <= '\u06FF' and not ('\u06F0' <= ch <= '\u06F9') for ch in plain)


def svg_text(x, y, s, cls='', anchor='middle', extra=''):
    """Emit an SVG <text>. Anchors are given in LTR terms (start = text grows to the right).
    The page is RTL, so Persian labels flip the anchor; labels without Persian letters
    (math, numbers) are forced to LTR so formulas read left-to-right."""
    if _has_fa_letters(s):
        anchor = {'start': 'end', 'end': 'start'}.get(anchor, anchor)
        d = ''
    else:
        d = ' direction="ltr"'
    c = f' class="{cls}"' if cls else ''
    return f'<text{c} x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{d}{extra}>{s}</text>'


class Graph:
    def __init__(self, xmax, ymax, w=500, h=350, xmin=0, ymin=0,
                 ml=58, mr=30, mt=30, mb=46,
                 xlabel='مقدار', ylabel='قیمت', title=''):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.w, self.h, self.ml, self.mr, self.mt, self.mb = w, h, ml, mr, mt, mb
        self.xlabel, self.ylabel, self.title = xlabel, ylabel, title
        self.back = []   # fills (drawn first)
        self.mid = []    # guides
        self.front = []  # curves, labels
        self.top = []    # dots and texts on top

    # coordinate transforms
    def X(self, x):
        return self.ml + (x - self.xmin) / (self.xmax - self.xmin) * (self.w - self.ml - self.mr)

    def Y(self, y):
        return self.h - self.mb - (y - self.ymin) / (self.ymax - self.ymin) * (self.h - self.mt - self.mb)

    def pt(self, x, y):
        return f"{self.X(x):.1f},{self.Y(y):.1f}"

    # primitives
    def poly(self, pts, cls):
        p = ' '.join(self.pt(x, y) for x, y in pts)
        self.back.append(f'<polygon class="{cls}" points="{p}"/>')

    def rect(self, x1, y1, x2, y2, cls):
        self.poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], cls)

    def path(self, pts, cls, layer='front'):
        p = ' '.join(self.pt(x, y) for x, y in pts)
        getattr(self, layer).append(f'<polyline class="{cls}" points="{p}"/>')

    def line(self, x1, y1, x2, y2, cls='k', layer='front'):
        self.path([(x1, y1), (x2, y2)], cls, layer)

    def fn(self, f, x0, x1, cls, n=60):
        pts = [(x0 + (x1 - x0) * i / n, f(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]
        self.path(pts, cls)

    def guide(self, x, y, to_x=True, to_y=True):
        if to_y:
            self.line(self.xmin, y, x, y, 'gd', 'mid')
        if to_x:
            self.line(x, self.ymin, x, y, 'gd', 'mid')

    def text(self, x, y, s, cls='', anchor='middle', dx=0, dy=0):
        self.top.append(svg_text(self.X(x) + dx, self.Y(y) + dy, s, cls, anchor))

    def ptext(self, px, py, s, cls='', anchor='middle'):
        self.top.append(svg_text(px, py, s, cls, anchor))

    def tickx(self, x, s, cls='tl', dy=0):
        X0, Y0 = self.X(x), self.Y(self.ymin)
        self.front.append(f'<line class="ax" x1="{X0:.1f}" y1="{Y0:.1f}" x2="{X0:.1f}" y2="{Y0 + 5:.1f}"/>')
        self.top.append(svg_text(X0, Y0 + 19 + dy, s, cls, 'middle'))

    def ticky(self, y, s, cls='tl'):
        X0, Y0 = self.X(self.xmin), self.Y(y)
        self.front.append(f'<line class="ax" x1="{X0 - 5:.1f}" y1="{Y0:.1f}" x2="{X0:.1f}" y2="{Y0:.1f}"/>')
        self.top.append(svg_text(X0 - 9, Y0 + 4.5, s, cls, 'end'))

    def dot(self, x, y, cls='dot'):
        self.top.append(f'<circle class="{cls}" cx="{self.X(x):.1f}" cy="{self.Y(y):.1f}" r="4"/>')

    def arrow(self, x1, y1, x2, y2, cls='arr', pixel=False, head=8):
        if pixel:
            X1, Y1, X2, Y2 = x1, y1, x2, y2
        else:
            X1, Y1, X2, Y2 = self.X(x1), self.Y(y1), self.X(x2), self.Y(y2)
        ang = math.atan2(Y2 - Y1, X2 - X1)
        bx, by = X2 - head * math.cos(ang), Y2 - head * math.sin(ang)
        lx, ly = bx + head * 0.5 * math.sin(ang), by - head * 0.5 * math.cos(ang)
        rx, ry = bx - head * 0.5 * math.sin(ang), by + head * 0.5 * math.cos(ang)
        self.top.append(f'<line class="{cls}" x1="{X1:.1f}" y1="{Y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}"/>')
        self.top.append(f'<polygon class="{cls}h" points="{X2:.1f},{Y2:.1f} {lx:.1f},{ly:.1f} {rx:.1f},{ry:.1f}"/>')

    def bracket(self, x1, x2, y, s, cls='br', dy=16):
        """Horizontal double arrow with a label under it (pixel offset dy)."""
        X1, X2, Y0 = self.X(x1), self.X(x2), self.Y(y) + dy
        self.arrow((X1 + X2) / 2, Y0, X1 + 1, Y0, cls, pixel=True, head=7)
        self.arrow((X1 + X2) / 2, Y0, X2 - 1, Y0, cls, pixel=True, head=7)
        self.ptext((X1 + X2) / 2, Y0 + 16, s, 'tsm')

    def axes(self):
        X0, Y0 = self.X(self.xmin), self.Y(self.ymin)
        XE, YE = self.w - self.mr + 14, self.mt - 14
        out = [
            f'<line class="ax" x1="{X0:.1f}" y1="{Y0:.1f}" x2="{XE:.1f}" y2="{Y0:.1f}"/>',
            f'<polygon class="axh" points="{XE + 7:.1f},{Y0:.1f} {XE - 2:.1f},{Y0 - 4.5:.1f} {XE - 2:.1f},{Y0 + 4.5:.1f}"/>',
            f'<line class="ax" x1="{X0:.1f}" y1="{Y0:.1f}" x2="{X0:.1f}" y2="{YE:.1f}"/>',
            f'<polygon class="axh" points="{X0:.1f},{YE - 7:.1f} {X0 - 4.5:.1f},{YE + 2:.1f} {X0 + 4.5:.1f},{YE + 2:.1f}"/>',
        ]
        if self.ylabel:
            out.append(svg_text(X0 + 10, YE + 4, self.ylabel, 'axl', 'start'))
        if self.xlabel:
            out.append(svg_text(XE + 4, Y0 + 36, self.xlabel, 'axl', 'end'))
        return out

    def svg(self, label=''):
        body = self.back + self.mid + self.axes() + self.front + self.top
        aria = label or self.title
        return (f'<svg class="g" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{aria}" '
                f'xmlns="http://www.w3.org/2000/svg">' + ''.join(body) + '</svg>')


def panels(*items):
    """items: (svg, subcaption) pairs placed side by side."""
    cells = ''.join(f'<div class="panel">{s}<div class="pcap">{c}</div></div>' for s, c in items)
    return f'<div class="panels">{cells}</div>'


# ----------------------------------------------------------------------------
# Chapter 1
# ----------------------------------------------------------------------------

def fig_ppf():
    g = Graph(110, 110, xlabel='کامپیوتر (هزار دستگاه)', ylabel='گندم (هزار تن)')
    f = lambda x: 100 * math.sqrt(max(0.0, 1 - (x / 100) ** 2))
    g.poly([(0, 0)] + [(x, f(x)) for x in range(0, 101, 2)] + [(100, 0)], 'acc')
    g.fn(f, 0, 100, 'k', 120)
    for name, x, y, cls in [('A', 40, 45, 'dot'), ('B', 60, f(60), 'dot'), ('C', 80, f(80), 'dot'), ('D', 85, 85, 'dotx')]:
        g.dot(x, y, cls)
        g.text(x, y, mi(name), '', 'start', 8, -6)
    g.guide(60, f(60))
    g.guide(80, f(80))
    g.ticky(f(60), fa(80))
    g.ticky(f(80), fa(60))
    g.tickx(60, fa(60))
    g.tickx(80, fa(80))
    g.ptext(g.X(30), g.Y(25), 'قابل تولید ولی ناکارا', 'tsm')
    g.text(85, 85, 'دست‌نیافتنی', 'tsm', 'middle', 0, 22)
    g.text(70, 95, 'مرز امکانات تولید', 'tk', 'start', 0, 0)
    return g.svg('مرز امکانات تولید')


def fig_circular():
    w, h = 680, 460
    parts = [f'<svg class="g" viewBox="0 0 {w} {h}" role="img" aria-label="نمودار جریان دوری" xmlns="http://www.w3.org/2000/svg">']

    def box(cx, cy, bw, bh, t1, t2, cls='bx'):
        parts.append(f'<rect class="{cls}" x="{cx - bw/2}" y="{cy - bh/2}" width="{bw}" height="{bh}" rx="10"/>')
        parts.append(svg_text(cx, cy - 4 if t2 else cy + 5, t1, 'bxt', 'middle'))
        if t2:
            parts.append(svg_text(cx, cy + 18, t2, 'tsm', 'middle'))

    def curve(p0, c, p1, cls, label, lcls):
        parts.append(f'<path class="{cls}" d="M{p0[0]} {p0[1]} Q{c[0]} {c[1]} {p1[0]} {p1[1]}"/>')
        ang = math.atan2(p1[1] - c[1], p1[0] - c[0])
        hd = 10
        bx, by = p1[0] - hd * math.cos(ang), p1[1] - hd * math.sin(ang)
        lx, ly = bx + hd * .5 * math.sin(ang), by - hd * .5 * math.cos(ang)
        rx, ry = bx - hd * .5 * math.sin(ang), by + hd * .5 * math.cos(ang)
        parts.append(f'<polygon class="{cls}h" points="{p1[0]},{p1[1]} {lx:.1f},{ly:.1f} {rx:.1f},{ry:.1f}"/>')
        mx = .25 * p0[0] + .5 * c[0] + .25 * p1[0]
        my = .25 * p0[1] + .5 * c[1] + .25 * p1[1]
        parts.append(svg_text(mx, my + 5, label, lcls + ' halo', 'middle'))

    # money (outer, solid) and real flows (inner, dashed)
    curve((220, 35), (45, 35), (45, 195), 'mflow', 'درآمد فروش', 'tm')
    curve((130, 195), (130, 75), (220, 75), 'rflow', 'کالا و خدمات فروخته‌شده', 'tr')
    curve((635, 195), (635, 35), (460, 35), 'mflow', 'مخارج خرید', 'tm')
    curve((460, 75), (550, 75), (550, 195), 'rflow', 'کالا و خدمات خریده‌شده', 'tr')
    curve((460, 425), (635, 425), (635, 265), 'mflow', 'درآمد خانوار', 'tm')
    curve((550, 265), (550, 385), (460, 385), 'rflow', 'کار، زمین، سرمایه', 'tr')
    curve((45, 265), (45, 425), (220, 425), 'mflow', 'دستمزد، اجاره، سود', 'tm')
    curve((220, 385), (130, 385), (130, 265), 'rflow', 'نهاده‌های تولید', 'tr')
    box(340, 55, 240, 66, 'بازار کالاها و خدمات', 'بنگاه‌ها می‌فروشند، خانوارها می‌خرند', 'bx2')
    box(340, 405, 240, 66, 'بازار عوامل تولید', 'خانوارها می‌فروشند، بنگاه‌ها می‌خرند', 'bx2')
    box(95, 230, 150, 70, 'بنگاه‌ها', 'تولید و فروش کالا')
    box(585, 230, 150, 70, 'خانوارها', 'مالک عوامل تولید')
    parts.append(svg_text(340, 214, 'حلقه بیرونی (پیوسته): جریان پول', 'tm', 'middle'))
    parts.append(svg_text(340, 240, 'حلقه درونی (خط‌چین): جریان کالا و عوامل', 'tr', 'middle'))
    parts.append('</svg>')
    return ''.join(parts)


# ----------------------------------------------------------------------------
# Chapter 2
# ----------------------------------------------------------------------------

def fig_demand_basic():
    g = Graph(10, 10, xlabel='مقدار تقاضا', ylabel='قیمت')
    f = lambda q: 9 - 0.9 * q
    g.fn(f, 0, 10, 'd')
    g.guide(3, f(3))
    g.ticky(f(3), mi('P', '0'))
    g.tickx(3, mi('Q', '0'))
    g.dot(3, f(3))
    g.text(9.4, f(9.4), mi('D'), 'td', 'start', 6, -8)
    return g.svg('منحنی تقاضا')


def fig_demand_move():
    g = Graph(10, 10, xlabel='مقدار تقاضا', ylabel='قیمت')
    f = lambda q: 9 - 0.9 * q
    g.fn(f, 0, 10, 'd')
    for q, s in [(3, '0'), (5.5, '1')]:
        g.guide(q, f(q))
        g.ticky(f(q), mi('P', s))
        g.tickx(q, mi('Q', s))
        g.dot(q, f(q))
    g.text(3, f(3), mi('A'), '', 'start', 8, -6)
    g.text(5.5, f(5.5), mi('B'), '', 'start', 8, -6)
    g.arrow(3.4, f(3.4) + 0.35, 5.1, f(5.1) + 0.35, 'arr')
    g.arrow(-0.55, f(3) - 0.2, -0.55, f(5.5) + 0.2, 'arr')
    g.arrow(3.2, -1.15, 5.3, -1.15, 'arr')
    g.text(9.4, f(9.4), mi('D'), 'td', 'start', 6, -8)
    return g.svg('حرکت روی منحنی تقاضا')


def fig_demand_slide17():
    g1 = Graph(50, 30, w=400, h=320, xlabel='مقدار', ylabel='قیمت')
    f = lambda q: 27.2 - 0.48 * q
    g1.fn(f, 5, 50, 'd')
    for q in (15, 40):
        g1.guide(q, f(q)); g1.dot(q, f(q))
        g1.tickx(q, fa(q)); g1.ticky(f(q), fa(f(q)))
    g1.arrow(17, f(17) + 1.4, 37, f(37) + 1.4, 'arr')
    g1.text(48, f(48), mi('D'), 'td', 'start', 4, -10)
    g2 = Graph(80, 30, w=400, h=320, xlabel='مقدار', ylabel='قیمت')
    d1 = lambda q: 25 - 0.5 * q
    d2 = lambda q: 35 - 0.5 * q
    g2.fn(d1, 2, 48, 'k2d'); g2.fn(d2, 12, 68, 'd')
    for q, f_ in [(30, d1), (50, d2)]:
        g2.guide(q, 10); g2.dot(q, 10); g2.tickx(q, fa(q))
    g2.ticky(10, fa(10))
    g2.arrow(26, 22, 40, 22, 'arr')
    g2.text(48, d1(48), mi('D', '1'), 'td', 'start', 4, 4)
    g2.text(68, d2(68), mi('D', '2'), 'td', 'start', 4, 4)
    return panels((g1.svg('حرکت روی منحنی'), 'الف) تغییر قیمت از ۲۰ به ۸: حرکت روی همان منحنی'),
                  (g2.svg('جابه‌جایی منحنی'), 'ب) تغییر عوامل دیگر: کل منحنی جابه‌جا می‌شود'))


def fig_gold():
    g = Graph(1800, 3500, w=560, h=360, ml=64, xlabel='قیمت طلا (دلار بر اونس)', ylabel='تقاضا (تن)')
    for x in (400, 800, 1200, 1600):
        g.tickx(x, fa(x))
    for y in (500, 1500, 2500, 3500):
        g.ticky(y, fa(y))
    g.line(280, 2750, 1570, 1800, 'k')
    g.line(280, 300, 1570, 1650, 'd')
    g.line(280, 400, 1570, 460, 's')
    g.text(1150, 2110, 'تقاضای جواهرات', 'tk', 'start', 0, -12)
    g.text(1560, 1650, 'تقاضای سرمایه‌گذاری', 'td', 'end', 10, 22)
    g.text(1560, 460, 'تقاضای صنعتی و فناوری', 'ts', 'end', 0, -12)
    return g.svg('تقاضای طلا')


def fig_supply_basic():
    g = Graph(10, 10, xlabel='مقدار عرضه', ylabel='قیمت')
    f = lambda q: 1.5 + 0.75 * q
    g.fn(f, 0.5, 10, 's')
    g.guide(5, f(5)); g.dot(5, f(5))
    g.ticky(f(5), mi('P', 'A')); g.tickx(5, mi('Q', 'A'))
    g.text(10, f(10), mi('S'), 'ts', 'start', 4, 4)
    return g.svg('منحنی عرضه')


def fig_cotton():
    g = Graph(7.2, 1.9, w=580, h=360, ml=58, xlabel='پنبه (میلیارد کیلوگرم در سال)', ylabel='قیمت (دلار بر کیلوگرم)', ymin=0.5)
    steps = [('پاکستان', 0, 1.68, 0.71), ('آرژانتین', 1.68, 1.86, 1.08), ('استرالیا', 1.86, 2.11, 1.15),
             ('برزیل', 2.11, 2.77, 1.27), ('نیکاراگوئه، ترکیه', 2.77, 2.95, 1.43),
             ('آمریکا', 2.95, 6.79, 1.56), ('ایران', 6.79, 6.95, 1.71)]
    pts = []
    for _, a, b, p in steps:
        pts += [(a, p), (b, p)]
    g.path(pts, 's')
    for name, a, b, p in steps:
        anchor, dx = 'middle', 0
        x = (a + b) / 2
        if name == 'ایران':
            anchor, x, dx = 'end', b, 0
        dy = -8
        if name in ('آرژانتین', 'استرالیا', 'نیکاراگوئه، ترکیه'):
            anchor, x, dx = 'end', a, -4
        if name == 'آرژانتین':
            dy = 16
        g.text(x, p, name, 'tsm', anchor, dx, dy)
        g.ticky(p, fa(p))
    for x in range(1, 8):
        g.tickx(x, fa(x))
    g.line(0, 1.20, 7.0, 1.20, 'pl', 'mid')
    g.text(7.0, 1.20, 'قیمت ۱٫۲۰', 'tsm', 'end', 0, -6)
    return g.svg('منحنی عرضه جهانی پنبه')


def fig_supply_move():
    g = Graph(10, 10, xlabel='مقدار عرضه', ylabel='قیمت')
    f = lambda q: 1 + 0.9 * q
    g.fn(f, 0.5, 9.5, 's')
    for q, s in [(7, '0'), (4.5, '1')]:
        g.guide(q, f(q)); g.dot(q, f(q))
        g.ticky(f(q), mi('P', s)); g.tickx(q, mi('Q', s))
    g.arrow(6.6, f(6.6) + 0.5, 4.9, f(4.9) + 0.5, 'arr')
    g.text(9.5, f(9.5), mi('S'), 'ts', 'start', 4, 4)
    return g.svg('حرکت روی منحنی عرضه')


def fig_supply_shift():
    g = Graph(10, 10, xlabel='مقدار عرضه', ylabel='قیمت')
    g.fn(lambda q: 1 + 0.9 * q, 1, 9.5, 's')
    g.fn(lambda q: 1 + 0.9 * (q - 2), 3, 10, 'k2s')
    g.fn(lambda q: 1 + 0.9 * (q + 2), 0, 7.5, 'k2s')
    g.text(9.5, 1 + 0.9 * 9.5, mi('S'), 'ts', 'start', 4, 4)
    g.text(7.5, 1 + 0.9 * 9.5, 'کاهش عرضه', 'tsm', 'end', -6, -4)
    g.text(8.5, 1 + 0.9 * 6.5, 'افزایش عرضه', 'tsm', 'start', 12, 4)
    g.arrow(5, 1 + 0.9 * 5, 3.3, 1 + 0.9 * 5, 'arr')
    g.arrow(5, 1 + 0.9 * 5 - 0.4, 6.7, 1 + 0.9 * 5 - 0.4, 'arr')
    return g.svg('جابه‌جایی منحنی عرضه')


def fig_equilibrium():
    # Qd = 100 - 2P, Qs = -20 + 4P  ->  P = 50 - Q/2, P = 5 + Q/4
    g = Graph(110, 50, w=540, h=360, xlabel='مقدار', ylabel='قیمت')
    g.fn(lambda q: 50 - q / 2, 0, 100, 'd')
    g.fn(lambda q: 5 + q / 4, 0, 110, 's')
    g.guide(60, 20); g.dot(60, 20)
    g.text(60, 20, mi('E'), '', 'start', 8, 16)
    g.ticky(20, fa(20)); g.tickx(60, fa(60))
    g.line(0, 25, 80, 25, 'pl', 'mid'); g.ticky(25, fa(25))
    g.line(0, 15, 70, 15, 'pl', 'mid'); g.ticky(15, fa(15))
    g.dot(50, 25, 'dots'); g.dot(80, 25, 'dots'); g.dot(40, 15, 'dots'); g.dot(70, 15, 'dots')
    g.text(65, 25, 'مازاد عرضه = ۳۰', 'tsm', 'middle', 0, -8)
    g.text(55, 15, 'کمبود = ۳۰', 'tsm', 'middle', 0, 18)
    g.text(100, 0, mi('D'), 'td', 'start', 6, -8)
    g.text(110, 5 + 110 / 4, mi('S'), 'ts', 'start', 4, 4)
    return g.svg('تعادل بازار')


def fig_shifts():
    def base(title):
        g = Graph(10, 10, w=380, h=300, xlabel='مقدار', ylabel='قیمت')
        return g
    g1 = base('')
    g1.fn(lambda q: 9 - 0.8 * q, 0.5, 10, 'k2d')
    g1.fn(lambda q: 11 - 0.8 * q, 2, 10, 'd')
    g1.fn(lambda q: 1 + 0.8 * q, 0.5, 10, 's')
    e0 = (5, 5); e1 = (6.25, 6)
    for (q, p), s in [(e0, '0'), (e1, '1')]:
        g1.guide(q, p); g1.dot(q, p); g1.ticky(p, mi('P', s)); g1.tickx(q, mi('Q', s))
    g1.arrow(7.2, 3.6, 8.6, 3.6, 'arr')
    g1.text(10, 9 - 8, mi('D'), 'td', 'start', 4, 4)
    g1.text(10, 11 - 8, mi('D′'), 'td', 'start', 4, 4)
    g1.text(10, 9, mi('S'), 'ts', 'start', 4, 4)
    g2 = base('')
    g2.fn(lambda q: 9 - 0.8 * q, 0.5, 10, 'd')
    g2.fn(lambda q: 1 + 0.8 * q, 0.5, 10, 'k2s')
    g2.fn(lambda q: -1 + 0.8 * q, 1.5, 10, 's')
    e0 = (5, 5); e1 = (6.25, 4)
    for (q, p), s in [(e0, '0'), (e1, '1')]:
        g2.guide(q, p); g2.dot(q, p); g2.ticky(p, mi('P', s)); g2.tickx(q, mi('Q', s))
    g2.arrow(3.2, 3.8, 4.6, 3.8, 'arr')
    g2.text(10, 1, mi('D'), 'td', 'start', 4, 4)
    g2.text(10, 9, mi('S'), 'ts', 'start', 4, 4)
    g2.text(10, 7, mi('S′'), 'ts', 'start', 4, 4)
    return panels((g1.svg('افزایش تقاضا'), 'الف) افزایش تقاضا: قیمت و مقدار هر دو بالا می‌روند'),
                  (g2.svg('افزایش عرضه'), 'ب) افزایش عرضه: قیمت پایین و مقدار بالا می‌رود'))


# ----------------------------------------------------------------------------
# Chapter 3
# ----------------------------------------------------------------------------

def fig_elast_extremes():
    g1 = Graph(10, 10, w=360, h=290, xlabel='مقدار', ylabel='قیمت')
    g1.line(5, 0, 5, 9.5, 'd')
    g1.text(5, 8.5, mi('D'), 'td', 'start', 8, 0)
    g1.text(5, 5, '<tspan class="mi">E</tspan> = 0', 'tk', 'start', 10, 0)
    g2 = Graph(10, 10, w=360, h=290, xlabel='مقدار', ylabel='قیمت')
    g2.line(0, 5, 9.5, 5, 'd')
    g2.text(9, 5, mi('D'), 'td', 'middle', 0, -10)
    g2.text(5, 5, '<tspan class="mi">E</tspan> = ∞', 'tk', 'middle', 0, -12)
    return panels((g1.svg('تقاضای کاملاً بی‌کشش'), 'الف) تقاضای کاملاً بی‌کشش (عمودی)'),
                  (g2.svg('تقاضای کاملاً باکشش'), 'ب) تقاضای کاملاً باکشش (افقی)'))


def fig_elast_linear():
    # Q = 90 - 10P  ->  P = 9 - Q/10
    g = Graph(95, 10, w=560, h=380, xlabel='مقدار تقاضا', ylabel='قیمت')
    f = lambda q: 9 - q / 10
    g.fn(f, 0, 90, 'd')
    for q in range(10, 90, 10):
        g.guide(q, f(q))
    for p in range(1, 9):
        g.ticky(p, fa(p))
    for q in range(10, 90, 10):
        g.tickx(q, fa(q))
    for (q1, q2, e) in [(20, 30, '−2.6'), (40, 50, '−1'), (70, 80, '−0.2')]:
        qm = (q1 + q2) / 2
        g.dot(qm, f(qm), 'dots')
        g.text(qm, f(qm), f'<tspan class="mi">E</tspan> = {e}', 'tk', 'start', 12, -8)
    g.text(58, 8.6, 'نیمه بالایی خط: باکشش', 'tsm', 'start')
    g.text(58, 8.0, 'نقطه وسط خط: کشش واحد', 'tsm', 'start')
    g.text(58, 7.4, 'نیمه پایینی خط: کم‌کشش', 'tsm', 'start')
    g.text(90, 0, mi('D'), 'td', 'start', 4, -8)
    return g.svg('کشش در طول منحنی تقاضای خطی')


def fig_tr_curve():
    g = Graph(9.5, 230, w=540, h=340, ml=60, xlabel='قیمت', ylabel='درآمد کل')
    tr = lambda p: p * (90 - 10 * p)
    g.poly([(0, 0)] + [(p / 10, tr(p / 10)) for p in range(0, 46)] + [(4.5, 0)], 'acc')
    g.fn(tr, 0, 9, 'k', 90)
    g.guide(4.5, 202.5); g.dot(4.5, 202.5)
    g.tickx(4.5, fa(4.5)); g.ticky(202.5, fa(202.5))
    for p in (1, 2, 3, 6, 7, 8, 9):
        g.tickx(p, fa(p))
    g.text(2.55, 95, 'ناحیه کم‌کشش', 'tk')
    g.text(2.55, 75, 'افزایش قیمت، درآمد را زیاد می‌کند', 'tsm')
    g.text(6.5, 95, 'ناحیه باکشش', 'tk')
    g.text(6.5, 75, 'افزایش قیمت، درآمد را کم می‌کند', 'tsm')
    return g.svg('درآمد کل بر حسب قیمت')


def fig_wheat():
    g = Graph(130, 4, w=540, h=360, xlabel='مقدار گندم', ylabel='قیمت گندم')
    d = lambda q: 13 - 0.1 * q
    s1 = lambda q: 3 + 0.08 * (q - 100)
    s2 = lambda q: 2 + 0.08 * (q - 110)
    g.rect(0, 0, 100, 2, 'acc')
    g.rect(0, 2, 100, 3, 'dwl')
    g.rect(100, 0, 110, 2, 'rev')
    g.fn(d, 95, 125, 'd')
    g.fn(s1, 85, 115, 's')
    g.fn(s2, 95, 125, 's')
    g.guide(100, 3); g.guide(110, 2)
    g.dot(100, 3); g.dot(110, 2)
    g.ticky(3, fa(3)); g.ticky(2, fa(2))
    g.tickx(100, fa(100)); g.tickx(110, fa(110))
    g.text(50, 2.5, 'از دست رفته: ۱۰۰', 'tsm')
    g.text(50, 1.0, 'مشترک: ۲۰۰', 'tsm')
    g.text(105, 0.55, '+۲۰', 'tsm')
    g.text(125, d(125), mi('D'), 'td', 'start', 4, 0)
    g.text(115, s1(115), mi('S', '1'), 'ts', 'start', 4, 0)
    g.text(125, s2(125), mi('S', '2'), 'ts', 'start', 4, 0)
    return g.svg('اثر بهبود بهره‌وری بر درآمد کشاورزان')


def fig_drugs():
    D = lambda q: 400 - 4 * q
    Dn = lambda q: 320 - 4 * q
    S = lambda q: q + 25
    Sn = lambda q: q + 45

    def panel(new_q, new_p, supply_side):
        g = Graph(100, 420, w=380, h=320, xlabel='مقدار', ylabel='قیمت')
        g.rect(0, 0, new_q, new_p, 'cs')
        g.path([(0, 100), (75, 100), (75, 0)], 'gdk', 'mid')
        g.fn(D, 25, 98, 'k2d' if not supply_side else 'd')
        g.fn(S, 0, 100, 's' if not supply_side else 'k2s')
        if supply_side:
            g.fn(Sn, 0, 100, 's')
            g.text(100, Sn(100), mi('S′'), 'ts', 'end', 0, -6)
            g.text(100, S(100), mi('S'), 'ts', 'start', 2, 4)
            g.text(25, D(25), mi('D'), 'td', 'start', 6, 4)
        else:
            g.fn(Dn, 5, 78, 'd')
            g.text(98, D(98), mi('D'), 'td', 'start', 2, -4)
            g.text(78, Dn(78), mi('D′'), 'td', 'start', 2, -4)
            g.text(100, S(100), mi('S'), 'ts', 'end', 0, -6)
        g.dot(75, 100, 'dots'); g.dot(new_q, new_p)
        g.ticky(100, fa(100)); g.ticky(new_p, fa(new_p))
        g.tickx(75, fa(75)) if abs(new_q - 75) > 6 else None
        g.tickx(new_q, fa(new_q))
        g.text(new_q / 2, 14, f'گردش پول = {fa(new_q * new_p)}', 'tsm')
        return g
    g1 = panel(71, 116, True)
    g2 = panel(59, 84, False)
    return panels((g1.svg('سیاست طرف عرضه'), 'الف) سیاست طرف عرضه: گردش پول از ۷٬۵۰۰ به ۸٬۲۳۶ می‌رسد'),
                  (g2.svg('سیاست طرف تقاضا'), 'ب) سیاست طرف تقاضا: گردش پول از ۷٬۵۰۰ به ۴٬۹۵۶ می‌رسد'))


# ----------------------------------------------------------------------------
# Chapter 4 (base example: P = 800 - 0.1Q, P = 200 + 0.1Q)
# ----------------------------------------------------------------------------
D0 = lambda q: 800 - 0.1 * q
S0 = lambda q: 200 + 0.1 * q


def base_graph(w=520, h=360):
    g = Graph(6500, 900, w=w, h=h, ml=58, xlabel='مقدار', ylabel='قیمت (دلار)')
    return g


def draw_base(g, d=True, s=True, label=True):
    if d:
        g.fn(D0, 0, 6000, 'd')
        if label:
            g.text(6000, D0(6000), 'تقاضا (MB)', 'td', 'start', 4, 16)
    if s:
        g.fn(S0, 0, 6000, 's')
        if label:
            g.text(6000, S0(6000), 'عرضه (MC)', 'ts', 'end', -6, 0)


def fig_step_demand():
    g = Graph(5, 120, w=520, h=340, xlabel='تعداد بلیت', ylabel='قیمت (هزار تومان)')
    wtp = [100, 80, 70, 50]
    for i, v in enumerate(wtp):
        if v > 60:
            g.rect(i, 60, i + 1, v, 'cs')
    pts = []
    for i, v in enumerate(wtp):
        pts += [(i, v), (i + 1, v)]
    pts += [(4, 0)]
    g.path(pts, 'd')
    g.line(0, 60, 4.7, 60, 'pl', 'mid')
    names = ['علی', 'سارا', 'رضا', 'مریم']
    for i, (v, n) in enumerate(zip(wtp, names)):
        g.text(i + 0.5, v, f'{n} ({fa(v)})', 'tsm', 'middle', 0, -7)
        g.tickx(i + 1, fa(i + 1))
        g.ticky(v, fa(v))
    g.ticky(60, fa(60))
    g.text(4.7, 60, 'قیمت = ۶۰', 'tsm', 'end', 0, -6)
    g.text(1.5, 64, 'مازاد مصرف‌کننده = ۷۰', 'tsm', 'start', 0, 0)
    return g.svg('منحنی تقاضای پله‌ای')


def fig_cs_linear():
    g = base_graph()
    g.poly([(0, 800), (3000, 500), (0, 500)], 'cs')
    draw_base(g)
    g.guide(3000, 500); g.dot(3000, 500)
    g.ticky(500, fa(500)); g.ticky(800, fa(800)); g.tickx(3000, fa(3000))
    g.text(900, 590, 'مازاد مصرف‌کننده', 'tsm', 'middle')
    g.text(900, 548, '۴۵۰٬۰۰۰', 'tsm', 'middle')
    return g.svg('مازاد مصرف‌کننده')


def fig_ps_linear():
    g = base_graph()
    g.poly([(0, 200), (3000, 500), (0, 500)], 'ps')
    draw_base(g)
    g.guide(3000, 500); g.dot(3000, 500)
    g.ticky(500, fa(500)); g.ticky(200, fa(200)); g.tickx(3000, fa(3000))
    g.text(900, 430, 'مازاد تولیدکننده', 'tsm', 'middle')
    g.text(900, 388, '۴۵۰٬۰۰۰', 'tsm', 'middle')
    return g.svg('مازاد تولیدکننده')


def fig_cs_change():
    g = base_graph()
    g.poly([(0, 800), (3000, 500), (0, 500)], 'cs')
    g.rect(0, 400, 3000, 500, 'ps')
    g.poly([(3000, 500), (4000, 400), (3000, 400)], 'rev')
    g.fn(D0, 0, 6000, 'd')
    g.text(6000, D0(6000), 'تقاضا', 'td', 'start', 4, 16)
    g.guide(3000, 500); g.guide(4000, 400)
    g.ticky(500, mi('P', '0') ); g.ticky(400, mi('P', '1'))
    g.tickx(3000, fa(3000)); g.tickx(4000, fa(4000))
    g.text(900, 570, 'CS اولیه', 'tsm')
    g.text(1500, 440, 'افزوده برای خریداران قبلی: ۳۰۰٬۰۰۰', 'tsm')
    g.text(3350, 330, 'خریداران جدید: ۵۰٬۰۰۰', 'tsm', 'start')
    g.arrow(3550, 360, 3300, 420, 'arr2', head=6)
    return g.svg('تغییر مازاد مصرف‌کننده')


def fig_ps_change():
    g = base_graph()
    g.poly([(0, 200), (3000, 500), (0, 500)], 'ps')
    g.rect(0, 500, 3000, 600, 'cs')
    g.poly([(3000, 500), (4000, 600), (3000, 600)], 'rev')
    g.fn(S0, 0, 6000, 's')
    g.text(6000, S0(6000), 'عرضه', 'ts', 'end', -6, 0)
    g.guide(3000, 500); g.guide(4000, 600)
    g.ticky(500, mi('P', '0')); g.ticky(600, mi('P', '1'))
    g.tickx(3000, fa(3000)); g.tickx(4000, fa(4000))
    g.text(900, 410, 'PS اولیه', 'tsm')
    g.text(1500, 540, 'افزوده برای تولیدکنندگان قبلی: ۳۰۰٬۰۰۰', 'tsm')
    g.text(4100, 700, 'تولیدکنندگان جدید: ۵۰٬۰۰۰', 'tsm', 'start')
    g.arrow(4300, 680, 3450, 585, 'arr2', head=6)
    return g.svg('تغییر مازاد تولیدکننده')


def _stick(parts, x, vals, width=46, scale=None, labels=True, title=''):
    wts, cost, price, wtp = vals
    Y = scale
    segs = [(wts, cost, 'st-sup'), (cost, price, 'st-firm'), (price, wtp, 'st-cust')]
    for a, b, cls in segs:
        parts.append(f'<rect class="{cls}" x="{x - width/2}" y="{Y(b):.1f}" width="{width}" height="{Y(a) - Y(b):.1f}"/>')
    for v in vals:
        parts.append(f'<line class="ax" x1="{x - width/2 - 6}" y1="{Y(v):.1f}" x2="{x + width/2}" y2="{Y(v):.1f}"/>')
    if title:
        parts.append(f'<text class="tk" x="{x}" y="{Y(1500) + 2:.1f}" text-anchor="middle">{title}</text>')


def fig_value_stick():
    w, h = 560, 330
    Y = lambda v: 300 - (v - 400) / (1300 - 400) * 260
    parts = [f'<svg class="g" viewBox="0 0 {w} {h}" role="img" aria-label="چوب ارزش" xmlns="http://www.w3.org/2000/svg">']
    vals = (500, 700, 1000, 1200)
    _stick(parts, 280, vals, width=70, scale=Y)
    names = [('تمایل به فروش (WTS)', 500), ('هزینه (Cost)', 700), ('قیمت (Price)', 1000), ('تمایل به پرداخت (WTP)', 1200)]
    for t, v in names:
        parts.append(svg_text(232, Y(v) + 5, f'{t} = {fa(v)}', 'tk', 'end'))
    segs = [('رضایت مشتری = ۲۰۰', 1000, 1200), ('حاشیه سود بنگاه = ۳۰۰', 700, 1000), ('مازاد تأمین‌کننده = ۲۰۰', 500, 700)]
    for t, a, b in segs:
        ym = (Y(a) + Y(b)) / 2
        parts.append(f'<path class="ax" fill="none" d="M326 {Y(b)+2:.1f} q8 0 8 8 v{(Y(a)-Y(b))/2-12:.1f} l6 4 l-6 4 v{(Y(a)-Y(b))/2-12:.1f} q0 8 -8 8"/>')
        parts.append(svg_text(348, ym + 5, t, 'tk', 'start'))
    parts.append('</svg>')
    return ''.join(parts)


def fig_value_stick4():
    w, h = 640, 360
    Y = lambda v: 320 - (v - 300) / (1500 - 300) * 270
    parts = [f'<svg class="g" viewBox="0 0 {w} {h}" role="img" aria-label="چهار سناریوی چوب ارزش" xmlns="http://www.w3.org/2000/svg">']
    cases = [('وضع فعلی', (500, 700, 1000, 1200)), ('افزایش قیمت', (500, 700, 1100, 1200)),
             ('افزایش ارزش', (500, 700, 1000, 1400)), ('کاهش هزینه', (500, 600, 1000, 1200)),
             ('کارایی نهاده', (400, 700, 1000, 1200))]
    for i, (t, vals) in enumerate(cases):
        x = 595 - i * 118
        _stick(parts, x, vals, width=44, scale=Y, title=t)
        for v in vals:
            parts.append(svg_text(x + 27, Y(v) + 4, fa(v), 'tl', 'start'))
    lg = [('st-cust', 'رضایت مشتری (WTP − قیمت)'), ('st-firm', 'حاشیه بنگاه (قیمت − هزینه)'), ('st-sup', 'مازاد تأمین‌کننده (هزینه − WTS)')]
    for i, (c, t) in enumerate(lg):
        x = 610 - i * 205
        parts.append(f'<rect class="{c}" x="{x - 12}" y="338" width="12" height="12"/>')
        parts.append(svg_text(x - 18, 348, t, 'tsm', 'end'))
    parts.append('</svg>')
    return ''.join(parts)


def fig_dwl_under_over():
    def panel(q):
        g = base_graph(w=400, h=330)
        g.poly([(q, D0(q)), (3000, 500), (q, S0(q))], 'dwl')
        draw_base(g, label=False)
        g.text(6000, D0(6000), 'MB', 'td', 'start', 4, 12)
        g.text(6000, S0(6000), 'MC', 'ts', 'start', 4, 4)
        g.guide(3000, 500, to_y=True); g.guide(q, D0(q)); g.guide(q, S0(q), to_x=False)
        g.dot(3000, 500)
        g.ticky(500, fa(500)); g.ticky(D0(q), fa(D0(q))); g.ticky(S0(q), fa(S0(q)))
        g.tickx(q, fa(q)); g.tickx(3000 + (0 if q > 3000 else 0), '')
        g.text(3000, 0, fa(3000), 'tl', 'middle', 0, 19) if False else None
        return g
    g1 = panel(2500); g1.tickx(3000, fa(3000), dy=14)
    g2 = panel(3500); g2.tickx(3000, fa(3000), dy=14)
    return panels((g1.svg('زیان رفاهی کم‌تولیدی'), 'الف) کم‌تولیدی (۲٬۵۰۰ واحد): زیان رفاهی = ۲۵٬۰۰۰'),
                  (g2.svg('زیان رفاهی بیش‌تولیدی'), 'ب) بیش‌تولیدی (۳٬۵۰۰ واحد): زیان رفاهی = ۲۵٬۰۰۰'))


# ----------------------------------------------------------------------------
# Chapter 5
# ----------------------------------------------------------------------------

def fig_ceiling():
    g = base_graph(w=560, h=380)
    g.poly([(0, 800), (2000, 600), (2000, 400), (0, 400)], 'cs')
    g.poly([(0, 200), (2000, 400), (0, 400)], 'ps')
    g.poly([(2000, 600), (3000, 500), (2000, 400)], 'dwl')
    draw_base(g)
    g.line(0, 400, 5600, 400, 'cap', 'front')
    g.text(5600, 400, 'سقف قیمت = ۴۰۰', 'tsm', 'end', 0, -8)
    g.guide(2000, 600); g.guide(4000, 400)
    g.ticky(600, fa(600) + ' (Pws)'); g.ticky(400, fa(400)); g.ticky(500, fa(500))
    g.tickx(2000, fa(2000)); g.tickx(4000, fa(4000)); g.tickx(3000, fa(3000))
    g.bracket(2000, 4000, 400, 'کمبود = ۲٬۰۰۰', dy=26)
    g.text(700, 520, 'CS', 'tk'); g.text(600, 345, 'PS', 'tk'); g.text(2300, 500, 'DWL', 'tk')
    return g.svg('سقف قیمت')


def fig_floor():
    g = base_graph(w=560, h=380)
    g.poly([(0, 800), (2000, 600), (0, 600)], 'cs')
    g.poly([(0, 600), (2000, 600), (2000, 400), (0, 200)], 'ps')
    g.poly([(2000, 600), (3000, 500), (2000, 400)], 'dwl')
    draw_base(g)
    g.line(0, 600, 5600, 600, 'cap', 'front')
    g.text(5600, 600, 'کف قیمت = ۶۰۰', 'tsm', 'end', 0, -8)
    g.guide(2000, 600); g.guide(4000, 600); g.guide(2000, 400, to_x=False)
    g.ticky(600, fa(600)); g.ticky(400, fa(400)); g.ticky(500, fa(500))
    g.tickx(2000, fa(2000)); g.tickx(4000, fa(4000)); g.tickx(3000, fa(3000))
    g.bracket(2000, 4000, 600, 'مازاد عرضه = ۲٬۰۰۰', dy=-48)
    g.text(600, 650, 'CS', 'tk'); g.text(800, 470, 'PS', 'tk'); g.text(2300, 500, 'DWL', 'tk')
    return g.svg('کف قیمت')


def fig_tax(on='seller'):
    g = base_graph(w=560, h=460)
    g.rect(0, 500, 2500, 550, 'rev')
    g.rect(0, 450, 2500, 500, 'rev2')
    g.poly([(2500, 550), (3000, 500), (2500, 450)], 'dwl')
    draw_base(g, label=False)
    if on == 'seller':
        g.fn(lambda q: 300 + 0.1 * q, 0, 5000, 's')
        g.text(5000, 800, 'عرضه پس از مالیات', 'ts', 'end', -8, -4)
        g.text(6000, S0(6000), 'عرضه', 'ts', 'start', 4, 4)
        g.text(6000, D0(6000), 'تقاضا', 'td', 'start', 4, 16)
        g.arrow(4500, 650, 4500, 742, 'arr')
        g.text(4500, 700, 't = ۱۰۰', 'tsm', 'start', 8, 0)
    else:
        g.fn(lambda q: 700 - 0.1 * q, 0, 6000, 'd')
        g.text(6000, 100, 'تقاضا پس از مالیات', 'td', 'end', 0, 18)
        g.text(6000, D0(6000), 'تقاضا', 'td', 'start', 4, 4)
        g.text(6000, S0(6000), 'عرضه', 'ts', 'start', 4, 4)
        g.arrow(4500, 350, 4500, 258, 'arr')
        g.text(4500, 300, 't = ۱۰۰', 'tsm', 'start', 8, 0)
    g.guide(2500, 550); g.guide(3000, 500)
    g.line(0, 450, 2500, 450, 'gd', 'mid')
    for v in (550, 500, 450):
        g.ticky(v, fa(v))
    g.tickx(2500, fa(2500)); g.tickx(3000, fa(3000), dy=14)
    g.dot(2500, 550); g.dot(2500, 450); g.dot(3000, 500, 'dots')
    g.text(1250, 525, 'سهم خریداران', 'tl', 'middle', 0, 4)
    g.text(1250, 475, 'سهم فروشندگان', 'tl', 'middle', 0, 4)
    g.text(2650, 500, 'DWL', 'tsm', 'middle', 0, 4)
    return g.svg('مالیات بر ' + ('فروشنده' if on == 'seller' else 'خریدار'))


def _incidence_panel(dfun, sfun, d_rng, s_rng, q, pb, ps, shift='supply'):
    g = Graph(5500, 1000, w=380, h=330, ml=56, xlabel='مقدار', ylabel='قیمت')
    g.rect(0, 500, q, pb, 'rev')
    g.rect(0, ps, q, 500, 'rev2')
    g.poly([(q, pb), (3000, 500), (q, ps)], 'dwl')
    g.fn(dfun, *d_rng, 'd')
    g.fn(sfun, *s_rng, 's')
    if shift == 'supply':
        g.fn(lambda x: sfun(x) + 100, s_rng[0], s_rng[1] - 300, 'k2s')
    else:
        g.fn(lambda x: dfun(x) - 100, d_rng[0], d_rng[1], 'k2d')
    g.guide(q, pb); g.line(0, ps, q, ps, 'gd', 'mid'); g.line(0, 500, 3000, 500, 'gd', 'mid')
    g.ticky(pb, fa(round(pb, 1))); g.ticky(ps, fa(round(ps, 1)))
    g.ticky(500, fa(500)) if pb - 500 > 35 and 500 - ps > 35 else None
    g.tickx(q, fa(round(q))); g.dot(q, pb); g.dot(q, ps)
    g.text(d_rng[1], dfun(d_rng[1]), mi('D'), 'td', 'start', 4, 4)
    g.text(s_rng[1], sfun(s_rng[1]), mi('S'), 'ts', 'start', 4, 4)
    return g


def fig_incidence_d():
    s = lambda q: 200 + 0.1 * q
    de = lambda q: 600 - q / 30
    di = lambda q: 1400 - 0.3 * q
    g1 = _incidence_panel(de, s, (0, 5400), (0, 5400), 2250, 525, 425)
    g2 = _incidence_panel(di, s, (1500, 4500), (0, 5400), 2750, 575, 475)
    return panels((g1.svg('تقاضای باکشش'), 'الف) تقاضای باکشش: خریدار ۲۵ و فروشنده ۷۵ از مالیات ۱۰۰ را می‌پردازد'),
                  (g2.svg('تقاضای کم‌کشش'), 'ب) تقاضای کم‌کشش: خریدار ۷۵ و فروشنده ۲۵ را می‌پردازد'))


def fig_incidence_s():
    d = lambda q: 800 - 0.1 * q
    se = lambda q: 400 + q / 30
    si = lambda q: -1000 + 0.5 * q
    g1 = _incidence_panel(d, se, (0, 5400), (0, 5400), 2250, 575, 475, shift='demand')
    g2 = _incidence_panel(d, si, (0, 5400), (2000, 3900), 2833.33, 516.67, 416.67, shift='demand')
    return panels((g1.svg('عرضه باکشش'), 'الف) عرضه باکشش: خریدار ۷۵ و فروشنده ۲۵ را می‌پردازد'),
                  (g2.svg('عرضه کم‌کشش'), 'ب) عرضه کم‌کشش: خریدار حدود ۱۷ و فروشنده حدود ۸۳ را می‌پردازد'))


def fig_tax_sizes():
    out = []
    for t, cap in [(100, 'الف) مالیات کوچک (۱۰۰)'), (300, 'ب) مالیات متوسط (۳۰۰)'), (500, 'ج) مالیات بزرگ (۵۰۰)')]:
        q = 3000 - 5 * t
        pb, ps = D0(q), S0(q)
        g = Graph(6500, 900, w=330, h=300, ml=50, mr=20, xlabel='مقدار', ylabel='قیمت')
        g.rect(0, ps, q, pb, 'rev')
        g.poly([(q, pb), (3000, 500), (q, ps)], 'dwl')
        g.fn(D0, 0, 6000, 'd'); g.fn(S0, 0, 6000, 's')
        g.guide(q, pb); g.line(0, ps, q, ps, 'gd', 'mid')
        g.ticky(pb, fa(pb)); g.ticky(ps, fa(ps)); g.tickx(q, fa(q))
        g.tickx(3000, fa(3000), dy=14 if t < 200 else 0)
        rev, dwl = t * q, 2.5 * t * t
        out.append((g.svg(cap), f'{cap}<br>درآمد مالیاتی {fa(rev)} · زیان رفاهی {fa(dwl)}'))
    return panels(*out)


def fig_laffer():
    g1 = Graph(650, 1000, w=380, h=300, ml=56, xlabel='نرخ مالیات (t)', ylabel='زیان رفاهی (هزار)')
    g1.fn(lambda t: 2.5 * t * t / 1000, 0, 600, 'dwlc')
    g2 = Graph(650, 500, w=380, h=300, ml=56, xlabel='نرخ مالیات (t)', ylabel='درآمد مالیاتی (هزار)')
    g2.fn(lambda t: (3000 * t - 5 * t * t) / 1000, 0, 600, 'revc')
    for g in (g1, g2):
        for t in (100, 300, 500):
            g.tickx(t, fa(t))
    for v in (250, 500, 750, 1000):
        g1.ticky(v, fa(v))
    for v in (100, 250, 400, 450):
        g2.ticky(v, fa(v))
    g2.guide(300, 450); g2.dot(300, 450)
    g2.guide(100, 250); g2.guide(500, 250)
    g2.text(200, 40, 'محدوده عادی', 'tsm'); g2.text(400, 40, 'محدوده بازدارنده', 'tsm')
    return panels((g1.svg('زیان رفاهی و نرخ مالیات'), 'الف) زیان رفاهی با مربع نرخ مالیات زیاد می‌شود'),
                  (g2.svg('منحنی لافر'), 'ب) منحنی لافر: درآمد اول زیاد و بعد کم می‌شود'))


def fig_subsidy():
    g = Graph(185, 110, w=560, h=380, xlabel='مقدار (میلیون تن)', ylabel='قیمت (دلار بر تن)')
    D = lambda q: 90 - 0.5 * q
    S = lambda q: 30 + 0.5 * q
    Ss = lambda q: 0.5 * q
    g.rect(0, 45, 90, 75, 'rev')
    g.poly([(60, 60), (90, 75), (90, 45)], 'dwl')
    g.fn(D, 0, 170, 'd'); g.fn(S, 0, 150, 's'); g.fn(Ss, 20, 160, 's')
    g.text(170, D(170), mi('D'), 'td', 'start', 4, 4)
    g.text(150, S(150), 'عرضه', 'ts', 'start', 4, 4)
    g.text(160, Ss(160), 'عرضه با یارانه', 'ts', 'start', 4, 4)
    g.guide(60, 60); g.guide(90, 75); g.guide(90, 45, to_x=False)
    for v in (45, 60, 75, 90):
        g.ticky(v, fa(v))
    for v in (30, 60, 90, 120, 150, 180):
        g.tickx(v, fa(v))
    g.dot(60, 60, 'dots'); g.dot(90, 75); g.dot(90, 45)
    g.arrow(120, 88, 120, 62, 'arr')
    g.text(120, 75, 'یارانه ۳۰', 'tsm', 'end', -8, 4)
    g.text(22, 50, 'هزینه دولت = ۲٬۷۰۰', 'tsm')
    g.text(81, 60, 'DWL', 'tsm', 'middle', 0, 4)
    return g.svg('یارانه به تولیدکننده')


def fig_quota():
    g = Graph(185, 110, w=560, h=380, xlabel='مقدار (میلیون تن)', ylabel='قیمت (دلار بر تن)')
    D = lambda q: 135 - q
    S = lambda q: 0.5 * q
    g.rect(0, 45, 60, 75, 'ps')
    g.poly([(60, 75), (90, 45), (60, 45)], 'dwl')
    g.poly([(60, 45), (90, 45), (60, 30)], 'dwl2')
    g.fn(D, 30, 125, 'd'); g.fn(S, 0, 180, 's')
    g.line(60, 0, 60, 105, 'cap', 'front')
    g.text(60, 105, 'سهمیه = ۶۰', 'tsm', 'start', 6, 0)
    g.text(125, D(125), mi('D'), 'td', 'start', 4, 4)
    g.text(180, S(180), mi('S'), 'ts', 'start', 4, 4)
    g.guide(60, 75); g.guide(60, 30, to_x=False); g.guide(90, 45)
    for v in (30, 45, 75):
        g.ticky(v, fa(v))
    for v in (30, 60, 90, 120, 150, 180):
        g.tickx(v, fa(v))
    g.dot(60, 75); g.dot(60, 30); g.dot(90, 45, 'dots')
    g.text(30, 62, 'سود اضافه تولیدکننده = ۱٬۸۰۰', 'tsm')
    g.text(150, 68, 'زیان رفاهی = ۶۷۵', 'tsm')
    g.arrow(130, 66, 72, 55, 'arr2', head=6)
    return g.svg('سهمیه تولید')


def fig_ext(kind='neg'):
    g = base_graph(w=560, h=380)
    if kind == 'neg':
        g.poly([(2500, 550), (3000, 600), (3000, 500)], 'dwl')
        g.fn(D0, 0, 6000, 'd'); g.fn(S0, 0, 6000, 's')
        g.fn(lambda q: 300 + 0.1 * q, 0, 5000, 'k')
        g.text(6000, D0(6000), 'MB = تقاضا', 'td', 'start', 4, 16)
        g.text(5200, 720, 'MPC (هزینه خصوصی)', 'ts', 'start', 10, 16)
        g.text(4200, 720, 'MSC (هزینه اجتماعی)', 'tk', 'end', -10, 0)
        g.guide(2500, 550); g.guide(3000, 600, to_x=False); g.guide(3000, 500)
        g.ticky(550, fa(550)); g.ticky(500, fa(500)); g.ticky(600, fa(600))
        g.tickx(2500, fa(2500)); g.tickx(3000, fa(3000), dy=14)
        g.dot(2500, 550); g.dot(3000, 500, 'dots')
        g.text(2500, 550, 'بهینه', 'tsm', 'end', -6, -8); g.text(3000, 500, 'بازار', 'tsm', 'start', 8, 16)
    else:
        g.poly([(3000, 600), (3500, 550), (3000, 500)], 'dwl')
        g.fn(D0, 0, 6000, 'd'); g.fn(S0, 0, 6000, 's')
        g.fn(lambda q: 900 - 0.1 * q, 1000, 6000, 'k')
        g.text(6000, D0(6000), 'MPB (منفعت خصوصی)', 'td', 'end', 0, 22)
        g.text(6000, 300, 'MSB (منفعت اجتماعی)', 'tk', 'start', 4, -2)
        g.text(6000, S0(6000), 'MC', 'ts', 'start', 4, 4)
        g.guide(3500, 550); g.guide(3000, 600, to_x=False); g.guide(3000, 500)
        g.ticky(550, fa(550)); g.ticky(500, fa(500)); g.ticky(600, fa(600))
        g.tickx(3000, fa(3000)); g.tickx(3500, fa(3500), dy=14)
        g.dot(3500, 550); g.dot(3000, 500, 'dots')
        g.text(3500, 550, 'بهینه', 'tsm', 'start', 8, -6); g.text(3000, 500, 'بازار', 'tsm', 'end', -6, 16)
    return g.svg('پیامد خارجی ' + ('منفی' if kind == 'neg' else 'مثبت'))


FIGS = {
    'ppf': fig_ppf,
    'circular': fig_circular,
    'demand_basic': fig_demand_basic,
    'demand_move': fig_demand_move,
    'demand_slide17': fig_demand_slide17,
    'gold': fig_gold,
    'supply_basic': fig_supply_basic,
    'cotton': fig_cotton,
    'supply_move': fig_supply_move,
    'supply_shift': fig_supply_shift,
    'equilibrium': fig_equilibrium,
    'shifts': fig_shifts,
    'elast_extremes': fig_elast_extremes,
    'elast_linear': fig_elast_linear,
    'tr_curve': fig_tr_curve,
    'wheat': fig_wheat,
    'drugs': fig_drugs,
    'step_demand': fig_step_demand,
    'cs_linear': fig_cs_linear,
    'ps_linear': fig_ps_linear,
    'cs_change': fig_cs_change,
    'ps_change': fig_ps_change,
    'value_stick': fig_value_stick,
    'value_stick4': fig_value_stick4,
    'dwl_under_over': fig_dwl_under_over,
    'ceiling': fig_ceiling,
    'floor': fig_floor,
    'tax_seller': lambda: fig_tax('seller'),
    'tax_buyer': lambda: fig_tax('buyer'),
    'incidence_d': fig_incidence_d,
    'incidence_s': fig_incidence_s,
    'tax_sizes': fig_tax_sizes,
    'laffer': fig_laffer,
    'subsidy': fig_subsidy,
    'quota': fig_quota,
    'ext_neg': lambda: fig_ext('neg'),
    'ext_pos': lambda: fig_ext('pos'),
}
