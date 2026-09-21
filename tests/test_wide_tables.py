"""A many-column table inside a column exhibit of the issue layout overflows; check must say so."""
from pathlib import Path

from exhibitkit.check import check

DOC = """---
layout: issue
title: T
date: 2026-01-01
theme: navy
authors: [{name: A}]
---

## Section

Text [](#ex-a) and [](#ex-b).

::: {.exhibit #ex-a title="Wide" source="s." cols="lrrrrrr"}
| a | b | c | d | e | f | g |
|---|---|---|---|---|---|---|
| 1 | 2 | 3 | 4 | 5 | 6 | 7 |
:::

::: {.exhibit #ex-b title="Narrow" source="s." cols="lrr"}
| a | b | c |
|---|---|---|
| 1 | 2 | 3 |
:::
"""


def test_many_column_table_in_a_column_warns(tmp_path: Path) -> None:
    p = tmp_path / "d.md"
    p.write_text(DOC)
    res = check(p)
    assert res.ok
    assert any("ex-a" in w and "wide" in w for w in res.warnings)
    assert not any("ex-b" in w for w in res.warnings)


def test_wide_table_does_not_warn(tmp_path: Path) -> None:
    p = tmp_path / "d.md"
    p.write_text(DOC.replace('cols="lrrrrrr"}', 'cols="lrrrrrr" wide="true"}'))
    res = check(p)
    assert not any("ex-a" in w for w in res.warnings)
