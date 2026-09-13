import sys, re, os

PRINT_CSS = """
<style>
@page { size: Letter; margin: 16mm 14mm 18mm 14mm; }
html, body { background:#fff !important; }
body { margin:0 !important; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
nav.toc, .toc { display:none !important; }
h1,h2,h3,h4 { break-after: avoid; page-break-after: avoid; }
table, pre, .flag, .callout, .card, figure { break-inside: avoid; page-break-inside: avoid; }
tr { break-inside: avoid; }
h2 { break-before: page; page-break-before: page; }
h2:first-of-type { break-before: auto; page-break-before: auto; }
pre { white-space: pre-wrap; word-wrap: break-word; font-size: 9pt !important; }
table { font-size: 9.5pt !important; width:100% !important; table-layout: fixed; }
td, th { word-wrap: break-word; overflow-wrap: anywhere; }
body, p, li { font-size: 10.5pt; }
a { color: inherit; text-decoration: none; }
</style>
"""

FONT_LINK = '<link rel="stylesheet" href="assets/fonts.css">'
def _fonts():
    return FONT_LINK

def wrap(path, out, title=None, extra_css=PRINT_CSS):
    src = open(path, encoding='utf-8').read()
    src = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>', '', src)
    if title is None:
        m = re.search(r'<title>(.*?)</title>', src, re.S)
        title = m.group(1).strip() if m else os.path.basename(path)
    head_part, _, body_part = src.partition('</style>')
    if body_part:
        head_part += '</style>'
    else:
        head_part, body_part = '', src
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           + _fonts() + head_part + '\n'
           '<style>img{max-width:100%}[hidden]{display:none!important}'
           'body{margin:0}</style>\n'
           + extra_css +
           '</head>\n<body>\n' + body_part + '\n</body>\n</html>\n')
    open(out, 'w', encoding='utf-8').write(doc)
    return out

if __name__ == '__main__':
    wrap(sys.argv[1], sys.argv[2])
