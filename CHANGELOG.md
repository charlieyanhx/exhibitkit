# Changelog

## 0.1.2 — 2026-09-14
- Issue cover: optional front-matter `headline` — the title with ` | ` where the cover headline should break (`title` stays the plain string for metadata and the contents page).
- Cover masthead redrawn: a full-bleed band across the top of the page (tikz page overlay, so it ignores the margins) with the wordmark on the text block's left edge, the series label letter-spaced on its right, and a brand-colour rule beneath (`brand.rule`, default = accent; Fóghnan gold `#C9A24D`). Band height and wordmark size are set per layout (primer 0.68in / 25pt, issue 0.62in / 22pt). Both covers pull the title up to sit under the band.
- Primer cover: sidebar set in `\scriptsize` at 0.39 of the width so the hero, key numbers, takeaways and the conflict box fit on one page.
- `\plainband` (themes without a brand) uses the same overlay.

## 0.1.1 — 2026-09-12
- Claims: `::: {.claim id=…}` marks a falsifiable sentence (rendered with a `CLAIM <id> · RESOLVES <date>` label), its test lives in front matter `claims:`; `exhibitkit claims doc.md` emits the JSON claimkeeper ingests; `check` errors on a marked claim without a spec, a spec never marked, or a spec missing a field.
- Issue layout: column exhibits are measured before placement and moved whole to the next column or page when they do not fit (`\needspace` on the boxed exhibit); an exhibit that opens a fresh pair of columns is measured at column width before the columns start. Previously an exhibit taller than the space left ran off the page.
- `sections_new_page: false` lets issue sections flow instead of starting on a new page.
- `exhibitkit check` warns when a table with six or more columns sits in a column exhibit without `wide="true"`.

## 0.1.0 — 2026-09-12
- `layout: issue`: two-column newsletter with masthead cover, auto-built Inside index, key-marks table, section decks, column breaks, column-width / wide exhibits with subtitles, compact fine-print disclosures; `exhibitkit demo --layout issue`.
- Page design: asymmetric text block with a margin column; exhibits span both; `keynumber`, `aside`, `pullquote` and `closing` devices; contents page with chapter and exhibit lists; part-opener pages; chapter numerals; zebra tables; cover with hero figure and key-number strip.
- Document model: Markdown + YAML front matter; fenced-div devices `exhibit`, `box`, `callout`, `warning`; `#ex-` cross-references.
- Lua filter renders exhibits as numbered floats with caption-above and source-beneath; tables as booktabs tabulars.
- Three themes (`navy`, `foghnan`, `claret`) with fontconfig font fallback to TeX Gyre and a validated chart palette.
- Palette validator: OKLab lightness/chroma, adjacent-pair distance for normal vision and three simulated CVDs, WCAG contrast.
- Disclosure library (11 sections) with variable substitution; cover conflict box and footer are non-optional.
- `exhibitkit check`: house rules on the pandoc AST, including the Sharpe-basis rule.
- `exhibitkit demo`: synthetic figures + document, builds in every theme; used by CI.
