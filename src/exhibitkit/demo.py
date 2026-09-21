"""A self-contained demo: synthetic data (numpy RandomState(0)), three figures drawn with the theme's
style, and a short document exercising every device — so `exhibitkit demo` builds a PDF anywhere the
toolchain exists, with no private data."""
from __future__ import annotations

from importlib import resources
from pathlib import Path


def make_figures(out: Path, theme: str) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from .mpl import FULL, use

    st = use(theme)
    out.mkdir(parents=True, exist_ok=True)
    rs = np.random.RandomState(0)
    paths = []

    # 1. a smile: implied vol by strike, two regimes
    k = np.linspace(-0.12, 0.08, 11)
    fig, ax = plt.subplots(figsize=(FULL, 2.4))
    for lvl, name in [(0.16, "Calm"), (0.30, "Stressed")]:
        ax.plot(k * 100, 100 * (lvl + 0.9 * k**2 - 0.35 * k), marker="o", label=name)
    ax.set_xlabel("Log-moneyness (%)")
    st.ylabel_above(ax, "Implied volatility (vol points), synthetic")
    ax.legend(loc="upper right")
    p = out / "smile.pdf"
    st.save(fig, p)
    plt.close(fig)
    paths.append(p)

    # 2. variance shares of three factors
    fig, ax = plt.subplots(figsize=(FULL, 2.2))
    shares = [93.0, 4.5, 1.5]
    ax.bar(["Level", "Slope", "Curvature"], shares, color=st.series[:3], width=0.6)
    for i, s in enumerate(shares):
        ax.text(i, s + 2, f"{s:.1f}%", ha="center", fontsize=7.5)
    ax.set_ylim(0, 110)
    st.ylabel_above(ax, "Share of daily variance (%), synthetic")
    p = out / "pca.pdf"
    st.save(fig, p)
    plt.close(fig)
    paths.append(p)

    # 3. a mean-reverting series with its rolling mean
    n = 500
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.93 * x[i - 1] + rs.normal(0, 1)
    fig, ax = plt.subplots(figsize=(FULL, 2.2))
    ax.plot(x, lw=1.2, label="Series")
    ax.plot(np.convolve(x, np.ones(60) / 60, mode="same"), lw=1.6, label="60-day mean")
    ax.set_xlabel("Day")
    st.ylabel_above(ax, "AR(1) with phi = 0.93 (half-life 9.5 days), synthetic")
    ax.legend(loc="upper right")
    p = out / "series.pdf"
    st.save(fig, p)
    plt.close(fig)
    paths.append(p)
    return paths


def write_document(out: Path, theme: str, layout: str = "primer") -> Path:
    name = "demo_issue.md" if layout == "issue" else "demo.md"
    src = (resources.files("exhibitkit") / "templates" / name).read_text()
    out.mkdir(parents=True, exist_ok=True)
    p = out / "demo.md"
    p.write_text(src.replace("theme: navy", f"theme: {theme}"), encoding="utf-8")
    return p
