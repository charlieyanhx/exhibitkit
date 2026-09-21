"""Assemble and compile a document: pandoc renders prose, Python owns the chrome.

build() returns a BuildResult; LaTeX errors fail the build (first five quoted), overfull boxes over
10pt are warnings with their line numbers. Nothing is cached: a build is a pure function of the
Markdown, the theme and the installed fonts, and it says which fonts it used."""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from string import Template

from . import disclosures as disc
from . import pandoc
from .document import Document, parse
from .themes import Theme, load_theme

OVERFULL_PT = 10.0


class BuildError(RuntimeError):
    pass


@dataclass
class BuildResult:
    pdf: Path
    tex: Path | None
    pages: int
    fonts: dict[str, str]
    theme: str
    warnings: list[str] = field(default_factory=list)


def _template(name: str) -> Template:
    return Template((resources.files("exhibitkit") / "templates" / name).read_text())


def _brandfont(theme: Theme) -> str:
    """fontspec line for the wordmark face: the shipped file if the theme names one, else the first installed candidate."""
    b = theme.brand
    if not b:
        return r"\newfontfamily\brandfont{" + theme.resolved_fonts.get("sans", "TeX Gyre Heros") + "}"
    f = b.get("font_file")
    if f:
        path = Path(str(resources.files("exhibitkit") / f))
        if path.exists():
            return r"\newfontfamily\brandfont[Path=%s/,Extension=%s]{%s}" % (path.parent.as_posix(), path.suffix, path.stem)
    from .fonts import resolve

    return r"\newfontfamily\brandfont{" + resolve(list(b.get("font") or ["TeX Gyre Bonum"])) + "}"


def _band(doc: Document, theme: Theme) -> str:
    """Cover band: the theme's wordmark with the document's series on the right; a plain band when the theme has no brand."""
    series = pandoc.inline_latex(str(doc.meta.get("series", "Research")))
    if theme.brand.get("name"):
        return r"\brandband{%s}{%s}" % (pandoc.inline_latex(str(theme.brand["name"])), series)
    return r"\plainband{%s}{%s}" % (series, doc.date_text)


def _credit_line(doc: Document, theme: Theme, style: str = "cover") -> str:
    text = str(doc.meta.get("credit", theme.credit) or "").strip()
    if not text:
        return ""
    tex = pandoc.inline_latex(text)
    if style == "cover":
        return "{\\noindent\\sffamily\\scriptsize\\color{slate}%s\\par}\\vspace{6pt}" % tex
    return "\\par\\vspace{6pt}{\\noindent\\sffamily\\scriptsize\\color{slate}%s\\par}" % tex


def _cover(doc: Document, theme: Theme) -> str:
    m = doc.meta
    variables = _variables(doc)
    take = m.get("takeaways") or []
    takeaways = ""
    if take:
        md = "\n".join(f"- {t}" for t in take)
        takeaways = "\\begin{keybox}{Key takeaways}\n" + pandoc.to_latex(md, resource_path=doc.path.parent) + "\\end{keybox}"
    hero = ""
    if m.get("cover_figure"):
        cap = pandoc.inline_latex(str(m.get("cover_caption", ""))) if m.get("cover_caption") else ""
        hero = ("\\includegraphics[width=\\linewidth]{%s}" % str(m["cover_figure"])) + (
            "\\par\\vspace{3pt}{\\sffamily\\scriptsize\\color{slate}%s\\par}" % cap if cap else "")
    keynumbers = ""
    kn = m.get("keynumbers") or []
    if kn:
        w = 0.98 / len(kn)
        cells = []
        for k in kn:
            cells.append("\\begin{minipage}[t]{%.3f\\exwidth}\\RaggedRight{\\sffamily\\bfseries\\fontsize{20}{22}\\selectfont\\color{accent}%s\\par}\\vspace{2pt}{\\sffamily\\scriptsize\\color{slate}%s\\par}\\end{minipage}"
                         % (w, pandoc.inline_latex(str(k.get("value", ""))), pandoc.inline_latex(str(k.get("label", "")))))
        keynumbers = ("\\vspace{7pt}\\noindent{\\color{rulec}\\hrule height 0.5pt}\\vspace{6pt}\\noindent" + "\\hfill".join(cells)
                      + "\\par\\vspace{6pt}{\\color{rulec}\\hrule height 0.5pt}\\vspace{2pt}")
    side: list[str] = []
    for a in doc.authors:
        lines = [f"\\textbf{{\\color{{primary}}{pandoc.inline_latex(a.get('name', ''))}}}"]
        if a.get("role"):
            lines.append(pandoc.inline_latex(str(a["role"])))
        if a.get("contact"):
            c = str(a["contact"])
            url = c if c.startswith("http") else "https://" + c
            lines.append(f"\\href{{{url}}}{{{pandoc.inline_latex(c)}}}")
        side.append("\\\\ ".join(lines))
    for blk in m.get("sidebar") or []:
        side.append(f"\\textbf{{\\color{{primary}}{pandoc.inline_latex(str(blk.get('title', '')))}}}\\\\ "
                    + pandoc.inline_latex(str(blk.get("text", ""))))
    sidebar = "\n\\vspace{10pt}\n\n".join(side)
    conflict = pandoc.inline_latex(disc.render_conflict((m.get("disclosures") or {}).get("conflict"), variables))
    return _template("cover.tex").substitute(
        series=pandoc.inline_latex(str(m.get("series", "RESEARCH"))), date=doc.date_text,
        title=pandoc.inline_latex(doc.title), subtitle=pandoc.inline_latex(str(m.get("subtitle", ""))),
        takeaways=takeaways, sidebar=sidebar, conflict=conflict, hero=hero, keynumbers=keynumbers, credit=_credit_line(doc, theme),
        band=_band(doc, theme))


