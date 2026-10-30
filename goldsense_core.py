"""GoldSense core: data loading, features, model and commentary.

No Streamlit import here, so this file can be tested on its own.
"""
import datetime as dt

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, brier_score_loss, mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SYMBOLS = {
    "gold": "GC=F",
    "dollar": "DX-Y.NYB",
    "equity": "^GSPC",
    "vix": "^VIX",
    "oil": "CL=F",
}
MIN_ROWS = 500
STALE_DAYS = 4


def load_prices(now=None):
    """Download 5y daily closes; drop bars from the current UTC date (may be unfinished)."""
    import yfinance as yf

    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now.date()
    parts = []
    for name, symbol in SYMBOLS.items():
        raw = yf.download(
            symbol, period="5y", interval="1d",
            auto_adjust=True, progress=False, threads=False,
        )
        if raw is None or raw.empty:
            raise ValueError(f"ไม่มีข้อมูล {name}")
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        parts.append(clean_series(close, cutoff).rename(name))

    prices = pd.concat(parts, axis=1).sort_index()
    prices = prices.loc[prices.gold.notna()]
    if prices.empty:
        raise ValueError("ไม่มีข้อมูลราคาทอง")
    return prices, now.isoformat()


def clean_series(close, cutoff):
    close = close.copy()
    idx = pd.to_datetime(close.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    close.index = idx
    close = close[~close.index.duplicated(keep="last")]
    return close.loc[close.index.date < cutoff]


def features(prices):
    gold = prices.gold
    x = pd.DataFrame(index=prices.index)
    x["gold_1d"] = gold.pct_change(fill_method=None)
    x["gold_5d"] = gold.pct_change(5, fill_method=None)
    x["momentum"] = gold / gold.rolling(20).mean() - 1
    x["volatility"] = x.gold_1d.rolling(20).std()
    for name in ["dollar", "equity", "vix", "oil"]:
        x[name] = prices[name].pct_change(fill_method=None)
    return x.shift(1).replace([np.inf, -np.inf], np.nan)


def _models():
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))
    reg = make_pipeline(StandardScaler(), Ridge(alpha=20))
    return clf, reg


def analyze(prices):
    x = features(prices)
    target = prices.gold.shift(-1) / prices.gold - 1
    data = x.join(target.rename("target")).dropna()
    if len(data) < MIN_ROWS:
        raise ValueError(f"ต้องมีข้อมูลครบอย่างน้อย {MIN_ROWS} แถว (มี {len(data)})")

    columns = list(x.columns)
    split = int(len(data) * 0.8)
    train, test = data.iloc[:split - 1], data.iloc[split:]
    ytrain = (train.target > 0).astype(int)
    ytest = (test.target > 0).astype(int)
    if ytrain.nunique() < 2:
        raise ValueError("ข้อมูลฝึกต้องมีทั้งขึ้นและไม่ขึ้น")

    clf, reg = _models()
    clf.fit(train[columns], ytrain)
    reg.fit(train[columns], train.target)
    prob = clf.predict_proba(test[columns])[:, 1]
    ret = reg.predict(test[columns])
    base = float(ytrain.mean())
    scores = {
        "accuracy": float(accuracy_score(ytest, prob >= 0.5)),
        "always_up": float(ytest.mean()),
        "brier": float(brier_score_loss(ytest, prob)),
        "baseline_brier": float(brier_score_loss(ytest, np.full(len(test), base))),
        "mae": float(mean_absolute_error(test.target, ret)),
        "zero_return_mae": float(mean_absolute_error(test.target, np.zeros(len(test)))),
        "samples": int(len(test)),
    }

    latest = x.iloc[[-1]]
    if latest.isna().any().any():
        raise ValueError("ปัจจัยล่าสุดไม่ครบ ระงับการคาดการณ์")

    clf, reg = _models()
    clf.fit(data[columns], (data.target > 0).astype(int))
    reg.fit(data[columns], data.target)
    p = float(clf.predict_proba(latest)[0, 1])
    expected = float(reg.predict(latest)[0])
    impact = clf[0].transform(latest)[0] * clf[1].coef_[0]
    impacts = pd.DataFrame(
        {"factor": columns, "log_odds_contribution": impact}
    ).sort_values("log_odds_contribution")
    return p, expected, scores, impacts


def data_age_days(prices, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    return (now.date() - prices.index[-1].date()).days


def commentary(prices, p, expected):
    date = prices.index[-1].strftime("%d/%m/%Y")
    change = prices.gold.pct_change(fill_method=None).iloc[-1]
    direction = (
        "ให้น้ำหนักการปรับขึ้น" if p >= .55 else
        "ให้น้ำหนักการไม่ปรับขึ้น" if p <= .45 else
        "ยังไม่มีทิศทางเด่นชัด"
    )
    return (
        f"ข้อมูลราคาอ้างอิงถึงวันที่ {date} "
        f"ทองล่วงหน้าเปลี่ยนแปลง {change:+.2%} จากแถวก่อนหน้า\n\n"
        f"โมเดล{direction}สำหรับวันซื้อขายถัดไป "
        f"โดยประมาณโอกาสขึ้น {p:.1%} และผลตอบแทน {expected:+.2%}\n\n"
        "ทั้งสองค่ามาจากคนละโมเดล จึงอาจไม่สอดคล้องกัน "
        "เปอร์เซ็นต์ยังไม่ได้สอบเทียบ "
        "บทวิเคราะห์นี้ไม่มีข้อมูลข่าวสดและไม่ใช่คำแนะนำลงทุน"
    )
