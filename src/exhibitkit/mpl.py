"""matplotlib styling that matches a theme: recessive grid, no top/right spines, the validated series,
the horizontal y-label above the axis, and page-matched figure widths (FULL = 6.85in = text + margin column, HALF = 3.3in).
Optional dependency: import this module only when matplotlib is installed."""
from __future__ import annotations

from dataclasses import dataclass

from .themes import Theme, load_theme

FULL, HALF, COL = 6.85, 3.3, 3.35  # COL = one column of the issue layout


@dataclass
class Style:
    theme: Theme
    series: list[str]
    ink: str
    slate: str
    grid: str
    neutral: str

    def ylabel_above(self, ax, text: str) -> None:
        ax.set_ylabel("")
        ax.text(0, 1.02, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, color=self.slate)

    def date_axis(self, ax, weeks: int = 1, fmt: str = "%b %d") -> None:
        import matplotlib.dates as mdates

        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=weeks))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))

    def year_axis(self, ax) -> None:
        import matplotlib.dates as mdates

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    @staticmethod
    def save(fig, path) -> None:
        fig.savefig(path, bbox_inches="tight", pad_inches=0.02)


def use(theme: str | Theme = "navy") -> Style:
    import matplotlib as mpl

    th = theme if isinstance(theme, Theme) else load_theme(theme)
    fonts = th.resolve_fonts()
    c = th.colors
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [fonts["sans"], "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "axes.edgecolor": c["slate"], "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": th.chart["grid"], "grid.linewidth": 0.5,
        "xtick.color": c["slate"], "ytick.color": c["slate"], "text.color": c["ink"], "axes.labelcolor": c["ink"],
        "lines.linewidth": 1.6, "lines.markersize": 4, "legend.frameon": False, "legend.fontsize": 7.5,
        "pdf.fonttype": 42, "axes.prop_cycle": mpl.cycler(color=th.series),
    })
    return Style(th, th.series, c["ink"], c["slate"], str(th.chart["grid"]), str(th.chart["neutral"]))
