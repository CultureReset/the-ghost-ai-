import h2md, datetime

PARTS = [
 ("Part I — An Honest Read", "honest-read.html",
  "Assessment: what it is, what to bet on, the kiosk, what worries me, what I'd do, the odds."),
 ("Part II — The Playbook", "anextgent-playbook.html",
  "The complete working record: thesis, products, architecture, data plane, economics, go-to-market, brand, IP, founder assets, risks."),
 ("Part III — The Build Spec", "build-spec.html",
  "Platform architecture: data placement, the business record, ingestion, capabilities, the app contract, surfaces, the App Store pipeline, isolation, repo layout, build order."),
 ("Part IV — The Build Plan", "remote-control-build-plan.html",
  "Phases P0–P5 with done-when gates, the weekly ops loop, economics, risk register, first thirty days."),
 ("Part V — The Parts Catalog", "parts-catalog.html",
  "Every open-source component by layer with a use / study / careful / skip verdict."),
 ("Part VI — The App Store Layer", "app-store.html",
  "Package format (Agent Plugins / Agent Skills), index-not-store distribution, the trust ladder, the installer, three targets per app, the nine deployable units, Grok Bot, Apple, and the spreadsheet channel."),
]

out = []
out.append("# A NEXT GENT — Complete Working Record\n")
out.append("*Compiled %s — a Linux computer made simple, and the business around it.*\n" % datetime.date.today().isoformat())
out.append("---\n")
out.append("## Contents\n")
for i, (title, _f, blurb) in enumerate(PARTS, 1):
    out.append("%d. **%s** — %s" % (i, title, blurb))
out.append("\n---\n")

for title, f, blurb in PARTS:
    out.append("\n# %s\n" % title)
    out.append(blurb + "\n")
    out.append(h2md.convert(f, shift=1))
    out.append("\n---\n")

open("A-NEXT-GENT-Complete-Record.md","w").write("\n".join(out).rstrip() + "\n")
