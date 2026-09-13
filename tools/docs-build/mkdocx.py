"""Build a Word document from the styled artifact HTML, preserving structure."""
import re, os, sys, html as H
import h2md
from h2md import Tree, Node, BLOCK, VOID, raw_text, has_block

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

INK   = RGBColor(0x18, 0x1B, 0x19)
INK2  = RGBColor(0x47, 0x4C, 0x48)
MUTED = RGBColor(0x75, 0x7B, 0x74)
ACC   = RGBColor(0xA4, 0x60, 0x1A)
GO    = RGBColor(0x2E, 0x6B, 0x4C)
STOP  = RGBColor(0x8C, 0x3B, 0x34)

SERIF = 'Source Serif 4'
SANS  = 'Archivo'
MONO  = 'JetBrains Mono'

def shade(el, hexcolor):
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto')
    sh.set(qn('w:fill'), hexcolor)
    el.get_or_add_pPr().append(sh)

def left_border(p, hexcolor='A4601A', size=18):
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr')
    lf = OxmlElement('w:left')
    lf.set(qn('w:val'), 'single'); lf.set(qn('w:sz'), str(size))
    lf.set(qn('w:space'), '8'); lf.set(qn('w:color'), hexcolor)
    bd.append(lf); pPr.append(bd)

def bottom_rule(p, hexcolor='D7DAD3'):
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr')
    bt = OxmlElement('w:bottom')
    bt.set(qn('w:val'), 'single'); bt.set(qn('w:sz'), '6')
    bt.set(qn('w:space'), '4'); bt.set(qn('w:color'), hexcolor)
    bd.append(bt); pPr.append(bd)

def keep_next(p):
    pPr = p._p.get_or_add_pPr()
    k = OxmlElement('w:keepNext'); k.set(qn('w:val'), '1'); pPr.append(k)

# ---------------------------------------------------------------- inline runs
def add_runs(p, node, base=None):
    """Walk inline content, emitting formatted runs."""
    base = base or {}
    def emit(text, fmt):
        if not text: return
        r = p.add_run(text)
        r.font.name = fmt.get('font', SERIF)
        if fmt.get('size'): r.font.size = Pt(fmt['size'])
        r.bold = bool(fmt.get('bold')); r.italic = bool(fmt.get('italic'))
        if fmt.get('color'): r.font.color.rgb = fmt['color']
        if fmt.get('caps'):
            r.font.all_caps = True
            r.font.size = Pt(fmt.get('size', 8))
        # ensure east-asian font too
        rPr = r._element.get_or_add_rPr()
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
        for a in ('w:ascii','w:hAnsi','w:cs'):
            rf.set(qn(a), r.font.name)

    def walk(n, fmt):
        for k in n.kids:
            t = k.tag
            if t == '#text':
                txt = re.sub(r'\s+', ' ', k.text)
                if txt: emit(txt, fmt)
            elif t == 'br':
                p.add_run().add_break()
            elif t in ('strong', 'b'):
                walk(k, {**fmt, 'bold': True})
            elif t in ('em', 'i'):
                walk(k, {**fmt, 'italic': True})
            elif t == 'code':
                emit(raw_text(k), {**fmt, 'font': MONO,
                                   'size': (fmt.get('size', 10.5) - 1.5)})
            elif t == 'a':
                walk(k, {**fmt, 'color': ACC})
            elif t == 'span':
                c = k.cls()
                if 'lbl' in c or 'k' in c:
                    walk(k, {**fmt, 'bold': True, 'font': MONO, 'caps': True,
                             'size': 8, 'color': ACC})
                    emit('  ', fmt)
                elif 'eyebrow' in c or 'tag' in c or 'pill' in c:
                    walk(k, {**fmt, 'font': MONO, 'caps': True, 'size': 8,
                             'color': ACC})
                elif 'score' in c or 'num' in c or 'n' in c:
                    walk(k, {**fmt, 'bold': True, 'font': MONO, 'color': ACC})
                    emit(' ', fmt)
                elif 'v' in c:
                    walk(k, {**fmt, 'bold': True})
                else:
                    walk(k, fmt)
            else:
                walk(k, fmt)
    walk(node, {'font': SERIF, 'size': 10.5, **base})

def has_text(node):
    return bool(re.sub(r'\s+', '', raw_text(node)))

# ------------------------------------------------------------------ blocks
def add_code(doc, text):
    text = H.unescape(re.sub(r'<[^>]+>', '', text)).strip('\n')
    if not text.strip(): return
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(6); pf.space_after = Pt(8)
    pf.left_indent = Inches(0.14)
    pf.line_spacing = 1.0
    shade(p._p, 'F1F2EF')
    left_border(p, 'D7DAD3', 12)
    for i, line in enumerate(text.split('\n')):
        if i: p.add_run().add_break()
        r = p.add_run(line)
        r.font.name = MONO; r.font.size = Pt(8.5)
        rPr = r._element.get_or_add_rPr()
        rf = OxmlElement('w:rFonts')
        for a in ('w:ascii','w:hAnsi','w:cs'): rf.set(qn(a), MONO)
        rPr.insert(0, rf)

