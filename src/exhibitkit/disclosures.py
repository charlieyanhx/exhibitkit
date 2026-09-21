"""Disclosure library: Markdown sections with $variable placeholders, selected and ordered by the
document, rendered to LaTeX at build time. Unknown section names are an error, never silently
skipped — a document either carries its disclosures or does not build."""
from __future__ import annotations

from importlib import resources
from string import Template

DEFAULT_SECTIONS = ["certification", "nature", "options_risk", "hypothetical", "data", "conflicts",
                    "forward_looking", "third_party", "no_affiliation", "warranty", "distribution"]
# Rendered in every document, whatever the front matter says; `sections` can add to this set, never remove from it.
CORE_SECTIONS = ["nature", "conflicts", "forward_looking", "third_party", "no_affiliation", "warranty", "distribution"]


def resolve_sections(requested: list[str] | None) -> list[str]:
    """The sections a document renders: the mandatory core plus whatever it asks for, in canonical order.
    None (key absent) means the full default set."""
    if requested is None:
        return list(DEFAULT_SECTIONS)
    wanted = set(CORE_SECTIONS) | set(requested)
    unknown = [r for r in requested if r not in library_names()]
    if unknown:
        raise KeyError(f"unknown disclosure section(s) {unknown}; library: {', '.join(library_names())}")
    ordered = [s for s in DEFAULT_SECTIONS if s in wanted]
    return ordered + [s for s in requested if s not in ordered]
DEFAULT_CONFLICT = ("$author trades for $entity's own account in the instruments discussed in this document and may hold "
                    "positions in any instrument mentioned. Readers should be aware that this creates a potential conflict "
                    "of interest that could affect the objectivity of the material. This document is $nature. It is not "
                    "investment research prepared under any regulatory regime, not investment advice, and not an offer or "
                    "solicitation to buy or sell any security or derivative. All performance figures are hypothetical, "
                    "simulated results and are subject to the limitations described in the Disclosure Appendix. Options "
                    "involve risk and are not suitable for all investors. Readers should consider this document as only a "
                    "single factor in any decision and should consult a licensed adviser. For the author's certification "
                    "and other important disclosures, see the Disclosure Appendix at the end of this document.")
DEFAULT_VARIABLES = {"nature": "educational commentary", "entity": "the author",
                     "instruments": "the instruments discussed", "data_sources": "public and vendor market-data sources"}


def library_names() -> list[str]:
    root = resources.files("exhibitkit") / "disclosures"
    return sorted(p.name[:-3] for p in root.iterdir() if p.name.endswith(".md"))


def _section_md(name: str) -> str:
    f = resources.files("exhibitkit") / "disclosures" / f"{name}.md"
    if not f.is_file():
        raise KeyError(f"unknown disclosure section {name!r}; library: {', '.join(library_names())}")
    return f.read_text()


def with_capitals(variables: dict[str, str]) -> dict[str, str]:
    """Add a capitalised twin for every variable (``$Entity`` for sentence-initial use)."""
    out = dict(variables)
    for k, v in variables.items():
        out.setdefault(k[:1].upper() + k[1:], v[:1].upper() + v[1:])
    return out


def render_markdown(sections: list[str], variables: dict[str, str], extra: list[dict] | None = None,
                    compact: bool = False) -> str:
    """Assemble the appendix as Markdown: numbered H2 sections, or (compact) run-in bold titles in one
    small-type block. Variables substituted; extra sections appended."""
    variables = with_capitals({**DEFAULT_VARIABLES, **variables})
    items: list[tuple[str, str]] = []
    for name in sections:
        md = Template(_section_md(name)).safe_substitute(variables)
        title, _, body = md.partition("\n")
        items.append((title.lstrip("# ").strip(), body.strip()))
    for ex in extra or []:
        items.append((str(ex["title"]), Template(str(ex["text"])).safe_substitute(variables).strip()))
    if compact:
        return "#### Disclosures\n\n" + "\n\n".join(f"**{t}.** {b}" for t, b in items) + "\n"
    return "\n".join(f"## {i}. {t}\n\n{b}\n" for i, (t, b) in enumerate(items, 1))


def render_conflict(text: str | None, variables: dict[str, str]) -> str:
    """The cover statement: the package's standard text always; a document's own sentence(s) are appended."""
    v = with_capitals({**DEFAULT_VARIABLES, **variables})
    base = Template(DEFAULT_CONFLICT).safe_substitute(v)
    return base + ((" " + Template(text).safe_substitute(v).strip()) if text else "")
