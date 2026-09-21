"""End-to-end: the demo document builds to a PDF with the expected page count, in every theme."""
import pytest
from conftest import needs_pandoc, needs_tex

from exhibitkit.build import BuildError, assemble, build
from exhibitkit.demo import make_figures, write_document
from exhibitkit.document import parse
from exhibitkit.themes import load_theme

mpl = pytest.importorskip("matplotlib")


@needs_pandoc
def test_assemble_contains_cover_body_and_appendix(tmp_path):
    md = write_document(tmp_path, "navy")
    make_figures(tmp_path / "figs", "navy")
    tex = assemble(parse(md), load_theme("navy"))
    assert tex.startswith("% exhibitkit preamble") or "\\documentclass" in tex[:300]
    for s in (r"\begin{keybox}{Key takeaways}", r"\begin{warnbox}", r"\partopen{Part 1}{Structure}", r"\begin{exhibit}[",
              r"\partopen{Disclosure Appendix}{Important information}", r"\subhead{1. Author certification}", "Synthetic data", r"\end{document}"):
        assert s in tex, s
    assert tex.count(r"\begin{exhibit}[") == 4


@needs_tex
@pytest.mark.parametrize("theme", ["navy", "foghnan", "claret"])
def test_demo_builds(tmp_path, theme):
    md = write_document(tmp_path, theme)
    make_figures(tmp_path / "figs", theme)
    r = build(md, tmp_path / "out.pdf", keep_tex=True)
    assert r.pdf.exists() and r.pdf.stat().st_size > 20_000
    assert 7 <= r.pages <= 13, r.pages
    assert r.tex is not None and r.tex.exists() and r.theme == theme
    assert all(isinstance(w, str) for w in r.warnings)


@needs_pandoc
def test_build_refuses_document_without_front_matter(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("no front matter\n")
    with pytest.raises(BuildError, match="front matter"):
        build(p, tmp_path / "x.pdf")
