"""Thin pandoc wrapper. One extension set for the whole kit, one Lua filter, stdin in, LaTeX out."""
from __future__ import annotations

import json
import shutil
import subprocess
from importlib import resources
from pathlib import Path

FORMAT = "markdown+smart+fenced_divs+pipe_tables+bracketed_spans+raw_tex+tex_math_dollars-implicit_figures-auto_identifiers"


class ToolMissing(RuntimeError):
    pass


def require(tool: str) -> str:
    p = shutil.which(tool)
    if not p:
        raise ToolMissing(f"{tool!r} is not on PATH; exhibitkit needs pandoc >= 3 and a TeX engine (xelatex) to build")
    return p


def filter_path() -> Path:
    return Path(str(resources.files("exhibitkit") / "lua" / "exhibits.lua"))


def to_latex(markdown: str, mode: str = "body", resource_path: Path | None = None, layout: str = "primer") -> str:
    """Markdown -> LaTeX body through the exhibitkit filter. `mode` is "body" | "appendix" | "lead"; `layout` is "primer" | "issue"."""
    cmd = [require("pandoc"), "-f", FORMAT, "-t", "latex", "--lua-filter", str(filter_path()), "-M", f"mode={mode}", "-M", f"layout={layout}"]
    if resource_path:
        cmd += ["--resource-path", str(resource_path)]
    r = subprocess.run(cmd, input=markdown, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc failed: {r.stderr.strip()}")
    return r.stdout


def inline_latex(markdown: str) -> str:
    """A one-paragraph Markdown snippet -> LaTeX inlines (no trailing newline, no \\par)."""
    return to_latex(markdown.strip()).strip()


def to_ast(markdown: str) -> dict:
    cmd = [require("pandoc"), "-f", FORMAT, "-t", "json"]
    r = subprocess.run(cmd, input=markdown, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc failed: {r.stderr.strip()}")
    return json.loads(r.stdout)