def _variables(doc: Document) -> dict[str, str]:
    v = dict(disc.DEFAULT_VARIABLES)
    v.update({"author": doc.author_names or "the author", "date": doc.date_text, "year": doc.year, "title": doc.title})
    v.update({k: str(x) for k, x in ((doc.meta.get("disclosures") or {}).get("variables") or {}).items()})
    return v


def _appendix(doc: Document, theme: Theme) -> str:
    d = doc.meta.get("disclosures") or {}
    sections = disc.resolve_sections(list(d["sections"]) if "sections" in d else None)
    if d.get("compact"):
        if str(doc.meta.get("layout", "primer")) == "issue":
            return "\n\\end{document}\n"  # rendered inline as fine print at the end of the last section
        md = disc.render_markdown(sections, _variables(doc), d.get("extra"), compact=True)
        return _template("appendix_compact.tex").substitute(disclosures=pandoc.to_latex(md, mode="appendix"), credit=_credit_line(doc, theme, "end"))
    md = disc.render_markdown(sections, _variables(doc), d.get("extra"))
    return _template("appendix.tex").substitute(disclosures=pandoc.to_latex(md, mode="appendix"), credit=_credit_line(doc, theme, "end"))


_SECTION = re.compile(r"^## +(.+?)\s*$", re.M)
_DECK = re.compile(r"^::: *\{\.deck\}\s*\n(.*?)\n:::", re.M | re.S)


def split_lead(body: str) -> tuple[str, str]:
    """Issue layout: everything before the first H2 is the cover lead; the rest is the sectioned body."""
    m = _SECTION.search(body)
    return (body, "") if not m else (body[: m.start()], body[m.start():])


def short_deck(deck: str, limit: int = 72) -> str:
    """The Inside index takes one clause of a deck: up to the first comma, semicolon or dash, capped at `limit`
    characters on a word boundary."""
    d = re.split(r",|;|\s[—–-]\s", deck.strip(), maxsplit=1)[0].strip()
    if len(d) > limit:
        d = d[:limit].rsplit(" ", 1)[0]
    return d


def inside_entries(sections_md: str) -> list[tuple[str, str]]:
    """(title, deck) per H2, decks taken from a `::: {.deck}` div that directly follows the heading."""
    out = []
    for m in _SECTION.finditer(sections_md):
        rest = sections_md[m.end():]
        nxt = _SECTION.search(rest)
        chunk = rest[: nxt.start()] if nxt else rest
        dm = _DECK.match(chunk.lstrip("\n"))
        out.append((m.group(1).strip(), dm.group(1).strip() if dm else ""))
    return out


def _headline(doc: Document) -> str:
    """The cover headline; a ' | ' in front matter `headline` (else the title) forces the line break there."""
    text = str(doc.meta.get("headline") or doc.title)
    return "\\\\".join(pandoc.inline_latex(part.strip()) for part in text.split(" | "))


