"""The theme brand block: a wordmark band on every cover, set in the shipped face when the theme names one."""
from conftest import MINIMAL, needs_pandoc

from exhibitkit.build import assemble
from exhibitkit.document import parse
from exhibitkit.themes import load_theme


def test_foghnan_brand_and_shipped_font():
    t = load_theme("foghnan")
    assert t.brand["name"] == "Fóghnan Trading" and t.brand["font_file"].endswith("AlfaSlabOne-Regular.ttf")
    from importlib import resources

    assert (resources.files("exhibitkit") / t.brand["font_file"]).is_file()
    assert load_theme("navy").brand == {}


@needs_pandoc
def test_brand_band_on_cover_and_plain_band_without_brand(doc_dir):
    (doc_dir / "doc.md").write_text(MINIMAL.replace("theme: navy", "theme: foghnan"))
    tex = assemble(parse(doc_dir / "doc.md"), load_theme("foghnan"))
    assert r"\brandband{Fóghnan Trading}" in tex and "AlfaSlabOne-Regular" in tex
    (doc_dir / "doc.md").write_text(MINIMAL)
    tex = assemble(parse(doc_dir / "doc.md"), load_theme("navy"))
    assert r"\plainband{" in tex and r"\brandband{" not in tex
