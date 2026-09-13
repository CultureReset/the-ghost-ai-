# Document build

Turns the six styled HTML sources into downloadable documents: PDF, Word, web
pages and one combined markdown file. Everything lands in `documents/`.

## What produces what

| Script | Job |
|---|---|
| `h2md.py` | HTML → markdown. A tree walker, not a regex pass — an earlier regex version silently dropped every callout body. |
| `wrap.py` | Wraps a source file into a standalone HTML page and adds print CSS (Letter, page breaks before each section, no orphaned headings). |
| `mkdocx.py` | Walks the same tree into a real Word document: Heading 1–4, Table Grid tables, shaded code blocks, callouts as bordered paragraphs. |
| `build_record.py` | Writes `A-NEXT-GENT-Complete-Record.md` — all six parts, cover and contents. |
| `build_docs.py` | Builds every PDF and DOCX, then merges the PDFs with a cover, bookmarks and metadata. |
| `cover.html` | Cover and contents page for the combined PDF. |
| `index_src.html` | Landing page for `documents/`. |

## Running it

Needs `python-docx`, `pypdf`, and a Chromium binary for print-to-PDF.
`build_docs.py` points at the Playwright Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; change `CHROME` for a
different machine.

```
pip install python-docx pypdf
python3 build_record.py     # markdown
python3 build_docs.py       # pdf + docx + html
```

Fonts (Archivo, Source Serif 4, JetBrains Mono) are base64-embedded in
`documents/assets/fonts.css`, so the pages render correctly with no network.
The PDFs embed their own copies and need nothing.

## Note on `cryptography`

`pypdf` pulls in `cryptography`, whose Rust bindings panic on import in some
containers. `build_docs.py` installs a `sys.meta_path` blocker that forces the
ImportError so `pypdf` takes its pure-Python path. Remove it if the bindings
work where you're building.

## The repo catalog

`catalog_data.py` holds every entry in Part VII as structured data — 244 rows
across 26 sections, each `(repo, licence, verdict, description)`. A leading `*`
on a repo name marks a fact re-verified on the web. `render_catalog.py` turns it
into `every-repo.html` using the same design system as the other parts.

Edit the data, re-run `render_catalog.py`, then `build_docs.py`. Do not edit
`every-repo.html` directly — it is generated.
