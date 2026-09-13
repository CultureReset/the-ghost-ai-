# -*- coding: utf-8 -*-
import html as H
import catalog_data as C

CSS = open('parts-catalog.html', encoding='utf-8').read().split('<style>',1)[1].split('</style>',1)[0]
EXTRA = """
  .p-core{background:var(--accent-soft);color:var(--accent)}
  table.cat{table-layout:fixed;min-width:860px}
  table.cat td.repo{white-space:normal;overflow-wrap:anywhere}
  table.cat td.repo span.nolink{font-size:.79rem;line-height:1.35;display:inline-block}
  table.cat td.d{min-width:0}
  td.chk{width:16px;padding-right:0;color:var(--use);font-size:.8rem}
  .counts{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-top:18px}
  .cbox{background:var(--surface);border:1px solid var(--rule);border-radius:3px;padding:13px 15px}
  .cbox .n{font-family:"JetBrains Mono",monospace;font-size:1.5rem;font-weight:700;color:var(--accent);line-height:1}
  .cbox .l{font-size:.78rem;color:var(--muted);margin-top:4px;line-height:1.35}
  .secnum{font-family:"JetBrains Mono",monospace;font-size:.7rem;font-weight:700;
    letter-spacing:.14em;color:var(--accent)}
  .toc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:2px 22px;margin-top:14px}
  .toc-grid a{display:flex;gap:10px;padding:6px 0;border-bottom:1px solid var(--rule);
    font-size:.9rem;color:var(--ink);border-bottom:1px solid var(--rule)}
  .toc-grid a:hover{color:var(--accent)}
  .toc-grid a .k{font-family:"JetBrains Mono",monospace;font-size:.72rem;color:var(--accent);
    font-weight:700;padding-top:3px;min-width:22px}
  .toc-grid a .c{font-family:"JetBrains Mono",monospace;font-size:.72rem;color:var(--muted);
    margin-left:auto;padding-top:3px}
"""

VERDICT = {
  'core':  ('p-core',  'CORE'),
  'use':   ('p-use',   'USE'),
  'study': ('p-study', 'STUDY'),
  'care':  ('p-care',  'CAREFUL'),
  'skip':  ('p-skip',  'SKIP'),
}

def repo_cell(r):
    chk = r.startswith('*')
    name = r.lstrip('*')
    if name == '—' or '/' not in name:
        return chk, f'<span class="nolink">{H.escape(name)}</span>'
    return chk, f'<span class="nolink">{H.escape(name)}</span>'

