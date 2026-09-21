import shutil
from pathlib import Path

import pytest

HAS_PANDOC = shutil.which("pandoc") is not None
HAS_XELATEX = shutil.which("xelatex") is not None
needs_pandoc = pytest.mark.skipif(not HAS_PANDOC, reason="pandoc not installed")
needs_tex = pytest.mark.skipif(not (HAS_PANDOC and HAS_XELATEX), reason="pandoc + xelatex not installed")


@pytest.fixture
def doc_dir(tmp_path: Path) -> Path:
    """A minimal valid document directory with one real figure file."""
    (tmp_path / "figs").mkdir()
    (tmp_path / "figs" / "a.pdf").write_bytes(b"%PDF-1.4\n%stub\n")
    (tmp_path / "doc.md").write_text(MINIMAL, encoding="utf-8")
    return tmp_path


MINIMAL = """---
title: T
subtitle: S
date: 2026-09-12
theme: navy
authors: [{name: A. Author, role: R}]
takeaways: ["one ([](#ex-a))"]
disclosures: {sections: [certification, warranty]}
rules: {sharpe_basis: true}
---

## 1. Chapter

Text referencing [](#ex-a) with a Sharpe of 1.0 at mid fills.

::: {.exhibit #ex-a title="A" source="S"}
![](figs/a.pdf)
:::
"""
