"""Categorical chart-palette validation in OKLab, with colour-vision-deficiency simulation.

Colours are sRGB hex strings. Distances are OKLab Euclidean distance x 100 ("Delta E"). The
invariants a shipped palette must keep, and the numbers the tests assert:
  - every slot has OKLab lightness in [L_MIN, L_MAX] and OKLCH chroma >= C_MIN (reads as a colour, not grey)
  - every adjacent pair is >= DE_NORMAL apart for normal vision and >= DE_CVD apart under each of
    protanopia, deuteranopia and tritanopia (Machado, Oliveira & Fernandes 2009, severity 1.0)
  - every slot has WCAG contrast >= CONTRAST_MIN against the paper surface
CVD simulation and OKLab both operate on linear sRGB; the Machado matrices are applied there.
"""
from __future__ import annotations

from dataclasses import dataclass, field

L_MIN, L_MAX, C_MIN = 0.43, 0.77, 0.10
DE_NORMAL, DE_CVD, CONTRAST_MIN = 15.0, 8.0, 3.0
PAPER = "#FCFCFB"

_MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"not a 6-digit hex colour: {h!r}")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_linear(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(_lin(c) for c in rgb)  # type: ignore[return-value]


def oklab(lin: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = (max(0.0, x) for x in lin)
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def simulate_cvd(lin: tuple[float, float, float], kind: str) -> tuple[float, float, float]:
    m = _MACHADO[kind]
    return tuple(sum(m[i][j] * lin[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def delta_e(h1: str, h2: str, cvd: str | None = None) -> float:
    a, b = to_linear(hex_to_rgb(h1)), to_linear(hex_to_rgb(h2))
    if cvd:
        a, b = simulate_cvd(a, cvd), simulate_cvd(b, cvd)
    la, lb = oklab(a), oklab(b)
    return 100.0 * sum((x - y) ** 2 for x, y in zip(la, lb, strict=True)) ** 0.5


def luminance(h: str) -> float:
    r, g, b = to_linear(hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1: str, h2: str) -> float:
    a, b = sorted((luminance(h1), luminance(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


@dataclass
class PaletteReport:
    ok: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    worst_normal: float = float("inf")
    worst_cvd: float = float("inf")


def validate_palette(series: list[str], surface: str = PAPER) -> PaletteReport:
    """Run the six checks on a categorical palette in slot order. Adjacent pairs only (bars, stacks, lines)."""
    rep = PaletteReport(ok=True)
    if len(series) < 1:
        rep.ok = False
        rep.failures.append("empty palette")
        return rep
    for h in series:
        L, a, b = oklab(to_linear(hex_to_rgb(h)))
        if not (L_MIN <= L <= L_MAX):
            rep.failures.append(f"{h}: lightness {L:.2f} outside [{L_MIN}, {L_MAX}]")
        if (a * a + b * b) ** 0.5 < C_MIN:
            rep.failures.append(f"{h}: chroma {(a * a + b * b) ** 0.5:.3f} below {C_MIN} (reads grey)")
        if contrast(h, surface) < CONTRAST_MIN:
            rep.failures.append(f"{h}: contrast {contrast(h, surface):.2f}:1 below {CONTRAST_MIN}:1 on {surface}")
    for x, y in zip(series, series[1:], strict=False):
        d = delta_e(x, y)
        rep.worst_normal = min(rep.worst_normal, d)
        if d < DE_NORMAL:
            rep.failures.append(f"{x}~{y}: normal-vision dE {d:.1f} below {DE_NORMAL}")
        for kind in _MACHADO:
            dc = delta_e(x, y, kind)
            rep.worst_cvd = min(rep.worst_cvd, dc)
            if dc < DE_CVD:
                rep.failures.append(f"{x}~{y}: {kind} dE {dc:.1f} below {DE_CVD}")
            elif dc < DE_CVD + 2:
                rep.warnings.append(f"{x}~{y}: {kind} dE {dc:.1f} is close to the floor; direct-label the series")
    rep.ok = not rep.failures
    return rep
