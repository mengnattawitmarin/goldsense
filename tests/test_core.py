import datetime as dt
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import goldsense_core as core  # noqa: E402


def fake_prices(n=900, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2022-01-03", periods=n)
    cols = {}
    for name, start in [("gold", 1800), ("dollar", 100), ("equity", 4500),
                        ("vix", 18), ("oil", 80)]:
        cols[name] = start * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame(cols, index=idx)


def test_features_use_only_past():
    prices = fake_prices()
    base = core.features(prices)
    changed = prices.copy()
    changed.iloc[-1] *= 2  # alter only the last row
    after = core.features(changed)
    # features at every row (including last) must not see that row's own price
    pd.testing.assert_frame_equal(base, after)


def test_analyze_outputs():
    p, expected, scores, impacts = core.analyze(fake_prices())
    assert 0 < p < 1
    assert np.isfinite(expected)
    assert scores["samples"] > 100
    assert 0 <= scores["accuracy"] <= 1
    assert len(impacts) == 8


def test_analyze_needs_enough_rows():
    try:
        core.analyze(fake_prices(n=300))
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_missing_latest_factor_blocks_forecast():
    prices = fake_prices()
    prices.iloc[-2, prices.columns.get_loc("oil")] = np.nan
    try:
        core.analyze(prices)
    except ValueError as e:
        assert "ไม่ครบ" in str(e)
        return
    raise AssertionError("expected ValueError")


def test_clean_series_drops_today_and_duplicates():
    idx = pd.to_datetime(["2026-10-28", "2026-10-29", "2026-10-29", "2026-10-30"]).tz_localize("UTC")
    s = pd.Series([1.0, 2.0, 3.0, 4.0], index=idx)
    out = core.clean_series(s, dt.date(2026, 10, 30))
    assert list(out.values) == [1.0, 3.0]


def test_commentary_and_age():
    prices = fake_prices()
    text = core.commentary(prices, 0.6, 0.002)
    assert "ให้น้ำหนักการปรับขึ้น" in text and "60.0%" in text
    now = dt.datetime.combine(prices.index[-1].date() + dt.timedelta(days=5),
                              dt.time(), dt.timezone.utc)
    assert core.data_age_days(prices, now) == 5
