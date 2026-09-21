"""Claims: a spec in front matter + a marked sentence in the body → one record; mismatches are check errors."""

from pathlib import Path

from exhibitkit.check import check
from exhibitkit.claims import records

DOC = """---
layout: issue
title: T
date: 2026-05-08
theme: navy
masthead: Weekly
issue: "Issue 001"
authors: [{name: A}]
claims:
  - {id: w1.a, metric: table.change, args: {file: s.csv, column: x, from: 2026-05-11, to: 2026-05-12}, op: "<", value: 0, p: 0.7, resolve: 2026-05-12}
  - {id: w1.b, metric: table.value, args: {file: s.csv, column: x, date: 2026-05-15}, op: between, value: [1, 2], resolve: 2026-05-15}
---

## Section

Text [](#ex-a).

::: {.claim id="w1.a" resolve="12 May"}
The wing cheapens through the print.
:::

::: {.claim id="w1.b"}
The wing stays in its band.
:::

::: {.exhibit #ex-a title="t" source="s." cols="lr"}
| a | b |
|---|---|
| 1 | 2 |
:::
"""


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "d.md"
    p.write_text(text)
    return p


def test_records_join_spec_and_sentence(tmp_path: Path) -> None:
    recs = records(_write(tmp_path, DOC))
    assert [r["id"] for r in recs] == ["w1.a", "w1.b"]
    a = recs[0]
    assert a["report"] == "Weekly Issue 001" and a["made"] == "2026-05-08" and a["p"] == 0.7
    assert a["statement"] == "The wing cheapens through the print." and a["args"]["from"] == "2026-05-11"
    assert "p" not in recs[1] and recs[1]["value"] == [1, 2]
    assert check(_write(tmp_path, DOC)).ok


def test_marked_without_spec_is_an_error(tmp_path: Path) -> None:
    res = check(_write(tmp_path, DOC.replace("  - {id: w1.b,", "  - {id: w1.zz,")))
    assert any("w1.b" in e and "no spec" in e for e in res.errors)
    assert any("w1.zz" in e and "never marked" in e for e in res.errors)


def test_spec_missing_fields_is_an_error(tmp_path: Path) -> None:
    res = check(_write(tmp_path, DOC.replace(', op: between, value: [1, 2], resolve: 2026-05-15', ', resolve: 2026-05-15')))
    assert any("w1.b" in e and "missing op, value" in e for e in res.errors)