def _cover_issue(doc: Document, theme: Theme) -> str:
    m = doc.meta
    lead_md, sections_md = split_lead(doc.body)
    lead = pandoc.to_latex(lead_md, mode="lead", resource_path=doc.path.parent, layout="issue")
    inside = []
    for i, (title, deck) in enumerate(inside_entries(sections_md), 1):
        deck = short_deck(deck)
        line = ("\\noindent\\parbox[t]{\\dimexpr\\linewidth-1.6em}{\\sffamily\\small\\color{ink}\\RaggedRight %s}\\hfill"
                "\\parbox[t]{1.4em}{\\sffamily\\small\\color{slate}\\hfill\\pageref{sec:%d}}\\par") % (pandoc.inline_latex(title), i)
        if deck:
            line += "\\vspace{1pt}{\\noindent\\sffamily\\scriptsize\\color{slate}\\RaggedRight\\linespread{0.95}\\selectfont %s\\par}" % pandoc.inline_latex(deck)
        inside.append(line + "\\vspace{3pt}")
    marks = ""
    if m.get("marks"):
        rows = " \\\\\n".join("%s & %s" % (pandoc.inline_latex(str(k.get("label", ""))), pandoc.inline_latex(str(k.get("value", "")))) for k in m["marks"])
        marks = ("\\vspace{2pt}{\\noindent\\sffamily\\bfseries\\footnotesize\\color{primary}%s\\par}\\vspace{3pt}{\\color{accent}\\hrule height 0.6pt}\\vspace{3pt}\\noindent\\begin{markstable}\n%s \\\\\n\\end{markstable}"
                 % (pandoc.inline_latex(str(m.get("marks_title", "Key marks"))), rows))
    dateline = doc.date_text + ((" | " + str(m["time"])) if m.get("time") else "")
    conflict = pandoc.inline_latex(disc.render_conflict((m.get("disclosures") or {}).get("conflict"), _variables(doc)))
    standfirst = ""
    if m.get("standfirst"):
        standfirst = "\\vspace{6pt}{\\noindent\\fontsize{11.5}{15}\\selectfont\\color{slate}\\RaggedRight\\hyphenpenalty=10000 %s\\par}" % pandoc.inline_latex(str(m["standfirst"]))
    return _template("cover_issue.tex").substitute(
        band=_band(doc, theme), masthead=pandoc.inline_latex(str(m.get("masthead", doc.title))),
        tagline=pandoc.inline_latex(str(m.get("tagline", ""))), standfirst=standfirst,
        dateline=dateline, issue=pandoc.inline_latex(str(m.get("issue", ""))), headline=_headline(doc),
        lead=lead, inside="\n".join(inside), marks=marks, byline=pandoc.inline_latex(str(m.get("byline", doc.author_names))),
        dataline=pandoc.inline_latex(str(m.get("dataline", ""))), conflict=conflict, credit=_credit_line(doc, theme))


GEOMETRY = {
    "primer": "letterpaper,left=0.85in,textwidth=4.95in,marginparsep=0.28in,marginparwidth=1.65in,top=0.95in,bottom=0.95in,headheight=16pt,headsep=14pt,footskip=26pt",
    "issue": "letterpaper,left=0.8in,right=0.8in,marginparsep=0pt,marginparwidth=0pt,top=0.85in,bottom=0.85in,headheight=14pt,headsep=12pt,footskip=24pt",
}


