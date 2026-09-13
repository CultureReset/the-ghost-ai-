import re, html, sys
from html.parser import HTMLParser

BLOCK = {'h1','h2','h3','h4','h5','h6','p','ul','ol','table','pre','div',
         'section','article','header','footer','main','nav','blockquote',
         'figure','details','aside'}
VOID = {'br','hr','img','input','meta','link','source','col','wbr'}
SKIP = {'style','script','svg','nav'}

class Node:
    __slots__ = ('tag','attrs','kids','text')
    def __init__(self, tag, attrs=None):
        self.tag = tag; self.attrs = attrs or {}; self.kids = []; self.text = ''
    def cls(self):
        return self.attrs.get('class','').split()

class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node('root'); self.stack = [self.root]; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag in SKIP: self.skip += 1
            return
        if tag in SKIP:
            self.skip = 1; return
        if tag in VOID:
            self.stack[-1].kids.append(Node(tag, dict(attrs))); return
        n = Node(tag, dict(attrs))
        self.stack[-1].kids.append(n); self.stack.append(n)
    def handle_endtag(self, tag):
        if self.skip:
            if tag in SKIP: self.skip -= 1
            return
        if tag in VOID: return
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; return
    def handle_data(self, d):
        if self.skip: return
        if d.strip() or ' ' in d:
            t = Node('#text'); t.text = d; self.stack[-1].kids.append(t)
    def handle_entityref(self, name):
        if self.skip: return
        t = Node('#text'); t.text = html.unescape('&'+name+';'); self.stack[-1].kids.append(t)
    def handle_charref(self, name):
        if self.skip: return
        t = Node('#text'); t.text = html.unescape('&#'+name+';'); self.stack[-1].kids.append(t)

def raw_text(n):
    if n.tag == '#text': return n.text
    if n.tag == 'br': return '\n'
    return ''.join(raw_text(k) for k in n.kids)

def inline(n):
    """Render a node's children as inline markdown."""
    out = []
    for k in n.kids:
        if k.tag == '#text':
            out.append(k.text)
        elif k.tag == 'br':
            out.append('\n')
        elif k.tag in ('strong','b'):
            t = inline(k).strip()
            out.append(f'**{t}**' if t else '')
        elif k.tag in ('em','i'):
            t = inline(k).strip()
            out.append(f'*{t}*' if t else '')
        elif k.tag == 'code':
            t = raw_text(k).strip()
            out.append(f'`{t}`' if t else '')
        elif k.tag == 'a':
            t = inline(k).strip(); href = k.attrs.get('href','')
            out.append(f'[{t}]({href})' if href and t else t)
        elif k.tag == 'span':
            c = k.cls()
            t = inline(k).strip()
            if not t: continue
            if 'lbl' in c or 'k' in c:      out.append(f'**{t}:** ')
            elif 'score' in c:              out.append(f'**[{t}]**')
            elif 'eyebrow' in c or 'tag' in c or 'pill' in c: out.append(f'*{t}*')
            elif 'num' in c or 'n' in c:    out.append(f'**{t}.**')
            else:                           out.append(t)
        else:
            out.append(inline(k))
    s = ''.join(out)
    s = re.sub(r'[ \t]*\n[ \t]*', ' ', s)
    s = re.sub(r'[ \t]{2,}', ' ', s)
    s = re.sub(r'\*\*:\*\*', '', s)
    return s.strip()

def table_md(n):
    rows = []
    def walk(x):
        if x.tag == 'tr': rows.append(x)
        else:
            for k in x.kids: walk(k)
    walk(n)
    out, header = [], False
    for r in rows:
        cells = []
        def cw(x):
            for k in x.kids:
                if k.tag in ('th','td'): cells.append(inline(k).replace('|', r'\|').replace('\n',' '))
                else: cw(k)
        cw(r)
        if not cells: continue
        out.append('| ' + ' | '.join(cells) + ' |')
        if not header:
            out.append('|' + '---|' * len(cells)); header = True
    return '\n'.join(out)

def has_block(n):
    for k in n.kids:
        if k.tag in BLOCK: return True
        if k.tag not in ('#text',) and has_block(k): return True
    return False

def render(n, out, shift):
    for k in n.kids:
        t = k.tag
        if t in ('h1','h2','h3','h4','h5','h6'):
            txt = inline(k)
            if not txt: continue
            lvl = int(t[1])
            if lvl == 1 and shift: continue
            out.append('\n' + '#' * min(lvl + shift, 6) + ' ' + txt.replace('\n',' ') + '\n')
        elif t == 'pre':
            code = html.unescape(re.sub(r'<[^>]+>', '', raw_text(k))).strip('\n')
            out.append('```\n' + code + '\n```\n')
        elif t == 'table':
            md = table_md(k)
            if md: out.append(md + '\n')
        elif t in ('ul','ol'):
            marker = '-' if t == 'ul' else '1.'
            items = [x for x in k.kids if x.tag == 'li']
            for li in items:
                if has_block(li):
                    sub = []
                    render(li, sub, shift)
                    txt = '\n'.join(s for s in sub if s.strip()).strip()
                    lead = inline_leading_text(li)
                    if lead: out.append(f'{marker} {lead}')
                    if txt: out.append(txt)
                else:
                    txt = inline(li).replace('\n', ' ')
                    if txt: out.append(f'{marker} {txt}')
            out.append('')
        elif t == 'p':
            txt = inline(k)
            if txt: out.append(txt.replace('\n', '  \n') + '\n')
        elif t == '#text':
            txt = k.text.strip()
            if txt: out.append(txt + '\n')
        elif t in VOID:
            continue
        elif has_block(k):
            render(k, out, shift)
        else:
            txt = inline(k)
            if not txt: continue
            c = k.cls()
            if 'eyebrow' in c or 'tag' in c or 'pill' in c:
                txt = f'*{txt}*'
            elif 'lbl' in c:
                txt = f'**{txt}:**'
            out.append(txt.replace('\n', '  \n') + '\n')

def inline_leading_text(li):
    parts = []
    for k in li.kids:
        if k.tag in BLOCK: break
        parts.append(k)
    tmp = Node('span'); tmp.kids = parts
    return inline(tmp).replace('\n', ' ')

def convert(path, shift=0):
    src = open(path, encoding='utf-8').read()
    src = src.split('</style>', 1)[-1]
    p = Tree(); p.feed(src); p.close()
    out = []
    render(p.root, out, shift)
    txt = '\n'.join(out)
    txt = re.sub(r'[ \t]+\n', '\n', txt)
    txt = re.sub(r'\n{3,}', '\n\n', txt)
    return txt.strip()

if __name__ == '__main__':
    print(convert(sys.argv[1], shift=int(sys.argv[2]) if len(sys.argv) > 2 else 0))
