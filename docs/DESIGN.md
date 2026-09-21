# exhibitkit — design

Sell-side-style research documents from Markdown: numbered exhibits, themed chrome, a
disclosure appendix, and a matplotlib style that matches the theme. One design rule: **an
exhibit never travels without its source line, and a document never ships without its
disclosures** — both are enforced by `exhibitkit check`, not by convention.

## 1. Pipeline

```
doc.md ──pandoc (markdown+fenced_divs, Lua filter)──▶ body.tex
                                                       │
theme.yaml + front matter ──Python templates──▶ preamble / cover / appendix
                                                       │
                                        assemble ──▶ doc.tex ──xelatex ×2──▶ doc.pdf
```

* pandoc does what pandoc is good at: Markdown → LaTeX for prose, lists, emphasis, math.
* A Lua filter (`lua/exhibits.lua`) maps three structural devices to LaTeX: fenced divs
  (`exhibit`, `box`, `callout`, `warning`), headers (H1 part band, H2 chapter, H3 subhead),
  and `#ex-…` links (→ `Exhibit N`). Tables inside exhibits are rendered as `booktabs`
  tabulars by the filter, because pandoc's `longtable` cannot live inside a float.
* Python owns everything that is *document-level* rather than *prose-level*: theme
  resolution, font fallback, the cover, the running header/footer, the disclosure appendix,
  the LaTeX run and its log. No regex post-processing of pandoc output anywhere.

## 2. Document model

A document is a Markdown file with a YAML front matter block.

```yaml
---
title: Trading the Smile
subtitle: Three numbers, two flows, one toll
series: OPTIONS RESEARCH | PRIMER        # cover band, left
date: 2026-09-11
theme: foghnan                           # navy | foghnan | claret | path/to/theme.yaml
authors:
  - {name: Charlie Yan, role: Independent options research, contact: github.com/charlieyanhx}
takeaways:                               # cover "KEY TAKEAWAYS" (≤ 6; may reference exhibits)
  - The surface moves as three things ([](#ex-pca)).
sidebar:                                 # cover sidebar blocks, in order
  - {title: Scope, text: Educational primer …}
disclosures:
  conflict: The author trades …          # cover box; default text if omitted
  sections: [certification, nature, options_risk, hypothetical, data, conflicts,
             forward_looking, third_party, no_affiliation, warranty, distribution]
  extra:                                 # appended after the library sections
    - {title: Model risk, text: …}
  variables: {entity: the author, instruments: "SPY, QQQ and IWM"}
footer: Charlie Yan | Independent options research
rules: {sharpe_basis: true}              # house rules for `check` (see §6)
---
```

Front matter also takes `cover_figure` / `cover_caption` (hero on the cover), `keynumbers`
(a strip of `{value, label}` tiles under the hero), `header` (running header text) and
`contents` (default true; a page listing chapters and exhibits after the cover).

Body conventions:

| Markdown | Rendered as |
|---|---|
| `# Part 1 — What the smile is` | full-width band, new page |
| `## 3. Who is on the other side` | numbered chapter head with rule |
| `### Three lines` | sub-head |
| `::: {.box title="In this chapter"} … :::` | shaded opener panel |
| `::: {.callout title="…"} … :::` | shaded call-out with title |
| `::: {.warning} … :::` | framed bold notice |
| `::: {.exhibit #ex-id title="…" source="…" note="…"} … :::` | numbered exhibit (figure or table) |
| `[](#ex-id)` / `[the smile](#ex-id)` | `Exhibit 3` / `the smile (Exhibit 3)` |
| `::: {.keynumber value="93%"} label :::` | large accent numeral with a small label, in the margin column |
| `::: {.aside} … :::` | small slate note in the margin column |
| `::: {.pullquote} … :::` | in-column quote, accent rule above, sans italic |
| `::: {.closing} … :::` | closing statement box with an accent left rule |

Exhibit attributes: `title` (required), `source` (required), `short` (for the exhibit list; defaults to the title before its first colon), `note`, `width` (fraction of
line width for the first image, default 1.0), `cols` (LaTeX column spec override for a
table, e.g. `lrrr` or `p{2cm}p{5cm}`), `float` (`true` default; `false` pins it in place).
Exhibit ids must start with `ex-` and be unique; numbering is order of appearance.

## 3. Themes

A theme is a YAML file (`src/exhibitkit/themes/*.yaml` or a user path):

```yaml
name: foghnan
colors:
  primary: "#301933"    # bands, chapter heads, rules
  accent:  "#A37EB8"    # sub-heads, exhibit rule
  ink:     "#1A1A1A"    # body text
  slate:   "#5A5F66"    # captions, sources, header/footer
  panel:   "#F1EEF4"    # box backgrounds
  rule:    "#CFC6D6"    # header rule, dividers
fonts:
  main: [Charter, Georgia, "TeX Gyre Pagella"]         # first installed wins; last always exists in TeX Live
  sans: [Jost, "Helvetica Neue", Helvetica, "TeX Gyre Heros"]
  mono: [Menlo, "DejaVu Sans Mono", "TeX Gyre Cursor"]
chart:
  series: ["#452C48", "#C98B1F", "#1A9EB0", "#A37EB8"] # validated categorical order
  neutral: "#B9BEC5"
  grid: "#D9DCE0"
```

A theme may carry a `credit` line (the `foghnan` theme: "Research assisted and accelerated by Silkcodex, by Fóghnan Trading."); every document built on the theme renders it on the cover and at the end of the disclosures, and front matter `credit:` overrides it (empty string to suppress).

