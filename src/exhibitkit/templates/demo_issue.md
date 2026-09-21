---
layout: issue
masthead: Demo Letter
series: Demo Research
issue: Issue 0
title: "A synthetic issue"
date: 2026-09-12
theme: navy
authors: [{name: A. Researcher, role: Head of Research}]
byline: "Author: A. Researcher | Demo Research"
dataline: "Data: a pseudo-random number generator with a fixed seed."
marks_title: "Key marks"
marks: [{label: "Series A", value: "1.23"}, {label: "Series B", value: "45.6"}]
footer: "Demo Research | Synthetic"
disclosures:
  compact: true
  sections: [nature, warranty]
  extra: [{title: "Synthetic data", text: "All series in this document are generated; they illustrate the layout, not any market."}]
---

**From the editor:** the lead paragraph sits on the cover beside the Inside index and the key marks.

::: {.pullquote}
A pull-quote on the cover.
:::

#### What we find

1. **A first finding.** With a number, 0.93.
2. **A second finding.** With another, 9.5 days.

## First section

::: {.deck}
The deck line under a section head.
:::

### Left column

#### Latest datapoints

- A bullet.
- Another bullet.

::: {.exhibit #ex-a title="A synthetic smile in two regimes" subtitle="Vol points, synthetic" source="Synthetic data, exhibitkit demo"}
![](figs/smile.pdf)
:::

::: {.colbreak}
:::

### Right column

Text in the right column referencing [](#ex-a) and [](#ex-b).

::: {.exhibit #ex-b title="A table in a column" source="Synthetic" cols="lrr"}
| Line | Value | n |
|---|---|---|
| One | 1.20 | 10 |
| Two | 0.30 | 20 |
:::

## Second section

::: {.deck}
Another deck.
:::

Body text flows in two columns; a wide exhibit breaks them.

::: {.exhibit #ex-w title="A wide exhibit" source="Synthetic data, exhibitkit demo" wide=true width=0.7}
![](figs/series.pdf)
:::

Text resumes in two columns after the wide exhibit, and the compact disclosures follow as fine print at the end.
