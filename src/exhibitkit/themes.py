"""Theme loading and validation. A theme fixes colours (chrome), fonts (candidate lists resolved at
build time) and the categorical chart series (validated in OKLab before it can be used)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

import yaml

from .fonts import resolve
from .palette import validate_palette

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_COLORS = ("primary", "accent", "ink", "slate", "panel", "rule")


@dataclass
class Theme:
    name: str
    colors: dict[str, str]
    fonts: dict[str, list[str]]
    chart: dict[str, object]
    description: str = ""
    credit: str = ""  # a line every document on this theme carries (cover + end of disclosures); front matter `credit` overrides
    brand: dict = field(default_factory=dict)  # {name, font (candidates), font_file (relative to the package), ink}
    resolved_fonts: dict[str, str] = field(default_factory=dict)

    @property
    def series(self) -> list[str]:
        return list(self.chart["series"])  # type: ignore[arg-type]

    def resolve_fonts(self) -> dict[str, str]:
        self.resolved_fonts = {k: resolve(v) for k, v in self.fonts.items()}
        return self.resolved_fonts


def builtin_names() -> list[str]:
    root = resources.files("exhibitkit") / "themes"
    return sorted(p.name[:-5] for p in root.iterdir() if p.name.endswith(".yaml"))


def _read(name_or_path: str) -> dict:
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return yaml.safe_load(p.read_text())
    root = resources.files("exhibitkit") / "themes"
    f = root / f"{name_or_path}.yaml"
    if not f.is_file():
        raise FileNotFoundError(f"unknown theme {name_or_path!r}; built-ins: {', '.join(builtin_names())}")
    return yaml.safe_load(f.read_text())


def load_theme(name_or_path: str) -> Theme:
    d = _read(name_or_path)
    colors = d.get("colors") or {}
    missing = [k for k in REQUIRED_COLORS if k not in colors]
    if missing:
        raise ValueError(f"theme {d.get('name')!r}: missing colours {missing}")
    bad = [f"{k}={v}" for k, v in colors.items() if not _HEX.match(str(v))]
    if bad:
        raise ValueError(f"theme {d.get('name')!r}: colours must be #RRGGBB: {bad}")
    fonts = d.get("fonts") or {}
    for k in ("main", "sans", "mono"):
        if not fonts.get(k):
            raise ValueError(f"theme {d.get('name')!r}: fonts.{k} must be a non-empty candidate list")
    chart = d.get("chart") or {}
    rep = validate_palette(list(chart.get("series") or []))
    if not rep.ok:
        raise ValueError(f"theme {d.get('name')!r}: chart palette fails validation: " + "; ".join(rep.failures))
    chart.setdefault("neutral", "#B9BEC5")
    chart.setdefault("grid", "#D9DCE0")
    return Theme(name=str(d.get("name") or name_or_path), colors={k: str(v).upper() for k, v in colors.items()},
                 fonts={k: list(v) for k, v in fonts.items()}, chart=chart, description=str(d.get("description", "")),
                 credit=str(d.get("credit", "") or ""), brand=dict(d.get("brand") or {}))