Font resolution asks fontconfig (`fc-list :family`) and takes the first installed family;
the last entry must be a TeX Gyre face, which TeX Live always ships, so a build never fails
on fonts — it degrades. The resolved names are reported in the build result.

Chart palettes are **validated, not eyeballed** (`palette.py`): OKLab lightness band
0.43–0.77, OKLab chroma ≥ 0.10, adjacent-pair ΔE ≥ 15 (normal vision) and ≥ 8 under
simulated protan/deutan/tritan (Machado et al. 2009 matrices), and ≥ 3:1 contrast against
the paper. Shipped themes pass; a user theme that fails is rejected at load with the failing
pair named.

## 4. Exhibits

The `exhibit` LaTeX environment is a `figure` float carrying its own counter, a sans-serif
bold caption **above** ("Exhibit N: title"), a coloured rule, the content, then optional
`Note:` and mandatory `Source:` lines in small slate sans beneath — the sell-side layout.
Floats let text fill pages; `float=false` gives an unbreakable in-place version for the
rare exhibit that must sit next to its sentence. Tables render with `booktabs`, sans,
footnote size, header bold; column spec is inferred from pandoc alignments unless `cols` is
given. Long, page-breaking tables are out of scope for v0.1 (use two exhibits).

## 5. Disclosures

`src/exhibitkit/disclosures/*.md` is a library of sections, each a Markdown file with
`$variable` placeholders (`string.Template`): `certification`, `nature`, `options_risk`,
`hypothetical` (the CFTC-style hypothetical-performance language), `data`, `conflicts`,
`forward_looking`, `third_party`, `no_affiliation`, `warranty`, `distribution`. The
document picks and orders sections; unknown names are an error; `extra` sections append.
Variables default from the front matter (`author`, `date`, `entity`) and can be overridden.
The cover conflict box (the package's standard statement, with any document-specific sentence appended — `disclosures.conflict` adds, it does not replace) and the footer sentence pointing at the disclosures are always rendered — they are not optional. Compact end-matter opens with a *Disclosures* heading.

### The rule

No document built by this package ships without the core disclosures and the cover conflict statement. That is enforced in `build`, not by convention.

## 6. House rules (`exhibitkit check`)

`check` parses the document through pandoc's JSON AST and fails (exit 1) on:

1. an exhibit without `title` or `source`; an id not starting with `ex-`; a duplicate id
2. a `#ex-…` link with no matching exhibit
3. an image whose file does not exist (relative to the document)
4. missing front matter keys: `title`, `date`, `authors`, `theme`; a theme that does not load
5. a disclosure section name not in the library
6. `sharpe_basis` (opt-in): a paragraph that quotes a Sharpe *number* ("Sharpe of 1.2", "Sharpe
   ratio by 2.1×", "a 1.4 Sharpe") with none of the basis words *mid, cross, MTM, full calendar,
   hypothetical, simulated, backtest, live, mark/marked/marking, exit-day* — the rule that every
   Sharpe carries its basis label. "Sharpe" as a concept, with no number beside it, is free.

and warns on: an exhibit never referenced from the text; more than six takeaways; an image
wider than the line.

## 7. Charts

`exhibitkit.mpl.use("foghnan")` applies the theme to matplotlib (fonts, recessive grid,
no top/right spines, 2px lines, 8px markers) and returns a `Style` with the validated
series, `ylabel_above(ax, text)` (the horizontal y-label above the axis), `date_axis(ax)`,
`year_axis(ax)`, and `save(fig, path)` (tight, PDF, fonttype 42). Widths: `FULL = 6.3`,
`HALF = 3.05` inches, matching the page templates' text width.

## 8. Build result and errors

`build()` returns `BuildResult(pdf, tex, pages, fonts, warnings, errors)`. LaTeX errors
(`!` lines) fail the build with the first five quoted; overfull boxes over 10pt are
warnings with their line numbers. `--keep-tex` leaves the assembled `.tex` beside the PDF.

## 9. The `issue` layout

`layout: issue` is the two-column newsletter: a masthead cover (series line, masthead, date |
time, issue; headline; the lead — everything before the first H2 — beside an **Inside** index
built from the H2s and their `::: {.deck}` lines with live page references, and a **Key marks**
table from `marks`), then one section per H2, each opening on a new page (`sections_new_page:
false` to flow) with a full-width head and deck and a two-column body. Devices that exist only
here: `::: {.deck}` (folded into the section head), `::: {.colbreak}` (`\columnbreak`), H4 → a
small-caps label, `::: {.small}` / `::: {.fineprint}` (footnotesize / scriptsize slate), and
exhibit attributes `subtitle` (a units line under the title) and `wide=true` (breaks the
columns for a full-width exhibit). Exhibits are column-width and in place, never floats.
`disclosures: {compact: true}` renders the disclosure sections as run-in fine print at the end
of the last section instead of an appendix part. The page is 9-pt `extarticle` on a 6.9in text
block with no margin column; `keynumber` becomes an in-column device. Front matter keys:
`masthead`, `issue`, `time`, `byline`, `dataline`, `marks_title`, `marks`.

## 10. Non-goals (v0.1)

HTML output, two-column body, page-breaking tables, bibliographies (use pandoc-citeproc
upstream if needed), and any GUI. All are additive later; the AST-based filter and the
Python-owned assembly are the seams they would plug into.
