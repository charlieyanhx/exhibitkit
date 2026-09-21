from conftest import MINIMAL, needs_pandoc

from exhibitkit.check import check


@needs_pandoc
def test_minimal_document_passes(doc_dir):
    r = check(doc_dir / "doc.md")
    assert r.ok, r.errors
    assert [e.id for e in r.exhibits] == ["ex-a"] and r.exhibits[0].kind == "figure"
    assert r.warnings == []


@needs_pandoc
def test_rules_fire(doc_dir):
    bad = MINIMAL.replace('source="S"', "").replace("#ex-a title", "#fig-a title").replace("figs/a.pdf", "figs/missing.pdf")
    bad = bad.replace("at mid fills", "").replace("sections: [certification, warranty]", "sections: [certification, nope]")
    (doc_dir / "doc.md").write_text(bad)
    r = check(doc_dir / "doc.md")
    msgs = " | ".join(r.errors)
    assert "has no source line" in msgs
    assert "must start with 'ex-'" in msgs
    assert "image not found: figs/missing.pdf" in msgs
    assert "unknown exhibit 'ex-a'" in msgs
    assert "Sharpe without a basis label" in msgs
    assert "unknown disclosure section 'nope'" in msgs


@needs_pandoc
def test_duplicate_and_unreferenced(doc_dir):
    md = MINIMAL + '\n::: {.exhibit #ex-a title="B" source="S"}\ntext\n:::\n\n::: {.exhibit #ex-c title="C" source="S"}\ntext\n:::\n'
    (doc_dir / "doc.md").write_text(md)
    r = check(doc_dir / "doc.md")
    assert any("duplicate exhibit id 'ex-a'" in e for e in r.errors)
    assert any("'ex-c' is never referenced" in w for w in r.warnings)


@needs_pandoc
def test_seven_takeaways_warns(doc_dir):
    md = MINIMAL.replace('takeaways: ["one ([](#ex-a))"]', "takeaways: [a, b, c, d, e, f, g]")
    (doc_dir / "doc.md").write_text(md)
    r = check(doc_dir / "doc.md")
    assert any("six takeaways" in w for w in r.warnings)


@needs_pandoc
def test_sharpe_rule_needs_a_number_beside_the_word(doc_dir):
    from conftest import MINIMAL

    ok_uses = ("the Sharpe nearly doubles", "a Sharpe above three is an audit trigger", "−59% of net, so the Sharpe is the wrong lens")
    for phrase in ok_uses:
        (doc_dir / "doc.md").write_text(MINIMAL.replace("with a Sharpe of 1.0 at mid fills", phrase))
        assert check(doc_dir / "doc.md").ok, phrase
    for phrase in ("a Sharpe of 8.7", "a Sharpe ratio by 2.1 to 2.4", "a 1.4 Sharpe"):
        (doc_dir / "doc.md").write_text(MINIMAL.replace("with a Sharpe of 1.0 at mid fills", phrase))
        assert not check(doc_dir / "doc.md").ok, phrase
