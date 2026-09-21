import pytest

from exhibitkit import disclosures as d


def test_library_and_rendering_substitutes_variables():
    names = d.library_names()
    assert set(d.DEFAULT_SECTIONS) <= set(names)
    md = d.render_markdown(["certification", "distribution"], {"author": "Jane Q", "year": "2026"}, extra=[{"title": "X", "text": "by $author"}])
    assert "I, Jane Q, certify" in md and "© 2026 Jane Q" in md
    assert "## 3. X\n\nby Jane Q" in md
    assert md.count("## ") == 3


def test_unknown_section_raises():
    with pytest.raises(KeyError, match="unknown disclosure section"):
        d.render_markdown(["no_such_section"], {})


def test_conflict_default_mentions_appendix():
    txt = d.render_conflict(None, {"author": "Jane Q", "nature": "a memo"})
    assert txt.startswith("Jane Q trades for the author") and "Disclosure Appendix" in txt and "a memo" in txt
    both = d.render_conflict("Custom sentence for $author.", {"author": "J"})
    assert both.startswith("J trades") and both.endswith("Custom sentence for J.")  # appended, never substituted


def test_sentence_initial_entity_is_capitalised():
    md = d.render_markdown(["nature"], {"entity": "the author", "nature": "a memo"})
    assert "The author accepts no responsibility" in md and "a memo." in md


def test_resolve_sections_adds_core_and_keeps_order():
    assert d.resolve_sections(None) == d.DEFAULT_SECTIONS
    assert d.resolve_sections([]) == d.CORE_SECTIONS
    got = d.resolve_sections(["hypothetical", "options_risk"])
    assert set(d.CORE_SECTIONS) <= set(got) and got.index("options_risk") < got.index("hypothetical")
    with pytest.raises(KeyError, match="unknown disclosure section"):
        d.resolve_sections(["nope"])
