"""OKLab / CVD / contrast identities. Reference values: white -> L = 1, black -> L = 0 (Ottosson 2020);
WCAG contrast of black on white = 21:1 exactly; the Machado matrices at severity 1.0 map achromatic
colours to themselves up to the published rounding (rows sum to ~1)."""
from exhibitkit import palette as p


def test_oklab_endpoints():
    L, a, b = p.oklab(p.to_linear(p.hex_to_rgb("#FFFFFF")))
    assert abs(L - 1.0) < 1e-6 and abs(a) < 1e-6 and abs(b) < 1e-6
    L0, _, _ = p.oklab(p.to_linear(p.hex_to_rgb("#000000")))
    assert L0 == 0.0


def test_contrast_black_white_is_21():
    assert abs(p.contrast("#000000", "#FFFFFF") - 21.0) < 1e-9
    assert p.contrast("#000000", "#FFFFFF") == p.contrast("#FFFFFF", "#000000")


def test_delta_e_symmetric_and_zero_on_self():
    assert p.delta_e("#2A5DA8", "#2A5DA8") == 0.0
    assert abs(p.delta_e("#2A5DA8", "#E0742A") - p.delta_e("#E0742A", "#2A5DA8")) < 1e-12


def test_machado_rows_sum_to_one_within_rounding():
    for kind in ("protan", "deutan", "tritan"):
        out = p.simulate_cvd((1.0, 1.0, 1.0), kind)
        assert all(abs(x - 1.0) < 2e-3 for x in out), (kind, out)


def test_validate_rejects_grey_and_low_contrast():
    r = p.validate_palette(["#888888", "#C98B1F"])
    assert not r.ok
    assert any("chroma" in f for f in r.failures)
    assert any("contrast" in f and "#C98B1F" in f for f in r.failures)


def test_validate_rejects_near_identical_neighbours():
    r = p.validate_palette(["#2A5DA8", "#2B5EA9"])
    assert not r.ok and any("normal-vision" in f for f in r.failures)


def test_bad_hex_raises():
    import pytest

    with pytest.raises(ValueError):
        p.hex_to_rgb("#12345")
