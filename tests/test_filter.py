"""The Lua filter, exercised through pandoc: every structural device maps to its LaTeX environment."""
from conftest import needs_pandoc

from exhibitkit import pandoc

SNIPPET = """# Part 1 — What it is

## 2. Chapter

### Sub

::: {.box title="In this chapter"}
- a
:::

See [](#ex-a) and [the table](#ex-b). 5% & more.

::: {.exhibit #ex-a title="The *smile* & co" source="Src" note="n = 3" width=0.8}
![](fig.pdf)
:::

::: {.exhibit #ex-b title="Tab" source="Src" cols="lrr" float=false}
| H1 | H2 | H3 |
|---|---:|---:|
| **x** | 1 | −2 |
:::

::: {.callout title="Key"}
text
:::

::: {.warning}
w
:::
"""


@needs_pandoc
def test_devices_map_to_environments():
    tex = pandoc.to_latex(SNIPPET)
    assert r"\partopen{Part 1}{What it is}" in tex
    assert r"\chapterhead{2}{Chapter}" in tex and r"\subhead{Sub}" in tex
    assert r"\begin{inthischapter}{In this chapter}" in tex
    assert r"\hyperref[ex-a]{Exhibit~\ref*{ex-a}}" in tex
    assert r"table (\hyperref[ex-b]{Exhibit~\ref*{ex-b}})" in tex
    assert r"\begin{exhibit}[]{The \emph{smile} \& co}\label{ex-a}" in tex
    assert r"width=0.8\linewidth" in tex and r"\exnote{n = 3}" in tex and r"\exsource{Src}" in tex
    assert r"\begin{exhibitfixed}[]{Tab}\label{ex-b}" in tex
    assert r"\begin{extabular}{lrr}\toprule" in tex and r"\textbf{H1} & \textbf{H2} & \textbf{H3} \\" in tex
    assert r"\midrule" in tex and r"\bottomrule\end{extabular}" in tex and "longtable" not in tex
    assert r"\begin{keybox}{Key}" in tex and r"\begin{warnbox}" in tex
    assert r"5\% \& more" in tex


@needs_pandoc
def test_appendix_mode_demotes_h2():
    tex = pandoc.to_latex("## 1. Section\n\ntext\n", mode="appendix")
    assert r"\subhead{1. Section}" in tex and "chapterhead" not in tex


@needs_pandoc
def test_inferred_alignment_and_default_width():
    tex = pandoc.to_latex("::: {.exhibit #ex-t title=T source=S}\n| a | b |\n|:--|--:|\n| 1 | 2 |\n:::\n")
    assert r"\begin{extabular}{lr}" in tex
    tex = pandoc.to_latex("::: {.exhibit #ex-i title=T source=S}\n![](f.pdf)\n:::\n")
    assert r"width=1\linewidth" in tex


@needs_pandoc
def test_margin_devices_and_closing():
    tex = pandoc.to_latex('::: {.pullquote}\nQuote *here*\n:::\n\n::: {.keynumber value="94 / 3 / 0.8"}\nvariance shares\n:::\n\n::: {.aside}\nsmall note\n:::\n\n::: {.closing}\nThe end.\n:::\n')
    assert r"\pullquote{Quote \emph{here}}" in tex
    assert r"\keynumber{94 / 3 / 0.8}{variance shares}" in tex
    assert r"\aside{small note}" in tex
    assert r"\begin{closingbox}" in tex and r"\end{closingbox}" in tex


@needs_pandoc
def test_short_title_for_the_exhibit_list():
    tex = pandoc.to_latex('::: {.exhibit #ex-a title="Claim here: the detail" source=S}\ntext\n:::\n')
    assert r"\begin{exhibit}[Claim here]{Claim here: the detail}" in tex
    tex = pandoc.to_latex('::: {.exhibit #ex-b title="No colon" short="Short" source=S}\ntext\n:::\n')
    assert r"\begin{exhibit}[Short]{No colon}" in tex