def render():
    out = []
    out.append('<title>Every Repo</title>')
    out.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
               'family=Archivo:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700'
               '&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400'
               '&display=swap">')
    out.append('<style>' + CSS + EXTRA + '</style>')

    nrepos = len({r[0].lstrip('*') for s in C.S for r in s['rows']})
    nrows  = sum(len(s['rows']) for s in C.S)
    counts = {}
    for s in C.S:
        for r in s['rows']:
            counts[r[2]] = counts.get(r[2], 0) + 1

    # masthead
    out.append('<header class="mast"><div class="wrap mast-inner">')
    out.append('<span class="eyebrow">The Complete Deck</span>')
    out.append('<h1>Every Repo</h1>')
    out.append('<p class="lede col">Two hundred and twenty-six projects across twenty-six layers &mdash; '
               'the full assembly list, not the short one. Each entry says what it is, what job it does '
               'in <i>your</i> build, what it is licensed under, and whether to use it, read it, '
               'handle it carefully, or leave it alone.</p>')
    out.append('<div class="key">')
    for k in ('core','use','study','care','skip'):
        cls, lbl = VERDICT[k]
        blurb = {'core':'Load-bearing','use':'Build on this','study':"Read it, don't depend on it",
                 'care':'Real catch attached','skip':'Wrong tool, or a trap'}[k]
        out.append(f'<span class="keyitem"><span class="pill {cls}">{lbl}</span>{blurb}</span>')
    out.append('</div>')
    out.append('<div class="counts">')
    out.append(f'<div class="cbox"><div class="n">{nrepos}</div><div class="l">unique projects</div></div>')
    for k in ('core','use','study','care','skip'):
        out.append(f'<div class="cbox"><div class="n">{counts.get(k,0)}</div>'
                   f'<div class="l">{VERDICT[k][1].lower()}</div></div>')
    out.append('</div>')
    out.append('</div></header>')

    out.append('<div class="wrap">')

    # contents
    out.append('<section id="contents"><div class="sec-head">'
               '<span class="secnum">Contents</span>'
               '<h2>Twenty-six layers</h2>'
               '<p class="note">Ordered roughly from the metal upward: the box, the distribution '
               'machine, the execution layer that is the actual product, then the platform above it.</p>'
               '</div><div class="toc-grid">')
    for s in C.S:
        out.append(f'<a href="#s{s["num"]}"><span class="k">{s["num"]}</span>'
                   f'<span>{H.escape(s["title"])}</span>'
                   f'<span class="c">{len(s["rows"])}</span></a>')
    out.append('</div>')
    out.append('<div class="flag"><h3>How to read the licence column</h3>'
               '<p>Licences are recorded as they stood when this project catalogued them, and they '
               'change &mdash; three entries here changed after they were first written down. '
               'A <span class="mono">&check;</span> beside a repository name means that entry was '
               're-verified on the web today; everything else is from the working record and should '
               'be re-checked before it becomes load-bearing in a build you ship. GitHub itself is '
               'unreachable from the environment this was compiled in, so nothing here was confirmed '
               'by opening the repository directly.</p></div>')
    out.append('</section>')

    for s in C.S:
        out.append(f'<section id="s{s["num"]}"><div class="sec-head">')
        out.append(f'<span class="secnum">{s["num"]}</span>')
        out.append(f'<h2>{H.escape(s["title"])}</h2>')
        out.append(f'<p class="lede">{s["lede"]}</p>')
        if s.get('note'):
            out.append(f'<p class="note">{s["note"]}</p>')
        out.append('</div>')
        out.append('<div class="tablewrap"><table class="cat">'
                   '<colgroup><col style="width:26px"><col style="width:178px">'
                   '<col style="width:96px"><col style="width:86px"><col></colgroup>'
                   '<thead><tr>'
                   '<th></th><th>Project</th><th>Licence</th><th>Verdict</th>'
                   '<th>What it is, and the job it does here</th>'
                   '</tr></thead><tbody>')
        for repo, lic, verdict, desc in s['rows']:
            chk, cell = repo_cell(repo)
            cls, lbl = VERDICT[verdict]
            mark = '&check;' if chk else ''
            out.append('<tr>'
                       f'<td class="chk">{mark}</td>'
                       f'<td class="repo">{cell}</td>'
                       f'<td class="lic">{H.escape(lic)}</td>'
                       f'<td class="v"><span class="pill {cls}">{lbl}</span></td>'
                       f'<td class="d">{desc}</td>'
                       '</tr>')
        out.append('</tbody></table></div>')
        if s.get('flag'):
            title, body = s['flag']
            out.append(f'<div class="flag"><h3>{H.escape(title)}</h3><p>{body}</p></div>')
        out.append('</section>')

    # ---- closing: the order ----
    ORDER = [
     ("<b>scrcpy</b> &mdash; get a real Android phone mirrored on a Linux box with working input. "
      "One afternoon, and the first time the idea stops being a description."),
     ("<b>uiautomator2</b> &mdash; dump the view tree of the Google Business Profile app and tap a "
      "button from Python. Then delete <span class='mono'>ghost/device.py</span>."),
     ("<b>Maestro and Maestro Studio</b> &mdash; record one flow by pointing at elements. Compare "
      "what their waiting logic does to what yours was going to do."),
     ("<b>The test that decides everything</b> &mdash; install the real apps a Destin charter or a "
      "restaurant actually uses. Turn on an accessibility service. See what still runs. This is the "
      "one assumption underneath the entire business, and it has still not been run."),
     ("<b>llama.cpp and llama-swap</b> &mdash; one endpoint, two models, hot swap on demand. An hour, "
      "and the orchestrator has an engine room."),
     ("<b>wyoming + openWakeWord + silero-vad + faster-whisper + kokoro</b> &mdash; wire five small "
      "things together and say a sentence to your box. This is the demo people repeat to other people."),
     ("<b>Playwright</b> &mdash; write the same fact through Android and read it back through the "
      "browser. The moment those two agree on a different path, you have the product."),
     ("<b>home-assistant/operating-system</b> &mdash; read the update and recovery design end to end "
      "before committing to your own."),
     ("<b>bootc + greenboot</b> &mdash; build one image, boot it, break it on purpose, watch it roll "
      "itself back. Now you have a company rather than a script."),
    ]
    out.append('<section id="order"><div class="sec-head">'
               '<span class="secnum">The order</span>'
               '<h2>Nine steps, and the order matters more than the list</h2>'
               '<p class="lede">Anyone can clone two hundred and twenty-six repositories in a '
               'weekend. The useful question is which three are working by Friday.</p></div>')
    out.append('<ol class="order">')
    for item in ORDER:
        out.append(f'<li><span>{item}</span></li>')
    out.append('</ol>')
    out.append('<div class="flag"><h3>Steps one to four are the product</h3>'
               '<p>Five and six are the demo. Seven is the defensible part. Eight and nine are the '
               'company. Step four is the only one that can end the project, which is an argument '
               'for running it this week rather than after another document.</p></div>')
    out.append('</section>')

    out.append('<footer class="wrap"><p>Compiled from the full working record. '
               'Two hundred and twenty-six projects, twenty-six layers, two hundred and forty-four '
               'entries &mdash; some listed twice where a project is both a part and a trap. '
               'Exactly one job in this catalogue has no upstream: fingerprint-gated remote control '
               'with independent read-back. Everything else is a part you did not have to build.</p></footer>')

    out.append('</div>')
    return '\n'.join(out)

if __name__ == '__main__':
    open('every-repo.html','w',encoding='utf-8').write(render())
    import os; print(os.path.getsize('every-repo.html'), 'bytes')
