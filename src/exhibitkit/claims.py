"""Claims a document commits to, declared once in the front matter and marked once in the text.

Front matter:
    claims:
      - {id: sw001.cpi_through, metric: table.change, args: {...}, op: "<", value: 0, p: 0.70, resolve: 2026-05-12}
Body:
    ::: {.claim id="sw001.cpi_through"}
    Through Tuesday's print the put wing cheapens.
    :::

The body carries the sentence, the front matter the test; `exhibitkit claims doc.md` joins them into the
record claimkeeper ingests (id, report, made, statement, metric, args, op, value, p, resolve). `check` errors
on a claim div without a spec, a spec without a div, or a spec missing a field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .check import _stringify, _walk
from .document import Document, parse
from .pandoc import to_ast

REQUIRED = ("id", "metric", "op", "value", "resolve")


@dataclass
class ClaimText:
    id: str
    statement: str


def claim_texts(ast: dict) -> list[ClaimText]:
    out: list[ClaimText] = []

    def visit(n):
        if n.get("t") == "Div":
            (ident, classes, kvs), blocks = n["c"]
            if "claim" in classes:
                cid = dict(kvs).get("id") or ident
                out.append(ClaimText(cid, " ".join(_stringify(b.get("c")) for b in blocks if b.get("t") in ("Para", "Plain")).strip()))
    _walk(ast.get("blocks", []), visit)
    return out


def problems(doc: Document, ast: dict) -> list[str]:
    specs = {str(s.get("id")): s for s in (doc.meta.get("claims") or [])}
    texts = claim_texts(ast)
    errs = []
    for t in texts:
        if not t.id:
            errs.append("claim div without an id")
        elif t.id not in specs:
            errs.append(f"claim {t.id!r} is marked in the text but has no spec in front matter 'claims'")
        elif not t.statement:
            errs.append(f"claim {t.id!r} has no statement text")
    seen = [t.id for t in texts]
    for cid, s in specs.items():
        if cid not in seen:
            errs.append(f"claim {cid!r} is in front matter but never marked in the text")
        missing = [k for k in REQUIRED if k not in s]
        if missing:
            errs.append(f"claim {cid!r} spec is missing {', '.join(missing)}")
    if len(seen) != len(set(seen)):
        errs.append("a claim id is marked more than once in the text")
    return errs


def records(path: str | Path) -> list[dict]:
    """The claim records for one document, ready for `claimkeeper ingest`."""
    doc = parse(path)
    ast = to_ast(doc.body)
    errs = problems(doc, ast)
    if errs:
        raise ValueError("; ".join(errs))
    specs = {str(s["id"]): s for s in (doc.meta.get("claims") or [])}
    m = doc.meta
    report = str(m.get("masthead", "") + (" " + str(m["issue"]) if m.get("issue") else "")).strip() or doc.title
    made = str(m.get("date"))
    out = []
    for t in claim_texts(ast):
        s = specs[t.id]
        args = {k: (v.isoformat() if isinstance(v, (date, datetime)) else v) for k, v in (s.get("args") or {}).items()}  # YAML reads bare dates as date objects
        rec = {"id": t.id, "report": report, "made": made, "statement": t.statement, "metric": s["metric"], "args": args,
               "op": s["op"], "value": s["value"], "resolve": str(s["resolve"])}
        if s.get("p") is not None:
            rec["p"] = s["p"]
        out.append(rec)
    return out


def write(path: str | Path, out: str | Path) -> int:
    recs = records(path)
    Path(out).write_text(json.dumps({"claims": recs}, indent=1, default=str))
    return len(recs)
