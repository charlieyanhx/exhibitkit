---
title: The Demo Document
subtitle: Every device exhibitkit renders, on synthetic data
series: RESEARCH | DEMO
date: 2026-09-12
theme: navy
authors:
  - {name: A. Researcher, role: Independent research, contact: github.com/example}
cover_figure: figs/smile.pdf
cover_caption: "A synthetic smile in two regimes. Source: exhibitkit demo."
keynumbers:
  - {value: "93 / 4.5 / 1.5", label: "variance shares of three synthetic factors"}
  - {value: "0.93", label: "day-one persistence of the synthetic skew"}
  - {value: "9.5 days", label: "its half-life"}
takeaways:
  - The surface moves as three things; one of them is most of the variance ([](#ex-pca)).
  - A skew series with day-one persistence 0.93 has a half-life of about nine days ([](#ex-series)).
  - Every exhibit carries a source line and every Sharpe carries its basis — `exhibitkit check` enforces both.
sidebar:
  - {title: Scope, text: A demonstration of the document model on synthetic data. Nothing here is a result.}
  - {title: Basis conventions, text: "Every Sharpe ratio is labeled with its fill basis, marking and window."}
disclosures:
  sections: [certification, nature, hypothetical, data, no_affiliation, warranty, distribution]
  variables: {entity: the author, data_sources: "a pseudo-random number generator with a fixed seed"}
  extra:
    - {title: Synthetic data, text: "All series in this document are generated; they illustrate the layout, not any market."}
footer: A. Researcher | Independent research
rules: {sharpe_basis: true}
---

## Before we start

This document exists to show what the kit does: a cover with key takeaways and a sidebar, part
bands, numbered chapters with an opener box, exhibits that are figures or tables with a source
line beneath, cross-references that resolve to *Exhibit N*, call-outs, warnings, and a disclosure
appendix assembled from a library. All data are synthetic.

# Part 1 — Structure

A part opener carries the part's abstract: one or two paragraphs on what the chapters that follow establish. The chapters start on a fresh page.

## 1. Three numbers

::: {.box title="In this chapter"}
- A surface of many points moves as a few factors.
- Level dominates; slope and curvature are small.
:::

::: {.keynumber value="93%"}
of daily variance in the first factor, synthetic
:::

A synthetic smile is shown in [](#ex-smile). Its shape is a parabola with a tilt, which is enough
to make the point: two regimes differ in *level* far more than in *shape*.

::: {.exhibit #ex-smile title="A synthetic smile in two regimes" source="Synthetic data, `exhibitkit demo`" note="Parabola with a linear tilt; no market data."}
![](figs/smile.pdf)
:::

Decompose daily changes and the shares come out as in [](#ex-pca): one factor is most of the
variance, the second a few percent, the third about one.

::: {.exhibit #ex-pca title="Variance shares of three synthetic factors" source="Synthetic data, `exhibitkit demo`" width=0.85}
![](figs/pca.pdf)
:::

## 2. Persistence

::: {.pullquote}
A clock exit ignores the completion time; a signal exit uses it.
:::

An AR(1) series with day-one autocorrelation 0.93 reverts with a half-life of about 9.5 days
([](#ex-series)). A trade on it at mid fills shows a hypothetical Sharpe of 1.2; at full cross it
is 0.3 with an interval that includes zero. The table in [](#ex-table) states both.

::: {.exhibit #ex-series title="A mean-reverting series and its rolling mean" source="Synthetic data, `exhibitkit demo`"}
![](figs/series.pdf)
:::

::: {.exhibit #ex-table title="Hypothetical results by accounting line" source="Synthetic data; illustrative only" note="Hypothetical results; see the Disclosure Appendix." cols="lrr"}
| Line | Sharpe (annualized, MTM-daily) | 95% interval |
|---|---:|---:|
| Mid fills | 1.20 | [0.7, 1.7] |
| Full cross | 0.30 | [−0.2, 0.8] |
:::

# Part 2 — Devices

The second part exists to exercise the remaining devices: call-outs, warnings, sub-heads, and the closing box.

## 3. Call-outs and warnings

::: {.callout title="Key point"}
A call-out is for the one paragraph a reader should not miss. It is shaded, titled, and set in the
sans face.
:::

::: {.warning}
A warning is framed and bold. Use it for the sentence that must be read before any number is.
:::

::: {.closing}
Three devices, one page, no market data.
:::

### A sub-head

Sub-heads are level-three headings. Body text is set in the theme's serif face with the sans face
reserved for chrome, so the two never compete.
