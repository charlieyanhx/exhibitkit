import datetime as dt

from exhibitkit.document import parse


def test_parse_front_matter_and_date(tmp_path):
    p = tmp_path / "d.md"
    p.write_text("---\ntitle: X\ndate: 2026-09-12\ntheme: navy\nauthors: [A, {name: B}]\n---\n\nbody\n")
    d = parse(p)
    assert d.problems == []
    assert d.title == "X" and d.body.strip() == "body"
    assert isinstance(d.meta["date"], dt.date) and d.date_text == "September 12, 2026" and d.year == "2026"
    assert d.author_names == "A, B"


def test_missing_keys_and_no_front_matter(tmp_path):
    p = tmp_path / "d.md"
    p.write_text("---\ntitle: X\n---\nbody\n")
    d = parse(p)
    assert {"date", "authors", "theme"} == {m.split("'")[1] for m in d.problems}
    p.write_text("no front matter\n")
    assert parse(p).problems == ["no YAML front matter block at the top of the file"]
