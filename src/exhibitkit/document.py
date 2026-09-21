"""Document model: a Markdown file with a YAML front matter block. Front matter is parsed here (pandoc
also sees it, but the cover, disclosures and checks need it in Python). Dates: ISO in, "Month D, YYYY" out."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REQUIRED = ("title", "date", "authors", "theme")
_FM = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)


@dataclass
class Document:
    path: Path
    meta: dict
    body: str
    problems: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return str(self.meta.get("title", ""))

    @property
    def date_text(self) -> str:
        d = self.meta.get("date")
        if isinstance(d, dt.datetime):
            d = d.date()
        if isinstance(d, dt.date):
            return f"{d.strftime('%B')} {d.day}, {d.year}"
        return str(d or "")

    @property
    def year(self) -> str:
        d = self.meta.get("date")
        return str(d.year) if isinstance(d, (dt.date, dt.datetime)) else str(d)[:4]

    @property
    def authors(self) -> list[dict]:
        a = self.meta.get("authors") or []
        return [{"name": x} if isinstance(x, str) else dict(x) for x in a]

    @property
    def author_names(self) -> str:
        names = [a.get("name", "") for a in self.authors]
        return ", ".join(n for n in names if n)


def parse(path: str | Path) -> Document:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    m = _FM.match(text)
    if not m:
        return Document(path, {}, text, ["no YAML front matter block at the top of the file"])
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:  # pragma: no cover - message formatting
        return Document(path, {}, text[m.end():], [f"front matter is not valid YAML: {e}"])
    if not isinstance(meta, dict):
        return Document(path, {}, text[m.end():], ["front matter must be a mapping"])
    doc = Document(path, meta, text[m.end():])
    doc.problems.extend(f"front matter is missing required key {k!r}" for k in REQUIRED if k not in meta)
    if "takeaways" in meta and not isinstance(meta["takeaways"], list):
        doc.problems.append("takeaways must be a list")
    return doc
