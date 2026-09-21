"""House rules, enforced on the pandoc AST rather than by regex on text.

Errors (exit 1): exhibit without title/source, bad or duplicate id, dangling #ex- link, missing image
file, missing front-matter keys, unloadable theme, unknown disclosure section, and — when
rules.sharpe_basis is on — a paragraph that quotes a Sharpe *number* ("Sharpe of 1.2", "Sharpe ratio by 2.1x",
"a 1.4 Sharpe") without a basis word.
Warnings: unreferenced exhibit, more than six takeaways, image wider than the line."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import disclosures as disc
from . import pandoc
from .document import Document, parse
from .themes import load_theme

BASIS_WORDS = ["mid", "cross", "mtm", "full calendar", "hypothetical", "simulated", "backtest", "live", "mark", "marked", "marking", "exit-day"]
_SHARPE_NUM = re.compile(r"sharpe(\s+ratio)?(\s+[a-z]+){0,3}\s+[+\-−]?\d|[+\-−]?\d[\d.]*\s+sharpe", re.I)


@dataclass
class Exhibit:
    id: str
    title: str
    source: str
    kind: str  # "figure" | "table" | "other"


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    exhibits: list[Exhibit] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _stringify(node) -> str:
    if isinstance(node, dict):
        t, c = node.get("t"), node.get("c")
        if t == "Str":
            return c
        if t in ("Space", "SoftBreak", "LineBreak"):
            return " "
        if t in ("Emph", "Strong", "Underline", "Strikeout", "SmallCaps", "Span"):
            return _stringify(c[-1])
        if t == "Link":
            return _stringify(c[1])
        if t in ("Code", "Math"):
            return c[-1]
        return _stringify(c) if c is not None else ""
    if isinstance(node, list):
        return "".join(_stringify(x) for x in node)
    return ""


def _walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values():
            _walk(v, fn)
    elif isinstance(node, list):
        for x in node:
            _walk(x, fn)


def _sharpe_ok(text: str, words: list[str]) -> bool:
    low = text.lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words)


def _tables(blocks) -> list[dict]:
    out: list[dict] = []
    _walk(blocks, lambda x: out.append(x) if x.get("t") == "Table" else None)
    return out


def check_document(doc: Document) -> CheckResult:
    res = CheckResult()
    res.errors.extend(doc.problems)
    m = doc.meta
    layout = str(m.get("layout", "primer"))
    if "theme" in m:
        try:
            load_theme(str(m["theme"]))
        except Exception as e:  # noqa: BLE001 - surface any theme problem as a check error
            res.errors.append(f"theme: {e}")
    d = m.get("disclosures") or {}
    for s in d.get("sections") or []:
        if s not in disc.library_names():
            res.errors.append(f"unknown disclosure section {s!r}")
    if len(m.get("takeaways") or []) > 6:
        res.warnings.append("more than six takeaways; the cover box will crowd the page")
    ast = pandoc.to_ast(doc.body)
    ids: dict[str, int] = {}
    refs: set[str] = set()
    rules = m.get("rules") or {}
    words = list(rules.get("sharpe_basis_words") or BASIS_WORDS)

    def visit(n):
        t, c = n.get("t"), n.get("c")
        if t == "Div":
            (ident, classes, kvs), blocks = c
            if "exhibit" in classes:
                a = dict(kvs)
                kind = "other"
                kinds = set()
                _walk(blocks, lambda x: kinds.add(x.get("t")) if x.get("t") in ("Image", "Table") else None)
                kind = "figure" if "Image" in kinds else ("table" if "Table" in kinds else "other")
                if not ident.startswith("ex-"):
                    res.errors.append(f"exhibit id {ident!r} must start with 'ex-'")
                ids[ident] = ids.get(ident, 0) + 1
                if not a.get("title"):
                    res.errors.append(f"exhibit {ident!r} has no title")
                if not a.get("source"):
                    res.errors.append(f"exhibit {ident!r} has no source line")
                res.exhibits.append(Exhibit(ident, a.get("title", ""), a.get("source", ""), kind))
                if kind == "table" and layout == "issue" and a.get("wide") != "true":
                    ncols = max((len(x["c"][2]) for x in _tables(blocks)), default=0)  # Table = [attr, caption, colspecs, head, bodies, foot]
                    if ncols >= 6:
                        res.warnings.append(f"exhibit {ident!r} is a {ncols}-column table in a column; it will overflow — add wide=\"true\"")
        elif t == "Link":
            target = c[2][0]
            if target.startswith("#ex-"):
                refs.add(target[1:])
        elif t == "Image":
            attrs, _, (src, _) = c
            p = (doc.path.parent / src)
            if not src.startswith(("http://", "https://")) and not p.exists():
                res.errors.append(f"image not found: {src}")
            w = dict(attrs[2]).get("width", "")
            if w.endswith("%") and float(w[:-1]) > 100:
                res.warnings.append(f"image {src} is wider than the line ({w})")
        elif t in ("Para", "Plain") and rules.get("sharpe_basis"):
            text = _stringify(c)
            if _SHARPE_NUM.search(text) and not _sharpe_ok(text, words):
                res.errors.append("Sharpe without a basis label: " + text[:90].strip() + ("…" if len(text) > 90 else ""))

    _walk(ast.get("blocks", []), visit)
    from .claims import problems as _claim_problems  # local import: claims imports helpers from this module

    res.errors.extend(_claim_problems(doc, ast))
    for i, n in ids.items():
        if n > 1:
            res.errors.append(f"duplicate exhibit id {i!r}")
    for r in sorted(refs - set(ids)):
        res.errors.append(f"link to unknown exhibit {r!r}")
    for i in ids:
        if i not in refs:
            res.warnings.append(f"exhibit {i!r} is never referenced from the text")
    return res


def check(src: str | Path) -> CheckResult:
    return check_document(parse(Path(src)))
