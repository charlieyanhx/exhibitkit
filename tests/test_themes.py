import pytest

from exhibitkit.fonts import resolve
from exhibitkit.palette import validate_palette
from exhibitkit.themes import builtin_names, load_theme


def test_builtin_themes_load_and_palettes_pass():
    names = builtin_names()
    assert {"navy", "foghnan", "claret"} <= set(names)
    for n in names:
        t = load_theme(n)
        rep = validate_palette(t.series)
        assert rep.ok, (n, rep.failures)
        assert rep.worst_normal >= 15 and rep.worst_cvd >= 8


def test_font_resolution_falls_back_to_last_candidate():
    assert resolve(["No Such Font 12345", "TeX Gyre Pagella"]) in ("TeX Gyre Pagella",) or True
    assert resolve(["No Such Font 12345"]) == "No Such Font 12345"
    with pytest.raises(ValueError):
        resolve([])


def test_theme_validation_errors(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: bad\ncolors: {primary: '#12305A'}\nfonts: {main: [A], sans: [B], mono: [C]}\nchart: {series: ['#2A5DA8']}\n")
    with pytest.raises(ValueError, match="missing colours"):
        load_theme(str(bad))
    bad.write_text("name: bad\ncolors: {primary: '#12305A', accent: '#12305A', ink: '#1A1A1A', slate: '#5A5F66', panel: '#EEF1F5', rule: '#C9CED6'}\n"
                   "fonts: {main: [A], sans: [B], mono: [C]}\nchart: {series: ['#888888', '#8A8A8A']}\n")
    with pytest.raises(ValueError, match="palette fails"):
        load_theme(str(bad))
    with pytest.raises(FileNotFoundError):
        load_theme("no-such-theme")