def add_table(doc, node):
    rows = []
    def walk(x):
        if x.tag == 'tr': rows.append(x)
        else:
            for k in x.kids: walk(k)
    walk(node)
    grid = []
    for r in rows:
        cells = []
        def cw(x):
            for k in x.kids:
                if k.tag in ('th', 'td'): cells.append(k)
                else: cw(k)
        cw(r)
        if cells: grid.append(cells)
    if not grid: return
    ncol = max(len(r) for r in grid)
    t = doc.add_table(rows=0, cols=ncol)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for ri, cells in enumerate(grid):
        row = t.add_row()
        header = ri == 0 and any(c.tag == 'th' for c in cells)
        for ci in range(ncol):
            cell = row.cells[ci]
            cell.paragraphs[0].text = ''
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if ci < len(cells):
                add_runs(p, cells[ci],
                         {'size': 9, 'bold': header,
                          'font': SANS if header else SERIF})
            if header:
                tcPr = cell._tc.get_or_add_tcPr()
                sh = OxmlElement('w:shd')
                sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto')
                sh.set(qn('w:fill'), 'E9EBE6')
                tcPr.append(sh)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_list(doc, node, ordered, depth=0):
    style = 'List Number' if ordered else 'List Bullet'
    for li in [k for k in node.kids if k.tag == 'li']:
        lead = Node('span'); lead.kids = []
        for k in li.kids:
            if k.tag in BLOCK: break
            lead.kids.append(k)
        if has_text(lead):
            try: p = doc.add_paragraph(style=style)
            except KeyError: p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.left_indent = Inches(0.25 + 0.25 * depth)
            add_runs(p, lead)
        for k in li.kids:
            if k.tag in ('ul', 'ol'):
                add_list(doc, k, k.tag == 'ol', depth + 1)
            elif k.tag in BLOCK:
                render(doc, k, depth)

CALLOUT = {'flag', 'callout', 'note', 'worry', 'fix', 'verdict', 'done'}

def add_callout(doc, node):
    if not has_text(node): return
    c = set(node.cls())
    color = 'A4601A'
    if 'go' in c or 'done' in c: color = '2E6B4C'
    if 'stop' in c or 'worry' in c: color = '8C3B34'
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Inches(0.16); pf.space_before = Pt(6); pf.space_after = Pt(8)
    left_border(p, color, 18)
    shade(p._p, 'F7F7F5')
    add_runs(p, node)

def render(doc, node, depth=0):
    for k in node.kids:
        t = k.tag
        if t in ('h1','h2','h3','h4','h5','h6'):
            if not has_text(k): continue
            lvl = int(t[1])
            if lvl == 1:
                continue  # part title supplied by the builder
            p = doc.add_heading(level=min(lvl, 4))
            for r in list(p.runs): r._element.getparent().remove(r._element)
            sizes = {2: 16, 3: 12.5, 4: 11}
            add_runs(p, k, {'font': SANS, 'size': sizes.get(lvl, 11),
                            'bold': True, 'color': INK})
            p.paragraph_format.space_before = Pt(14 if lvl == 2 else 10)
            p.paragraph_format.space_after = Pt(4)
            keep_next(p)
            if lvl == 2: bottom_rule(p)
        elif t == 'pre':
            add_code(doc, raw_text(k))
        elif t == 'table':
            add_table(doc, k)
        elif t in ('ul', 'ol'):
            add_list(doc, k, t == 'ol', depth)
        elif t == 'p':
            if not has_text(k): continue
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(7)
            add_runs(p, k)
        elif t == '#text':
            txt = k.text.strip()
            if txt:
                p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(7)
                r = p.add_run(txt); r.font.name = SERIF; r.font.size = Pt(10.5)
        elif t in VOID:
            continue
        elif set(k.cls()) & CALLOUT and not has_block(k):
            add_callout(doc, k)
        elif has_block(k):
            render(doc, k, depth)
        else:
            if not has_text(k): continue
            c = set(k.cls())
            if c & CALLOUT:
                add_callout(doc, k)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(6)
                if 'eyebrow' in c:
                    add_runs(p, k, {'font': MONO, 'caps': True, 'size': 8, 'color': ACC})
                else:
                    add_runs(p, k)

def parse(path):
    src = open(path, encoding='utf-8').read().split('</style>', 1)[-1]
    p = Tree(); p.feed(src); p.close()
    return p.root

def base_doc():
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = SERIF; st.font.size = Pt(10.5)
    st.paragraph_format.space_after = Pt(7)
    st.paragraph_format.line_spacing = 1.15
    rPr = st.element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
    for a in ('w:ascii','w:hAnsi','w:cs','w:eastAsia'): rf.set(qn(a), SERIF)
    for s in doc.sections:
        s.top_margin = Inches(0.85); s.bottom_margin = Inches(0.85)
        s.left_margin = Inches(0.8); s.right_margin = Inches(0.8)
    return doc

def part_title(doc, eyebrow, title, blurb):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
    r = p.add_run(eyebrow.upper()); r.font.name = MONO; r.font.size = Pt(8)
    r.bold = True; r.font.color.rgb = ACC
    h = doc.add_paragraph(); h.paragraph_format.space_after = Pt(6)
    r = h.add_run(title); r.font.name = SANS; r.font.size = Pt(26); r.bold = True
    r.font.color.rgb = INK
    if blurb:
        b = doc.add_paragraph(); b.paragraph_format.space_after = Pt(10)
        r = b.add_run(blurb); r.font.name = SERIF; r.font.size = Pt(11.5)
        r.italic = True; r.font.color.rgb = INK2
        bottom_rule(b)