def assemble(doc: Document, theme: Theme) -> str:
    fonts = theme.resolve_fonts()
    m = doc.meta
    layout = str(m.get("layout", "primer"))
    if layout not in GEOMETRY:
        raise BuildError(f"unknown layout {layout!r}; choose one of {sorted(GEOMETRY)}")
    extras = ""
    if layout == "issue":
        extras = r"\setlist[itemize]{leftmargin=1.1em,itemsep=1pt,topsep=2pt,parsep=0pt}\setlist[enumerate]{leftmargin=1.4em,itemsep=2pt,topsep=2pt}\setlength{\parskip}{4pt}"
        if m.get("sections_new_page", True):
            extras += r"\sectionpagetrue"
    compact = bool((m.get("disclosures") or {}).get("compact"))
    pre = _template("preamble.tex").substitute(geometry=GEOMETRY[layout], ptsize="9pt" if layout == "issue" else "10pt", layoutextras=extras,
        brandfont=_brandfont(theme), c_brandink=str(theme.brand.get("ink", "#FFFFFF")).lstrip("#"),
        c_brandrule=str(theme.brand.get("rule", theme.colors["accent"])).lstrip("#"), bandheight="0.62in" if layout == "issue" else "0.68in",
        brandsize="22" if layout == "issue" else "25",
        footer_right="See the disclosures at the end of this document." if compact else "See the Disclosure Appendix for important disclosures.",
        font_main=fonts["main"], font_sans=fonts["sans"], font_mono=fonts["mono"],
        c_primary=theme.colors["primary"].lstrip("#"), c_accent=theme.colors["accent"].lstrip("#"),
        c_ink=theme.colors["ink"].lstrip("#"), c_slate=theme.colors["slate"].lstrip("#"),
        c_panel=theme.colors["panel"].lstrip("#"), c_rule=theme.colors["rule"].lstrip("#"),
        header_left=pandoc.inline_latex(str(m.get("header", (m.get("masthead", "") + " | " + m.get("issue", "")) if layout == "issue" and m.get("masthead") else doc.title))), date=doc.date_text,
        footer_left=pandoc.inline_latex(str(m.get("footer", doc.author_names))))
    graphics = "\\graphicspath{{%s/}}\n" % doc.path.parent.resolve().as_posix()
    if layout == "issue":
        _, sections_md = split_lead(doc.body)
        d = m.get("disclosures") or {}
        if d.get("compact"):
            sections = disc.resolve_sections(list(d["sections"]) if "sections" in d else None)
            md = disc.render_markdown(sections, _variables(doc), d.get("extra"), compact=True)
            credit = str(m.get("credit", theme.credit) or "").strip()
            sections_md += "\n\n::: {.fineprint}\n" + md + (("\n\n" + credit) if credit else "") + "\n:::\n"
        body = pandoc.to_latex(sections_md, mode="body", resource_path=doc.path.parent, layout="issue")
        return pre + graphics + _cover_issue(doc, theme) + body + _appendix(doc, theme)
    body = pandoc.to_latex(doc.body, mode="body", resource_path=doc.path.parent)
    contents = _template("contents.tex").template if m.get("contents", True) else ""
    return pre + graphics + _cover(doc, theme) + contents + body + _appendix(doc, theme)


def _run_engine(engine: str, tex: Path) -> str:
    for _ in range(2):
        subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=tex.parent,
                       capture_output=True, text=True)
    log = tex.with_suffix(".log")
    return log.read_text(errors="ignore") if log.exists() else ""


def build(src: str | Path, out: str | Path | None = None, theme: str | None = None, keep_tex: bool = False,
          engine: str = "xelatex") -> BuildResult:
    src = Path(src)
    doc = parse(src)
    if doc.problems:
        raise BuildError("; ".join(doc.problems))
    th = load_theme(theme or str(doc.meta["theme"]))
    pandoc.require("pandoc")
    pandoc.require(engine)
    out = Path(out) if out else src.with_suffix(".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    tex = out.with_suffix(".tex")
    tex.write_text(assemble(doc, th), encoding="utf-8")
    log = _run_engine(engine, tex)
    errors = [ln for ln in log.splitlines() if ln.startswith("!")]
    if errors or not tex.with_suffix(".pdf").exists():
        raise BuildError("LaTeX failed: " + " | ".join(errors[:5]) + f" (log: {tex.with_suffix('.log')})")
    m = re.search(r"Output written on .*\((\d+) pages?", log)
    pages = int(m.group(1)) if m else 0
    warnings = [f"overfull box {float(w):.0f}pt at line {ln}" for w, ln in
                re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\) in paragraph at lines (\d+)", log) if float(w) > OVERFULL_PT]
    for f in th.fonts:
        if th.resolved_fonts[f] == th.fonts[f][-1] and len(th.fonts[f]) > 1:
            warnings.append(f"font fallback: {f} -> {th.resolved_fonts[f]} (none of {th.fonts[f][:-1]} installed)")
    if tex.with_suffix(".pdf") != out:
        shutil.move(tex.with_suffix(".pdf"), out)
    for ext in (".aux", ".log", ".out"):
        p = tex.with_suffix(ext)
        if p.exists() and not keep_tex:
            p.unlink()
    if not keep_tex:
        tex.unlink()
    return BuildResult(pdf=out, tex=tex if keep_tex else None, pages=pages, fonts=dict(th.resolved_fonts), theme=th.name, warnings=warnings)
