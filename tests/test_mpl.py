import pytest

mpl = pytest.importorskip("matplotlib")
mpl.use("Agg")

from exhibitkit.mpl import FULL, HALF, use  # noqa: E402


def test_use_applies_theme_and_cycle():
    st = use("foghnan")
    assert st.series == ["#6B3F78", "#B07410", "#1A9EB0", "#C24E7A"]
    cyc = [c["color"] for c in mpl.rcParams["axes.prop_cycle"]]
    assert cyc == st.series
    assert mpl.rcParams["axes.spines.top"] is False and mpl.rcParams["pdf.fonttype"] == 42
    assert HALF < FULL / 2 + 0.01 and FULL > 6.5


def test_ylabel_above_writes_text():
    import matplotlib.pyplot as plt

    st = use("navy")
    fig, ax = plt.subplots()
    st.ylabel_above(ax, "Label")
    assert ax.get_ylabel() == "" and any(t.get_text() == "Label" for t in ax.texts)
    plt.close(fig)
