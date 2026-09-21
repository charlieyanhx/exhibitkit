# exhibitkit

[![ci](https://github.com/charlieyanhx/exhibitkit/actions/workflows/ci.yml/badge.svg)](https://github.com/charlieyanhx/exhibitkit/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)

Sell-side-style research documents from Markdown: a cover with key takeaways and a conflict
box, part bands and numbered chapters with an opener panel, **numbered exhibits with the caption
above and the source line beneath**, cross-references that resolve to *Exhibit N*, a themed
running header and footer, and a disclosure appendix assembled from a library of sections
(including the CFTC-style hypothetical-performance language). Three themes ship — `navy`
(house style), `foghnan` (Fóghnan Trading brand: plum chrome, gold and teal charts) and
`claret` (internal memo) — each with a chart palette validated in OKLab for normal and
colour-deficient vision, and a matplotlib style so figures match the page. The one design
rule: **an exhibit never travels without its source line, and a document never ships without
its disclosures** — a core set of seven disclosure sections and the cover conflict statement are
rendered whatever the front matter says. `exhibitkit check` enforces both, plus the house rule that every quoted
Sharpe ratio carries its basis label.

The pipeline is pandoc for prose (Markdown → LaTeX through one Lua filter) and Python for
everything document-level (theme, fonts, cover, appendix, the XeTeX run and its log). There is
no regex post-processing of pandoc output anywhere.

## Run it

```bash
pip install -e ".[dev]"              # needs pandoc >= 3 and xelatex on PATH
pytest -q                            # 50 tests: palette identities, theme validation, the Lua filter through pandoc,
                                     #   the checker's rules, claims, and the end-to-end builds (skipped without TeX)
exhibitkit demo --theme foghnan      # synthetic figures + a document exercising every device -> exhibitkit-demo/demo.pdf
exhibitkit demo --layout issue       # the two-column newsletter layout on the same synthetic data
exhibitkit init mydoc                # scaffold a document directory
exhibitkit check mydoc/mydoc.md      # house rules; exit 1 on any error
exhibitkit build mydoc/mydoc.md      # -> mydoc/mydoc.pdf
exhibitkit themes                    # built-in themes with the fonts they resolved to on this machine
```

## The document model

```markdown
---
title: Trading the Smile
subtitle: Three numbers, two flows, one toll
series: OPTIONS RESEARCH | PRIMER
date: 2026-09-11
theme: foghnan
authors: [{name: Charlie Yan, role: Independent options research, contact: github.com/charlieyanhx}]
takeaways: ["The surface moves as three things ([](#ex-pca))."]
sidebar: [{title: Scope, text: Educational primer; operating parameters withheld.}]
disclosures: {sections: [certification, nature, hypothetical, conflicts, warranty, distribution]}
rules: {sharpe_basis: true}
---

# Part 1 — What the smile is            <- full-width band, new page
## 2. It is only three numbers          <- numbered chapter head
::: {.box title="In this chapter"}      <- shaded opener panel
- Level is ~93% of the variance.
:::
The shares are in [](#ex-pca).          <- renders as "Exhibit 2"
::: {.exhibit #ex-pca title="Principal components of daily surface changes" source="Cboe quotes, author's calculations" width=0.9}
![](figs/pca.pdf)
:::
::: {.exhibit #ex-menu title="Trade menu" source="Author's calculations" note="Hypothetical results." cols="lrr"}
| Structure | Apr 4 | Apr 8 |
|---|---:|---:|
| Short straddle | +$1,292 | +$2,114 |
:::
```

The cover opens with a full-bleed masthead band: the theme's wordmark (`brand.name`, in `brand.font`) on the text block's left edge, the document's `series` letter-spaced on the right, and a rule in `brand.rule` beneath. Themes without a `brand` get the same band with the series and date.

A document can register the claims it makes: a `::: {.claim id="sw001.cpi_through"}` div marks
the sentence and a `claims:` entry in the front matter carries its test (metric, args, operator,
value, probability, resolve date). The PDF shows a `CLAIM … · RESOLVES …` label beside the
sentence, `exhibitkit claims doc.md` writes the records as JSON, and
[claimkeeper](https://github.com/charlieyanhx/claimkeeper) judges them from data when the date
comes. `check` refuses a marked claim with no spec and a spec that is never marked.

Two layouts ship. `primer` (default) is the long-form report above. `layout: issue` is a
two-column newsletter: masthead cover with the lead beside an auto-built **Inside** index and a
key-marks table, one section per page (or flowing, with `sections_new_page: false`) with a
full-width head and deck, column-width exhibits with a units subtitle that move whole to the
next column when they do not fit, `::: {.colbreak}`, `wide=true` exhibits that break the
columns (use it for tables of six or more columns; `check` warns otherwise), and compact
fine-print disclosures at the end. Exhibits in the primer layout are `figure` floats
with their own counter that span the text block and the margin
column; tables become `booktabs` tabulars with zebra rows (pandoc's `longtable` cannot live in
a float, so the filter renders them itself). `float=false` pins an exhibit in place. The page
is asymmetric: a 4.95in text block and a 1.65in margin column for `::: {.keynumber value="93%"}`
and `::: {.aside}` devices; `::: {.pullquote}` sets an in-column quote with an accent rule and
`::: {.closing}` a closing statement. The cover takes a `cover_figure`, `keynumbers` strip,
takeaways and sidebar; a contents page listing chapters and exhibits follows it (`contents:
false` to drop). Part headings open on their own page with the paragraphs that follow them as
the part's abstract. Full grammar, theme schema and the checker's rules are in
[docs/DESIGN.md](docs/DESIGN.md).

## What `check` enforces

| Rule | Level |
|---|---|
| exhibit without `title` or `source`; id not `ex-…`; duplicate id | error |
| `[](#ex-…)` link to an exhibit that does not exist | error |
| image file missing | error |
| front matter missing `title` / `date` / `authors` / `theme`; theme fails to load | error |
| disclosure section not in the library | error |
| `sharpe_basis`: a quoted Sharpe number without *mid / cross / MTM / full calendar / hypothetical / simulated / backtest / live / marking / exit-day* | error |
| exhibit never referenced; more than six takeaways; image wider than the line | warning |

## Charts that match the page

```python
from exhibitkit.mpl import use, FULL
st = use("foghnan")                      # rcParams: fonts, recessive grid, no top/right spines, validated series
fig, ax = plt.subplots(figsize=(FULL, 2.4))
ax.plot(x, y, color=st.series[0])
st.ylabel_above(ax, "Implied volatility (vol points)")
st.save(fig, "figs/smile.pdf")
```

The palette check (`exhibitkit.validate_palette`) computes OKLab lightness and chroma, adjacent-pair
distance under normal vision and under simulated protanopia / deuteranopia / tritanopia (Machado,
Oliveira & Fernandes 2009), and WCAG contrast against the paper. Shipped themes pass (worst adjacent
pair: normal ≥ 19, CVD ≥ 8.2); a user theme that fails is refused at load with the pair named. The
first gold I tried for the brand theme was 2.84:1 against paper; the validator, not my eye, caught it.

## Design rules

Tested:
- OKLab endpoints (white → L = 1, black → L = 0), WCAG black/white = 21:1 exactly, ΔE symmetric and zero on self, Machado rows sum to one within published rounding.
- Every built-in theme loads, resolves fonts, and its palette passes all six checks.
- The Lua filter maps every device to its environment (part band, chapter head, opener box, exhibit float and fixed, booktabs table with inferred or overridden column spec, call-out, warning, `Exhibit N` references) — asserted on pandoc's actual output.
- The checker's errors and warnings fire on crafted documents and stay silent on a valid one; the Sharpe rule fires on "Sharpe of 8.7" and not on "the Sharpe nearly doubles".
- The demo builds to a 5–9 page PDF in all three themes; a document without front matter is refused before any tool runs.

By construction (not a test):
- The cover conflict box and the footer sentence pointing at the appendix cannot be switched off; the disclosure list can be shortened but an unknown section name fails the build.
- Font resolution ends on a TeX Gyre face that TeX Live ships, so a missing brand font degrades the build and is reported in the result rather than failing it.
- Exhibit numbering is order of appearance in the compiled PDF, so a float that moves cannot desynchronise from its references.

## What is where

```text
src/exhibitkit/
  build.py          assemble preamble + cover + body + appendix, run xelatex twice, parse the log -> BuildResult
  check.py          house rules on the pandoc JSON AST -> CheckResult
  document.py       front-matter parsing, date formatting, author block
  themes.py         theme loading + validation;  themes/{navy,foghnan,claret}.yaml
  palette.py        OKLab, CVD simulation, contrast, validate_palette
  fonts.py          fontconfig lookup with the TeX Gyre fallback
  disclosures.py    section library + variable substitution;  disclosures/*.md (11 sections)
  pandoc.py         one extension set, one filter, stdin -> LaTeX / JSON
  lua/exhibits.lua  the filter: divs, headers, links, tables
  templates/        preamble.tex, cover.tex, cover_issue.tex, contents.tex, appendix.tex, appendix_compact.tex, demo.md, demo_issue.md
  mpl.py            matplotlib style matching the theme
  demo.py           synthetic figures + document (used by CI)
  cli.py            build | check | init | themes | demo
tests/              42 tests
docs/DESIGN.md      the spec: pipeline, document model, theme schema, exhibit rules, checker rules
```

## Roadmap

- v0.2: HTML output from the same AST (the filter already keeps numbering in-document); page-breaking tables; a `bibliography` device via pandoc's citeproc.
- v0.3: two-column body option; per-exhibit "chart data" export (CSV beside the PDF) so every figure ships its numbers.
- Not planned: a GUI, or any Markdown extension beyond pandoc's.

## Data and privacy

Everything in this repository is synthetic: the demo draws its series from `numpy.random.RandomState(0)`.
No market data, no private documents, and no theme carries anything beyond colours and font names.
The Fóghnan Trading palette is the public website's.

## Companion repos

[claimkeeper](https://github.com/charlieyanhx/claimkeeper) — the ledger that ingests the claims `exhibitkit claims` emits ·
[tcakit](https://github.com/charlieyanhx/tcakit) · [quant-research-agent](https://github.com/charlieyanhx/quant-research-agent) ·
[deskboard](https://github.com/charlieyanhx/deskboard) · [pricers](https://github.com/charlieyanhx/pricers) · [riskkit](https://github.com/charlieyanhx/riskkit) ·
[volsurf](https://github.com/charlieyanhx/volsurf) · [quotesim](https://github.com/charlieyanhx/quotesim) · [tickq](https://github.com/charlieyanhx/tickq) ·
[lobcore](https://github.com/charlieyanhx/lobcore)

MIT © Hanxiong (Charlie) Yan
