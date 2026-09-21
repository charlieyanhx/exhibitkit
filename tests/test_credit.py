"""The theme credit line: carried by the theme, overridable in front matter, rendered on the cover and at the end."""
from conftest import MINIMAL, needs_pandoc

from exhibitkit.build import assemble
from exhibitkit.document import parse
from exhibitkit.themes import load_theme


def test_foghnan_theme_carries_the_credit():
    assert "Silkcodex" in load_theme("foghnan").credit
    assert load_theme("navy").credit == ""


@needs_pandoc
def test_credit_rendered_on_cover_and_at_end(doc_dir):
    (doc_dir / "doc.md").write_text(MINIMAL.replace("theme: navy", "theme: foghnan"))
    tex = assemble(parse(doc_dir / "doc.md"), load_theme("foghnan"))
    assert tex.count("Silkcodex") == 2
    (doc_dir / "doc.md").write_text(MINIMAL.replace("theme: navy", "theme: foghnan\ncredit: Custom credit line"))
    tex = assemble(parse(doc_dir / "doc.md"), load_theme("foghnan"))
    assert "Silkcodex" not in tex and tex.count("Custom credit line") == 2
    (doc_dir / "doc.md").write_text(MINIMAL)
    assert "Silkcodex" not in assemble(parse(doc_dir / "doc.md"), load_theme("navy"))
