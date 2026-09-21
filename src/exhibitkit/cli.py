"""exhibitkit CLI: build, check, init, themes, demo."""
from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .build import BuildError, build
from .check import check
from .pandoc import ToolMissing
from .themes import builtin_names, load_theme


def _build(a) -> int:
    try:
        r = build(a.src, a.out, theme=a.theme, keep_tex=a.keep_tex, engine=a.engine)
    except (BuildError, ToolMissing, FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{r.pdf}  ({r.pages} pages, theme {r.theme}, fonts {r.fonts['main']} / {r.fonts['sans']})")
    for w in r.warnings:
        print(f"warning: {w}")
    return 0


def _claims(a) -> int:
    from .claims import write

    out = a.out or str(Path(a.src).with_suffix(".claims.json"))
    try:
        n = write(a.src, out)
    except (ValueError, ToolMissing, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{n} claim(s) -> {out}")
    return 0


def _check(a) -> int:
    try:
        r = check(a.src)
    except (ToolMissing, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for e in r.errors:
        print(f"error: {e}")
    for w in r.warnings:
        print(f"warning: {w}")
    print(f"{len(r.exhibits)} exhibits, {len(r.errors)} errors, {len(r.warnings)} warnings")
    return 0 if r.ok else 1


def _init(a) -> int:
    dst = Path(a.path)
    if dst.exists() and any(dst.iterdir()):
        print(f"error: {dst} exists and is not empty", file=sys.stderr)
        return 1
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "figs").mkdir()
    src = (resources.files("exhibitkit") / "templates" / "demo.md").read_text()
    (dst / f"{dst.name}.md").write_text(src.replace("theme: navy", f"theme: {a.theme}"), encoding="utf-8")
    print(f"scaffolded {dst}/{dst.name}.md — figures go in {dst}/figs; run `exhibitkit demo` to see the figures it expects")
    return 0


def _themes(a) -> int:
    for n in builtin_names():
        t = load_theme(n)
        fonts = t.resolve_fonts()
        print(f"{n:10s} {t.colors['primary']}  series {' '.join(t.series)}  fonts {fonts['main']} / {fonts['sans']}  — {t.description}")
    return 0


def _demo(a) -> int:
    from .demo import make_figures, write_document

    out = Path(a.out)
    try:
        make_figures(out / "figs", a.theme)
    except ImportError:
        print("error: the demo needs matplotlib (pip install 'exhibitkit[charts]')", file=sys.stderr)
        return 1
    md = write_document(out, a.theme, a.layout)
    r = check(md)
    if not r.ok:
        print("\n".join("error: " + e for e in r.errors), file=sys.stderr)
        return 1
    ns = argparse.Namespace(src=md, out=out / "demo.pdf", theme=None, keep_tex=a.keep_tex, engine=a.engine)
    return _build(ns)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="exhibitkit", description="Sell-side-style research documents from Markdown.")
    p.add_argument("--version", action="version", version=f"exhibitkit {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build a PDF from a Markdown document")
    b.add_argument("src")
    b.add_argument("-o", "--out")
    b.add_argument("--theme", help="override the front-matter theme (name or path)")
    b.add_argument("--keep-tex", action="store_true")
    b.add_argument("--engine", default="xelatex")
    b.set_defaults(fn=_build)
    c = sub.add_parser("check", help="enforce the house rules; exit 1 on any error")
    c.add_argument("src")
    c.set_defaults(fn=_check)
    i = sub.add_parser("init", help="scaffold a new document directory")
    i.add_argument("path")
    i.add_argument("--theme", default="navy")
    i.set_defaults(fn=_init)
    k = sub.add_parser("claims", help="extract the document's claims (front matter specs + marked sentences) as JSON for claimkeeper")
    k.add_argument("src")
    k.add_argument("-o", "--out", default=None, help="output JSON (default: <src>.claims.json)")
    k.set_defaults(fn=_claims)
    t = sub.add_parser("themes", help="list built-in themes with their resolved fonts")
    t.set_defaults(fn=_themes)
    d = sub.add_parser("demo", help="generate synthetic figures + document and build them")
    d.add_argument("--out", default="exhibitkit-demo")
    d.add_argument("--theme", default="navy")
    d.add_argument("--layout", default="primer", choices=["primer", "issue"])
    d.add_argument("--keep-tex", action="store_true")
    d.add_argument("--engine", default="xelatex")
    d.set_defaults(fn=_demo)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())



