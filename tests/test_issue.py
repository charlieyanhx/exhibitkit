"""The issue layout: two-column sections with decks, column breaks, column-width and wide exhibits,
the cover's Inside index, and compact disclosures rendered inline."""
import pytest
from conftest import needs_pandoc, needs_tex

from exhibitkit import pandoc
from exhibitkit.build import assemble, build, inside_entries, short_deck, split_lead
from exhibitkit.demo import make_figures, write_document
from exhibitkit.document import parse
from exhibitkit.themes import load_theme

SNIP = """Lead text.

## First section

::: {.deck}
The deck line.
:::

#### Latest datapoints

- one

::: {.exhibit #ex-a title="Chart: units" source="S" subtitle="Index"}
![](fig.pdf)
:::

::: {.colbreak}
:::

Right column.

::: {.exhibit #ex-w title="Wide one" source="S" wide=true}
![](fig.pdf)
:::

## Second section

Text.
"""


def test_split_lead_and_inside_entries():
    lead, sections = split_lead(SNIP)
    assert lead.strip() == "Lead text." and sections.startswith("## First section")
    assert inside_entries(sections) == [("First section", "The deck line."), ("Second section", "")]


@needs_pandoc
def test_issue_mode_groups_sections_into_columns():
    tex = pandoc.to_latex(SNIP, mode="body", layout="issue")
    assert r"\issuesection{First section}{The deck line.}" in tex and r"\issuesection{Second section}{}" in tex
    assert tex.count(r"\begin{multicols}{2}") == 3 and tex.count(r"\end{multicols}") == 3
    assert r"\caplabel{Latest datapoints}" in tex and r"\columnbreak" in tex
    assert r"\begin{exhibitcol}[Chart]{Chart: units}\label{ex-a}" in tex and r"\exsubtitle{Index}" in tex
    assert r"\end{multicols}" + "\n\n" + r"\begin{exhibitfixed}[]{Wide one}" in tex
    assert "issuedeck" not in tex


@needs_pandoc
def test_lead_mode_has_no_columns():
    assert "multicols" not in pandoc.to_latex("Lead with [](#ex-a).", mode="lead", layout="issue")


@needs_pandoc
def test_issue_assemble_has_masthead_inside_marks_and_fineprint(tmp_path):
    md = write_document(tmp_path, "navy", layout="issue")
    make_figures(tmp_path / "figs", "navy")
    tex = assemble(parse(md), load_theme("navy"))
    for s in (r"\documentclass[9pt]{extarticle}", "Demo Letter", r"\begin{insidebox}", r"\pageref{sec:1}", r"\begin{markstable}",
              r"\sectionpagetrue", r"\begingroup\scriptsize\color{slate}", "Synthetic data", r"\end{document}"):
        assert s in tex, s
    assert r"\partopen{Disclosure Appendix}" not in tex


@needs_tex
def test_issue_demo_builds(tmp_path):
    pytest.importorskip("matplotlib")
    md = write_document(tmp_path, "foghnan", layout="issue")
    make_figures(tmp_path / "figs", "foghnan")
    r = build(md, tmp_path / "out.pdf")
    assert r.pdf.exists() and 2 <= r.pages <= 5, r.pages


@needs_pandoc
def test_core_disclosures_cannot_be_removed(tmp_path):
    p = tmp_path / "d.md"
    p.write_text("---\ntitle: T\ndate: 2026-09-12\ntheme: navy\nauthors: [A]\ndisclosures: {sections: [], compact: true}\n---\n\n## S\n\ntext\n")
    tex = assemble(parse(p), load_theme("navy"))
    for phrase in ("No warranty", "Conflicts of interest", "No affiliation", "Distribution and intellectual property", "forward-looking"):
        assert phrase in tex, phrase
    assert "Options risk" not in tex  # optional sections stay optional


def test_short_deck_takes_one_clause():
    assert short_deck("The deck line.") == "The deck line."
    assert short_deck("Oil moves real yields, equities fear them; the mapping changed") == "Oil moves real yields"
    assert short_deck("A very long deck without punctuation that keeps going well past the limit of seventy two characters") == "A very long deck without punctuation that keeps going well past the"
