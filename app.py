from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

try:
    from supabase import create_client
except Exception:
    create_client = None


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Live Market Trader",
    page_icon="📈",
    layout="centered",
)

st.title("Live Market Trader")

st.caption(
    "Scanner • trade plan • EOD forecast • watchlist • prediction scorecard"
)

st.warning(
    "Signals, forecasts and trade levels are model estimates for research. "
    "They are not guaranteed outcomes or personalized investment advice."
)


# ============================================================
# TIME
# ============================================================

ET = ZoneInfo("America/Toronto")


def now_et():
    return datetime.now(ET)


def session_mode():
    current = now_et()

    if current.weekday() >= 5:
        return "WEEKEND", "Market closed"

    if current.time() < time(9, 30):
        return "PREMARKET", "Premarket"

    if current.time() <= time(16, 0):
        return "REGULAR", "Live"

    return "AFTERHOURS", "After-hours"


SESSION, SESSION_LABEL = session_mode()


def regular_session_fraction():
    """
    0.0 at 9:30 ET
    1.0 at 4:00 ET
    """
    current = now_et()

    if SESSION == "PREMARKET":
        return 0.0

    if SESSION == "AFTERHOURS":
        return 1.0

    if SESSION != "REGULAR":
        return 0.0

    start = current.replace(
        hour=9,
        minute=30,
        second=0,
        microsecond=0,
    )

    end = current.replace(
        hour=16,
        minute=0,
        second=0,
        microsecond=0,
    )

    total = (end - start).total_seconds()
    elapsed = (current - start).total_seconds()

    return float(
        max(
            0.0,
            min(1.0, elapsed / total),
        )
    )


# ============================================================
# UNIVERSES
# ============================================================

CANADIAN_ETFS = {
    "XEQT": "iShares Core Equity ETF Portfolio",
    "XGRO": "iShares Core Growth ETF Portfolio",
    "XBAL": "iShares Core Balanced ETF Portfolio",
    "VEQT": "Vanguard All-Equity ETF Portfolio",
    "VGRO": "Vanguard Growth ETF Portfolio",
    "VBAL": "Vanguard Balanced ETF Portfolio",
    "VFV": "Vanguard S&P 500 Index ETF",
    "XQQ": "iShares NASDAQ 100 Index ETF",
    "VCN": "Vanguard FTSE Canada All Cap Index ETF",
    "XIU": "iShares S&P/TSX 60 Index ETF",
    "ZAG": "BMO Aggregate Bond Index ETF",
    "VAB": "Vanguard Canadian Aggregate Bond Index ETF",
}

TSX = {
    "RY.TO": "Royal Bank",
    "TD.TO": "TD Bank",
    "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank",
    "CM.TO": "CIBC",
    "NA.TO": "National Bank",
    "MFC.TO": "Manulife",
    "SLF.TO": "Sun Life",
    "CNQ.TO": "Canadian Natural",
    "SU.TO": "Suncor",
    "CVE.TO": "Cenovus",
    "IMO.TO": "Imperial Oil",
    "TRP.TO": "TC Energy",
    "ENB.TO": "Enbridge",
    "SHOP.TO": "Shopify",
    "CSU.TO": "Constellation Software",
    "OTEX.TO": "OpenText",
    "CNR.TO": "CN Rail",
    "CP.TO": "CPKC",
    "ABX.TO": "Barrick Mining",
    "AEM.TO": "Agnico Eagle",
    "WPM.TO": "Wheaton Precious Metals",
    "NTR.TO": "Nutrien",
    "TECK-B.TO": "Teck Resources",
    "FTS.TO": "Fortis",
    "EMA.TO": "Emera",
    "BCE.TO": "BCE",
    "T.TO": "TELUS",
    "ATD.TO": "Couche-Tard",
    "L.TO": "Loblaw",
}

SP500 = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "META": "Meta",
    "GOOGL": "Alphabet",
    "AVGO": "Broadcom",
    "JPM": "JPMorgan",
    "BAC": "Bank of America",
    "GS": "Goldman Sachs",
    "V": "Visa",
    "MA": "Mastercard",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "LLY": "Eli Lilly",
    "WMT": "Walmart",
    "COST": "Costco",
    "HD": "Home Depot",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "DIS": "Disney",
    "UBER": "Uber",
    "PLTR": "Palantir",
}

NASDAQ = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "META": "Meta",
    "GOOGL": "Alphabet",
    "AVGO": "Broadcom",
    "TSLA": "Tesla",
    "COST": "Costco",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "ADBE": "Adobe",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "AMAT": "Applied Materials",
    "MU": "Micron",
    "PANW": "Palo Alto Networks",
    "CRWD": "CrowdStrike",
    "CSCO": "Cisco",
    "MRVL": "Marvell",
    "LRCX": "Lam Research",
    "KLAC": "KLA",
    "MSTR": "Strategy",
    "ARM": "Arm Holdings",
}

ALL_NAMES = {}
ALL_NAMES.update(TSX)
ALL_NAMES.update(SP500)
ALL_NAMES.update(NASDAQ)

for symbol, name in CANADIAN_ETFS.items():
    ALL_NAMES[f"{symbol}.TO"] = name


# ============================================================
# TICKER HELPERS
# ============================================================

def normalize_ticker(raw):
    ticker = raw.strip().upper()

    if not ticker:
        return ""

    if ticker.endswith(".TO"):
        return ticker

    if ticker in CANADIAN_ETFS:
        return ticker + ".TO"

    if ticker + ".TO" in TSX:
        return ticker + ".TO"

    return ticker


def is_canadian_etf(ticker):
    return ticker.replace(".TO", "") in CANADIAN_ETFS


def market_index(ticker):
    if ticker.endswith(".TO"):
        return "^GSPTSE"

    if ticker in NASDAQ:
        return "^IXIC"

    return "^GSPC"


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=600)
def daily_data(ticker, period="1y"):
    try:
        df = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.dropna()

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def intraday_data(ticker):
    try:
        df = yf.download(
            ticker,
            period="5d",
            interval="5m",
            auto_adjust=False,
            prepost=True,
            progress=False,
            threads=False,
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.dropna()

    except Exception:
        return pd.DataFrame()


def get_series(df, column):
    if df is None or df.empty or column not in df.columns:
        return pd.Series(dtype=float)

    result = df[column]

    if isinstance(result, pd.DataFrame):
        result = result.iloc[:, 0]

    return pd.to_numeric(
        result,
        errors="coerce",
    )


def latest_move(ticker):
    data = daily_data(ticker, "1mo")
    close = get_series(data, "Close").dropna()

    if len(close) < 2:
        return 0.0

    return float(
        close.iloc[-1]
        / close.iloc[-2]
        - 1
    )


# ============================================================
# PRICE
# ============================================================

def price_info(ticker):
    intra = intraday_data(ticker)
    daily = daily_data(ticker, "1mo")

    daily_close = get_series(
        daily,
        "Close",
    ).dropna()

    previous_close = (
        float(daily_close.iloc[-1])
        if len(daily_close)
        else None
    )

    if not intra.empty:
        intra_close = get_series(
            intra,
            "Close",
        ).dropna()

        if len(intra_close):
            if SESSION == "PREMARKET":
                label = "Premarket"

            elif SESSION == "REGULAR":
                label = "Live / latest available"

            elif SESSION == "AFTERHOURS":
                label = "After-hours"

            else:
                label = "Latest available"

            return (
                float(intra_close.iloc[-1]),
                label,
                previous_close,
            )

    return (
        previous_close,
        "Previous Close",
        previous_close,
    )


# ============================================================
# INDICATORS
# ============================================================

def calculate_rsi(close, period=14):
    change = close.diff()

    gains = (
        change
        .clip(lower=0)
        .rolling(period)
        .mean()
    )

    losses = (
        -change
        .clip(upper=0)
        .rolling(period)
        .mean()
    )

    rs = gains / losses.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def calculate_atr(df, period=14):
    high = get_series(df, "High")
    low = get_series(df, "Low")
    close = get_series(df, "Close")

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(period).mean()


def calculate_vwap(ticker):
    data = intraday_data(ticker)

    if data.empty:
        return None

    high = get_series(data, "High")
    low = get_series(data, "Low")
    close = get_series(data, "Close")
    volume = get_series(data, "Volume")

    cumulative_volume = volume.cumsum()

    if (
        len(close) == 0
        or len(cumulative_volume) == 0
        or cumulative_volume.iloc[-1] <= 0
    ):
        return None

    typical_price = (
        high + low + close
    ) / 3

    vwap = (
        (typical_price * volume).cumsum()
        / cumulative_volume
    )

    return float(vwap.iloc[-1])


# ============================================================
# EOD FORECAST
# ============================================================

def make_eod_forecast(
    ticker,
    current,
    previous_close,
    close,
    atr_value,
    rsi_value,
    market_move,
    day_score,
    quality_score,
    vwap,
):
    """
    Heuristic end-of-day / next-session close estimate.

    This is NOT a guaranteed price target.
    The important part is that the forecast is saved before the
    actual closing price is known and later scored against reality.
    """

    ret1 = float(
        close.pct_change(1).iloc[-1]
    )

    ret3 = float(
        close.pct_change(3).iloc[-1]
    )

    ret5 = float(
        close.pct_change(5).iloc[-1]
    )

    if previous_close is None or previous_close <= 0:
        previous_close = current

    current_move = (
        current / previous_close
        - 1
    )

    daily_volatility = (
        close
        .pct_change()
        .tail(20)
        .std()
    )

    if pd.isna(daily_volatility):
        daily_volatility = 0.015

    atr_pct = (
        atr_value / current
        if current > 0
        else 0.02
    )

    # Historical momentum expectation
    momentum_expectation = (
        0.30 * ret1
        + 0.20 * (ret3 / 3)
        + 0.15 * (ret5 / 5)
        + 0.20 * market_move
    )

    # RSI contribution
    rsi_bias = (
        (rsi_value - 50)
        / 50
        * 0.0035
    )

    # VWAP contribution
    vwap_bias = 0.0

    if (
        vwap is not None
        and vwap > 0
    ):
        vwap_distance = (
            current / vwap
            - 1
        )

        vwap_bias = float(
            np.clip(
                vwap_distance * 0.15,
                -0.004,
                0.004,
            )
        )

    base_expected_move = (
        momentum_expectation
        + rsi_bias
        + vwap_bias
    )

    max_expected_move = max(
        0.005,
        atr_pct * 1.25,
    )

    base_expected_move = float(
        np.clip(
            base_expected_move,
            -max_expected_move,
            max_expected_move,
        )
    )

    elapsed = regular_session_fraction()

    if SESSION == "REGULAR":
        # As we approach 4 PM, today's actual move becomes more
        # important than the historical forecast.
        predicted_session_return = (
            elapsed * current_move
            + (1 - elapsed) * base_expected_move
        )

    elif SESSION == "AFTERHOURS":
        # After close, this becomes a next-session estimate.
        predicted_session_return = base_expected_move

    elif SESSION == "WEEKEND":
        predicted_session_return = base_expected_move

    else:
        # Premarket
        predicted_session_return = (
            0.20 * current_move
            + 0.80 * base_expected_move
        )

    predicted_close = (
        previous_close
        * (
            1
            + predicted_session_return
        )
    )

    # Prevent extreme unrealistic forecast jumps.
    cap = max(
        atr_value * 1.50,
        current * 0.01,
    )

    predicted_close = float(
        np.clip(
            predicted_close,
            current - cap,
            current + cap,
        )
    )

    remaining_fraction = (
        max(
            0.10,
            1 - elapsed,
        )
        if SESSION == "REGULAR"
        else 1.0
    )

    uncertainty = max(
        atr_value * (
            0.30
            + 0.55 * remaining_fraction
        ),
        current
        * daily_volatility
        * 0.35,
    )

    forecast_low = max(
        0.01,
        predicted_close - uncertainty,
    )

    forecast_high = (
        predicted_close
        + uncertainty
    )

    score_strength = (
        abs(day_score - 50)
        / 50
    )

    quality_strength = (
        quality_score / 100
    )

    confidence = (
        50
        + 20 * score_strength
        + 12 * quality_strength
    )

    if SESSION == "REGULAR":
        confidence += (
            elapsed * 6
        )

    confidence = int(
        np.clip(
            round(confidence),
            50,
            85,
        )
    )

    predicted_move_from_current = (
        predicted_close / current
        - 1
    )

    if predicted_close > current * 1.001:
        eod_direction = "UP"

    elif predicted_close < current * 0.999:
        eod_direction = "DOWN"

    else:
        eod_direction = "FLAT"

    return {
        "eod_predicted_close":
            float(predicted_close),

        "eod_range_low":
            float(forecast_low),

        "eod_range_high":
            float(forecast_high),

        "eod_confidence":
            confidence,

        "eod_predicted_move":
            float(predicted_move_from_current),

        "eod_direction":
            eod_direction,
    }


# ============================================================
# ANALYSIS
# ============================================================

def analyze(raw_ticker):
    ticker = normalize_ticker(
        raw_ticker
    )

    data = daily_data(
        ticker
    )

    if data.empty:
        return None

    close = get_series(
        data,
        "Close",
    )

    volume = get_series(
        data,
        "Volume",
    )

    high = get_series(
        data,
        "High",
    )

    low = get_series(
        data,
        "Low",
    )

    if len(close) < 70:
        return None

    current, price_label, previous_close = (
        price_info(
            ticker
        )
    )

    if current is None:
        return None

    ret1 = close.pct_change(1).iloc[-1]
    ret3 = close.pct_change(3).iloc[-1]
    ret5 = close.pct_change(5).iloc[-1]
    ret20 = close.pct_change(20).iloc[-1]

    ma5 = (
        close
        .rolling(5)
        .mean()
        .iloc[-1]
    )

    ma20 = (
        close
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    ma50 = (
        close
        .rolling(50)
        .mean()
        .iloc[-1]
    )

    rsi_value = (
        calculate_rsi(close)
        .iloc[-1]
    )

    average_volume = (
        volume
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    if (
        average_volume
        and not pd.isna(
            average_volume
        )
    ):
        relative_volume = float(
            volume.iloc[-1]
            / average_volume
        )

    else:
        relative_volume = 1.0

    market_move = latest_move(
        market_index(
            ticker
        )
    )

    # ========================================================
    # DAY SCORE
    # ========================================================

    day_score = 50

    day_score += (
        11
        * np.tanh(
            ret1 / 0.015
        )
    )

    day_score += (
        8
        * np.tanh(
            ret3 / 0.025
        )
    )

    day_score += (
        7
        * np.tanh(
            market_move / 0.012
        )
    )

    day_score += (
        8
        * np.tanh(
            (
                ma5 / ma20
                - 1
            )
            / 0.025
        )
    )

    if relative_volume >= 1.5:
        day_score += 5

    elif relative_volume >= 1.2:
        day_score += 3

    if 55 <= rsi_value <= 68:
        day_score += 4

    if rsi_value >= 80:
        day_score -= 8

    elif rsi_value >= 73:
        day_score -= 4

    if is_canadian_etf(ticker):
        day_score = (
            50
            + (
                day_score - 50
            )
            * 0.80
        )

    day_score = int(
        np.clip(
            round(day_score),
            0,
            100,
        )
    )

    # ========================================================
    # SWING SCORE
    # ========================================================

    swing_score = 50

    swing_score += (
        8
        * np.tanh(
            ret3 / 0.025
        )
    )

    swing_score += (
        11
        * np.tanh(
            ret5 / 0.04
        )
    )

    swing_score += (
        10
        * np.tanh(
            ret20 / 0.09
        )
    )

    swing_score += (
        8
        * np.tanh(
            (
                ma5 / ma20
                - 1
            )
            / 0.03
        )
    )

    swing_score += (
        8
        * np.tanh(
            (
                ma20 / ma50
                - 1
            )
            / 0.05
        )
    )

    if 50 <= rsi_value <= 68:
        swing_score += 4

    if rsi_value >= 80:
        swing_score -= 8

    if is_canadian_etf(ticker):
        swing_score = (
            50
            + (
                swing_score - 50
            )
            * 0.85
        )

    swing_score = int(
        np.clip(
            round(swing_score),
            0,
            100,
        )
    )

    # ========================================================
    # QUALITY SCORE
    # ========================================================

    quality_score = 50

    if 50 <= rsi_value <= 68:
        quality_score += 12

    elif rsi_value >= 80:
        quality_score -= 18

    if relative_volume >= 1.5:
        quality_score += 8

    elif relative_volume >= 1.2:
        quality_score += 4

    if ma5 > ma20 > ma50:
        quality_score += 10

    vwap = calculate_vwap(
        ticker
    )

    if (
        vwap is not None
        and SESSION == "REGULAR"
    ):
        if current >= vwap:
            quality_score += 10
        else:
            quality_score -= 10

    quality_score = int(
        np.clip(
            round(quality_score),
            0,
            100,
        )
    )

    # ========================================================
    # ATR
    # ========================================================

    atr_values = calculate_atr(
        data
    )

    if (
        len(atr_values)
        and not pd.isna(
            atr_values.iloc[-1]
        )
    ):
        atr_value = float(
            atr_values.iloc[-1]
        )

    else:
        atr_value = (
            current * 0.02
        )

    # ========================================================
    # TRADE LEVELS
    # ========================================================

    support = max(
        float(
            low.tail(10).min()
        ),
        current
        - 1.5 * atr_value,
    )

    resistance = float(
        high.tail(10).max()
    )

    if is_canadian_etf(
        ticker
    ):
        entry_low = (
            current
            - 0.30 * atr_value
        )

        entry_high = (
            current
            + 0.08 * atr_value
        )

        stop = min(
            support
            - 0.15 * atr_value,

            entry_low
            - 0.75 * atr_value,
        )

    else:
        entry_low = (
            current
            - 0.45 * atr_value
        )

        entry_high = (
            current
            + 0.10 * atr_value
        )

        stop = min(
            support
            - 0.20 * atr_value,

            entry_low
            - 0.85 * atr_value,
        )

    entry_mid = (
        entry_low
        + entry_high
    ) / 2

    risk = max(
        entry_mid - stop,
        0.01,
    )

    target1 = max(
        resistance,
        entry_mid
        + 1.5 * risk,
    )

    target2 = max(
        resistance + atr_value,
        entry_mid
        + 2.2 * risk,
    )

    rr1 = (
        target1
        - entry_mid
    ) / risk

    rr2 = (
        target2
        - entry_mid
    ) / risk

    # ========================================================
    # ACTION
    # ========================================================

    if rsi_value >= 80:
        action = "DON'T CHASE"

        prediction = (
            "UP"
            if day_score >= 55
            else "NEUTRAL"
        )

    elif (
        rsi_value >= 70
        and not is_canadian_etf(
            ticker
        )
    ):
        action = "WAIT FOR PULLBACK"

        prediction = (
            "UP"
            if day_score >= 55
            else "NEUTRAL"
        )

    elif rr1 < 1.5:
        action = "WAIT — POOR RISK/REWARD"

        prediction = (
            "UP"
            if day_score >= 55
            else "NEUTRAL"
        )

    elif (
        day_score >= 75
        and quality_score >= 70
    ):
        action = "BUY SETUP / ENTRY FAVOURABLE"
        prediction = "UP"

    elif (
        day_score >= 65
        or swing_score >= 70
    ):
        action = "WATCH FOR ENTRY"
        prediction = "UP"

    elif (
        day_score <= 40
        and swing_score <= 45
    ):
        action = "AVOID / SELL REVIEW"
        prediction = "DOWN"

    else:
        action = "NO CLEAR ENTRY"
        prediction = "NEUTRAL"

    eod = make_eod_forecast(
        ticker=ticker,
        current=current,
        previous_close=previous_close,
        close=close,
        atr_value=atr_value,
        rsi_value=rsi_value,
        market_move=market_move,
        day_score=day_score,
        quality_score=quality_score,
        vwap=vwap,
    )

    result = {
        "ticker": ticker,

        "name":
            ALL_NAMES.get(
                ticker,
                ticker,
            ),

        "current":
            float(current),

        "price_label":
            price_label,

        "previous_close":
            previous_close,

        "day":
            day_score,

        "swing":
            swing_score,

        "quality":
            quality_score,

        "prediction":
            prediction,

        "action":
            action,

        "rsi":
            float(rsi_value),

        "relative_volume":
            relative_volume,

        "vwap":
            vwap,

        "atr":
            atr_value,

        "entry_low":
            float(entry_low),

        "entry_high":
            float(entry_high),

        "stop":
            float(stop),

        "target1":
            float(target1),

        "target2":
            float(target2),

        "rr1":
            float(rr1),

        "rr2":
            float(rr2),

        "rank":
            (
                day_score * 0.45
                + swing_score * 0.25
                + quality_score * 0.30
            ),
    }

    result.update(eod)

    return result


# ============================================================
# SESSION STATE
# ============================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "scanner_results" not in st.session_state:
    st.session_state.scanner_results = []

if "my_stock_results" not in st.session_state:
    st.session_state.my_stock_results = []

if "predictions" not in st.session_state:
    st.session_state.predictions = []


# ============================================================
# SUPABASE
# ============================================================

def get_database():
    if create_client is None:
        return None

    try:
        return create_client(
            st.secrets[
                "SUPABASE_URL"
            ],
            st.secrets[
                "SUPABASE_KEY"
            ],
        )

    except Exception:
        return None


DATABASE = get_database()

PERSISTENT_STORAGE = (
    DATABASE is not None
)


# ============================================================
# PREDICTION DATE
# ============================================================

def prediction_trade_date():
    current = now_et()

    if (
        current.weekday() < 5
        and current.time() <= time(16, 0)
    ):
        return current.date()

    next_date = (
        current.date()
        + timedelta(days=1)
    )

    while next_date.weekday() >= 5:
        next_date += timedelta(days=1)

    return next_date


# ============================================================
# DATABASE
# ============================================================

def fetch_predictions():
    if PERSISTENT_STORAGE:
        try:
            response = (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .select("*")
                .order(
                    "tracked_at",
                    desc=True,
                )
                .execute()
            )

            return response.data or []

        except Exception as error:
            st.error(
                f"Could not load tracker: {error}"
            )

            return []

    return list(
        st.session_state.predictions
    )


def already_tracked(
    ticker,
    trade_date,
):
    for row in fetch_predictions():
        if (
            row.get("ticker") == ticker
            and str(
                row.get("trade_date")
            ) == str(trade_date)
        ):
            return True

    return False


def save_prediction(result):
    trade_date = (
        prediction_trade_date()
    )

    if already_tracked(
        result["ticker"],
        trade_date,
    ):
        return "duplicate"

    row = {
        "ticker":
            result["ticker"],

        "tracked_at":
            now_et().isoformat(),

        "trade_date":
            trade_date.isoformat(),

        "prediction":
            result["prediction"],

        "action":
            result["action"],

        "day_score":
            result["day"],

        "swing_score":
            result["swing"],

        "quality_score":
            result["quality"],

        "start_price":
            result["current"],

        "entry_low":
            result["entry_low"],

        "entry_high":
            result["entry_high"],

        "stop_price":
            result["stop"],

        "target1":
            result["target1"],

        "target2":
            result["target2"],

        "eod_predicted_close":
            result[
                "eod_predicted_close"
            ],

        "eod_range_low":
            result[
                "eod_range_low"
            ],

        "eod_range_high":
            result[
                "eod_range_high"
            ],

        "eod_confidence":
            result[
                "eod_confidence"
            ],

        "eod_predicted_move":
            result[
                "eod_predicted_move"
            ],

        "close_price":
            None,

        "day_high":
            None,

        "day_low":
            None,

        "direction_correct":
            None,

        "stop_hit":
            None,

        "target1_hit":
            None,

        "target2_hit":
            None,

        "eod_error_abs":
            None,

        "eod_error_pct":
            None,

        "eod_range_hit":
            None,

        "result_status":
            "OPEN",
    }

    if PERSISTENT_STORAGE:
        try:
            (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .insert(row)
                .execute()
            )

            return "persistent"

        except Exception as error:
            st.error(
                f"Database save failed: {error}"
            )

            return "error"

    existing_ids = [
        item.get("id", 0)
        for item
        in st.session_state.predictions
    ]

    row["id"] = (
        max(existing_ids or [0])
        + 1
    )

    st.session_state.predictions.append(
        row
    )

    return "temporary"


def remove_prediction(row_id):
    if PERSISTENT_STORAGE:
        try:
            (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .delete()
                .eq(
                    "id",
                    row_id,
                )
                .execute()
            )

            return True

        except Exception as error:
            st.error(
                f"Could not remove prediction: {error}"
            )

            return False

    st.session_state.predictions = [
        row
        for row
        in st.session_state.predictions
        if row.get("id") != row_id
    ]

    return True


def clear_all_predictions():
    if PERSISTENT_STORAGE:
        try:
            for row in fetch_predictions():
                row_id = row.get("id")

                if row_id is not None:
                    (
                        DATABASE
                        .table(
                            "prediction_tracker"
                        )
                        .delete()
                        .eq(
                            "id",
                            row_id,
                        )
                        .execute()
                    )

            return True

        except Exception as error:
            st.error(
                f"Could not clear predictions: {error}"
            )

            return False

    st.session_state.predictions = []

    return True


def update_prediction(
    row_id,
    values,
):
    if PERSISTENT_STORAGE:
        try:
            (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .update(values)
                .eq(
                    "id",
                    row_id,
                )
                .execute()
            )

            return

        except Exception as error:
            st.error(
                f"Could not update result: {error}"
            )

            return

    for row in st.session_state.predictions:
        if row.get("id") == row_id:
            row.update(values)


# ============================================================
# SETTLE PREDICTION
# ============================================================

def settle_prediction(row):
    if (
        row.get("result_status")
        == "CLOSED"
    ):
        return row

    data = daily_data(
        row["ticker"],
        "3mo",
    )

    if data.empty:
        return row

    target_date = (
        pd.to_datetime(
            row["trade_date"]
        )
        .date()
    )

    available_dates = (
        pd.to_datetime(
            data.index
        )
        .date
    )

    positions = [
        index
        for index, available_date
        in enumerate(
            available_dates
        )
        if available_date >= target_date
    ]

    if not positions:
        return row

    position = positions[0]

    actual_date = (
        available_dates[position]
    )

    # Don't close today's forecast before today's session is over.
    if (
        actual_date
        == now_et().date()
        and SESSION
        in [
            "PREMARKET",
            "REGULAR",
        ]
    ):
        return row

    daily_row = data.iloc[
        position
    ]

    def scalar(column):
        value = daily_row[column]

        if isinstance(
            value,
            pd.Series,
        ):
            value = value.iloc[0]

        return float(value)

    close_price = scalar(
        "Close"
    )

    day_high = scalar(
        "High"
    )

    day_low = scalar(
        "Low"
    )

    start_price = float(
        row["start_price"]
    )

    prediction = row[
        "prediction"
    ]

    if prediction == "UP":
        direction_correct = (
            close_price > start_price
        )

    elif prediction == "DOWN":
        direction_correct = (
            close_price < start_price
        )

    else:
        direction_correct = None

    predicted_close = row.get(
        "eod_predicted_close"
    )

    eod_error_abs = None
    eod_error_pct = None

    if (
        predicted_close is not None
        and float(predicted_close) > 0
    ):
        predicted_close = float(
            predicted_close
        )

        eod_error_abs = abs(
            close_price
            - predicted_close
        )

        eod_error_pct = (
            eod_error_abs
            / close_price
        )

    range_low = row.get(
        "eod_range_low"
    )

    range_high = row.get(
        "eod_range_high"
    )

    eod_range_hit = None

    if (
        range_low is not None
        and range_high is not None
    ):
        eod_range_hit = (
            float(range_low)
            <= close_price
            <= float(range_high)
        )

    values = {
        "close_price":
            close_price,

        "day_high":
            day_high,

        "day_low":
            day_low,

        "direction_correct":
            direction_correct,

        "stop_hit":
            (
                day_low
                <= float(
                    row["stop_price"]
                )
            ),

        "target1_hit":
            (
                day_high
                >= float(
                    row["target1"]
                )
            ),

        "target2_hit":
            (
                day_high
                >= float(
                    row["target2"]
                )
            ),

        "eod_error_abs":
            eod_error_abs,

        "eod_error_pct":
            eod_error_pct,

        "eod_range_hit":
            eod_range_hit,

        "result_status":
            "CLOSED",
    }

    update_prediction(
        row["id"],
        values,
    )

    row.update(values)

    return row


# ============================================================
# DISPLAY
# ============================================================

def show_eod_forecast(result):
    st.subheader(
        "End-of-Day Forecast"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Predicted close",
        f"${result['eod_predicted_close']:.2f}",
        f"{result['eod_predicted_move']:+.2%}",
    )

    col2.metric(
        "Confidence",
        f"{result['eod_confidence']}%",
    )

    st.write(
        f"**Expected direction:** "
        f"{result['eod_direction']}"
    )

    st.write(
        f"**Likely closing range:** "
        f"${result['eod_range_low']:.2f} – "
        f"${result['eod_range_high']:.2f}"
    )

    if SESSION in [
        "AFTERHOURS",
        "WEEKEND",
    ]:
        st.caption(
            "Market is closed, so this is effectively a forecast "
            "for the next trading session."
        )

    else:
        st.caption(
            "The forecast can change during the day as price, "
            "volume, VWAP and momentum change."
        )


def show_trade(result):
    st.subheader(
        result["action"]
    )

    st.metric(
        "CURRENT PRICE",
        f"${result['current']:.2f}",
    )

    st.caption(
        f"Price source: "
        f"{result['price_label']}"
    )

    show_eod_forecast(
        result
    )

    st.divider()

    st.markdown(
        f"""
### BUY ZONE
**${result['entry_low']:.2f} – ${result['entry_high']:.2f}**

### STOP / EXIT
**${result['stop']:.2f}**

### SELL TARGET 1
**${result['target1']:.2f}**

### SELL TARGET 2
**${result['target2']:.2f}**
"""
    )

    st.write(
        f"Day / Swing / Quality: "
        f"**{result['day']} / "
        f"{result['swing']} / "
        f"{result['quality']}**"
    )

    st.write(
        f"RSI: "
        f"**{result['rsi']:.0f}**"
    )

    st.write(
        f"Prediction: "
        f"**{result['prediction']}**"
    )

    st.write(
        f"Risk / Reward to T1: "
        f"**1:{result['rr1']:.1f}**"
    )


def track_button(
    result,
    key,
):
    trade_date = (
        prediction_trade_date()
    )

    if already_tracked(
        result["ticker"],
        trade_date,
    ):
        st.success(
            f"Tracked ✓ for "
            f"{trade_date}"
        )

        return

    if st.button(
        "📌 Track this prediction",
        key=key,
        use_container_width=True,
    ):
        mode = save_prediction(
            result
        )

        if mode == "duplicate":
            st.info(
                "Already tracked for this trading session."
            )

        elif mode == "persistent":
            st.success(
                "Prediction and EOD forecast saved permanently."
            )

        elif mode == "temporary":
            st.success(
                "Prediction saved for this session."
            )

        st.write(
            f"Tracker now contains "
            f"**{len(fetch_predictions())}** "
            f"prediction(s)."
        )


# ============================================================
# HOLDINGS / WATCHLIST
# ============================================================

try:
    saved_holdings = (
        st.query_params.get(
            "holdings",
            "TRP.TO",
        )
    )

    saved_watchlist = (
        st.query_params.get(
            "watchlist",
            "",
        )
    )

except Exception:
    saved_holdings = "TRP.TO"
    saved_watchlist = ""


st.subheader(
    "My Holdings"
)

holdings_text = st.text_input(
    "Stocks / ETFs you own",
    value=saved_holdings,
)

st.subheader(
    "⭐ My Watchlist"
)

watchlist_text = st.text_input(
    "Stocks / ETFs you want to watch",
    value=saved_watchlist,
)

holdings = [
    normalize_ticker(item)
    for item
    in holdings_text.split(",")
    if item.strip()
]

watchlist = [
    normalize_ticker(item)
    for item
    in watchlist_text.split(",")
    if item.strip()
]


if st.button(
    "💾 Save My Stocks",
    use_container_width=True,
):
    st.query_params[
        "holdings"
    ] = ",".join(
        holdings
    )

    st.query_params[
        "watchlist"
    ] = ",".join(
        watchlist
    )

    st.success(
        "Saved."
    )


# ============================================================
# TABS
# ============================================================

scan_tab, my_tab, analyze_tab, tracker_tab = st.tabs(
    [
        "Scanner",
        "⭐ My Stocks",
        "Analyze",
        "📊 Prediction Tracker",
    ]
)


# ============================================================
# SCANNER
# ============================================================

with scan_tab:
    market_choice = st.selectbox(
        "Market",
        [
            "TSX",
            "S&P 500",
            "Nasdaq-100",
            "Canadian ETFs",
            "All Markets",
        ],
    )

    count = st.selectbox(
        "Number to scan",
        [
            10,
            20,
            30,
            50,
        ],
        index=1,
    )

    if st.button(
        "🔎 Scan Now",
        type="primary",
        use_container_width=True,
    ):
        if market_choice == "TSX":
            universe = list(TSX)

        elif market_choice == "S&P 500":
            universe = list(SP500)

        elif market_choice == "Nasdaq-100":
            universe = list(NASDAQ)

        elif market_choice == "Canadian ETFs":
            universe = [
                symbol + ".TO"
                for symbol
                in CANADIAN_ETFS
            ]

        else:
            universe = list(
                dict.fromkeys(
                    list(TSX)
                    + list(SP500)
                    + list(NASDAQ)
                    + [
                        symbol + ".TO"
                        for symbol
                        in CANADIAN_ETFS
                    ]
                )
            )

        universe = universe[:count]

        for ticker in (
            holdings + watchlist
        ):
            if ticker not in universe:
                universe.insert(
                    0,
                    ticker,
                )

        results = []

        progress = st.progress(0)
        status = st.empty()

        for index, ticker in enumerate(
            universe
        ):
            status.write(
                f"Analyzing {ticker}..."
            )

            result = analyze(
                ticker
            )

            if result:
                results.append(
                    result
                )

            progress.progress(
                (index + 1)
                / len(universe)
            )

        progress.empty()
        status.empty()

        st.session_state.scanner_results = sorted(
            results,
            key=lambda item:
                item["rank"],
            reverse=True,
        )

    results = (
        st.session_state
        .scanner_results
    )

    if results:
        best = results[0]

        st.subheader(
            "🏆 Best Current Setup"
        )

        st.header(
            best["ticker"]
        )

        st.write(
            best["name"]
        )

        show_trade(
            best
        )

        track_button(
            best,
            "best_track",
        )

        st.divider()

        if st.button(
            "📌 Track all scanner results",
            use_container_width=True,
        ):
            saved_count = 0
            duplicate_count = 0

            for result in results:
                mode = save_prediction(
                    result
                )

                if mode == "duplicate":
                    duplicate_count += 1

                elif mode in [
                    "persistent",
                    "temporary",
                ]:
                    saved_count += 1

            st.success(
                f"Saved {saved_count} prediction(s). "
                f"{duplicate_count} already tracked."
            )

        st.subheader(
            "Top Opportunities"
        )

        for index, result in enumerate(
            results[:10]
        ):
            with st.expander(
                f"{result['ticker']} — "
                f"{result['action']}"
            ):
                st.write(
                    f"**{result['name']}**"
                )

                show_trade(
                    result
                )

                track_button(
                    result,
                    f"scan_track_{index}",
                )


# ============================================================
# MY STOCKS
# ============================================================

with my_tab:
    personal = list(
        dict.fromkeys(
            holdings
            + watchlist
        )
    )

    if st.button(
        "Refresh My Stocks",
        use_container_width=True,
    ):
        refreshed = []

        for ticker in personal:
            result = analyze(
                ticker
            )

            if result:
                refreshed.append(
                    result
                )

        st.session_state.my_stock_results = (
            refreshed
        )

    results = (
        st.session_state
        .my_stock_results
    )

    if watchlist:
        if st.button(
            "📌 Track all watchlist",
            use_container_width=True,
        ):
            saved_count = 0
            duplicate_count = 0

            for ticker in watchlist:
                result = analyze(
                    ticker
                )

                if result is None:
                    continue

                mode = save_prediction(
                    result
                )

                if mode == "duplicate":
                    duplicate_count += 1

                elif mode in [
                    "persistent",
                    "temporary",
                ]:
                    saved_count += 1

            st.success(
                f"Saved {saved_count} "
                f"watchlist prediction(s). "
                f"{duplicate_count} already tracked."
            )

    for index, result in enumerate(
        results
    ):
        st.header(
            result["ticker"]
        )

        if (
            result["ticker"]
            in holdings
        ):
            st.caption(
                "OWNED"
            )

        else:
            st.caption(
                "WATCHLIST"
            )

        show_trade(
            result
        )

        track_button(
            result,
            f"my_track_{index}",
        )

        st.divider()


# ============================================================
# ANALYZE
# ============================================================

with analyze_tab:
    raw_ticker = st.text_input(
        "Enter ticker",
        value="CVE",
    )

    ticker = normalize_ticker(
        raw_ticker
    )

    if (
        ticker
        != raw_ticker
        .strip()
        .upper()
    ):
        st.caption(
            f"Using ticker: "
            f"**{ticker}**"
        )

    if st.button(
        "Analyze",
        use_container_width=True,
    ):
        result = analyze(
            ticker
        )

        if result is None:
            st.session_state.analysis_result = None

            st.error(
                "No usable market data was found."
            )

        else:
            st.session_state.analysis_result = (
                result
            )

    result = (
        st.session_state
        .analysis_result
    )

    if result is not None:
        st.header(
            result["ticker"]
        )

        st.write(
            result["name"]
        )

        show_trade(
            result
        )

        track_button(
            result,
            "single_track",
        )


# ============================================================
# PREDICTION TRACKER
# ============================================================

with tracker_tab:
    st.subheader(
        "Prediction Tracker"
    )

    if PERSISTENT_STORAGE:
        st.success(
            "Persistent storage connected."
        )

    else:
        st.warning(
            "Temporary storage only."
        )

    rows = fetch_predictions()

    st.metric(
        "Tracked Predictions",
        len(rows),
    )

    # ========================================================
    # CONTROLS
    # ========================================================

    if rows:
        st.subheader(
            "Tracker Controls"
        )

        if st.button(
            "🧹 Clear All Tracked Predictions",
            type="secondary",
            use_container_width=True,
        ):
            if clear_all_predictions():
                st.success(
                    "All tracked predictions removed."
                )

                st.rerun()

    # ========================================================
    # UPDATE
    # ========================================================

    if st.button(
        "🔄 Update results",
        use_container_width=True,
    ):
        updated_count = 0

        for row in rows:
            before = row.get(
                "result_status"
            )

            result = settle_prediction(
                row
            )

            if (
                before != "CLOSED"
                and result.get(
                    "result_status"
                ) == "CLOSED"
            ):
                updated_count += 1

        st.success(
            f"Updated "
            f"{updated_count} prediction(s)."
        )

        rows = fetch_predictions()

    # ========================================================
    # CLOSED
    # ========================================================

    closed = [
        row
        for row
        in rows
        if row.get(
            "result_status"
        ) == "CLOSED"
    ]

    # ========================================================
    # OVERALL STATS
    # ========================================================

    if closed:
        scored = [
            row
            for row
            in closed
            if row.get(
                "direction_correct"
            ) is not None
        ]

        correct = sum(
            1
            for row
            in scored
            if row.get(
                "direction_correct"
            ) is True
        )

        directional_accuracy = (
            correct
            / len(scored)
            if scored
            else None
        )

        eod_scored = [
            row
            for row
            in closed
            if row.get(
                "eod_error_pct"
            ) is not None
        ]

        mean_eod_error = (
            np.mean(
                [
                    float(
                        row["eod_error_pct"]
                    )
                    for row
                    in eod_scored
                ]
            )
            if eod_scored
            else None
        )

        range_scored = [
            row
            for row
            in closed
            if row.get(
                "eod_range_hit"
            ) is not None
        ]

        range_hits = sum(
            bool(
                row.get(
                    "eod_range_hit"
                )
            )
            for row
            in range_scored
        )

        range_accuracy = (
            range_hits
            / len(range_scored)
            if range_scored
            else None
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Closed",
            len(closed),
        )

        col2.metric(
            "Direction accuracy",
            (
                f"{directional_accuracy:.1%}"
                if directional_accuracy
                is not None
                else "—"
            ),
        )

        col3, col4 = st.columns(2)

        col3.metric(
            "Avg EOD error",
            (
                f"{mean_eod_error:.2%}"
                if mean_eod_error
                is not None
                else "—"
            ),
        )

        col4.metric(
            "EOD range hit",
            (
                f"{range_accuracy:.1%}"
                if range_accuracy
                is not None
                else "—"
            ),
        )

        col5, col6 = st.columns(2)

        col5.metric(
            "Target 1 hits",
            sum(
                bool(
                    row.get(
                        "target1_hit"
                    )
                )
                for row
                in closed
            ),
        )

        col6.metric(
            "Stops hit",
            sum(
                bool(
                    row.get(
                        "stop_hit"
                    )
                )
                for row
                in closed
            ),
        )

    if not rows:
        st.info(
            "No tracked predictions yet."
        )

    # ========================================================
    # INDIVIDUAL ROWS
    # ========================================================

    for index, row in enumerate(
        rows
    ):
        if (
            row.get(
                "direction_correct"
            ) is True
        ):
            icon = "✅"

        elif (
            row.get(
                "direction_correct"
            ) is False
        ):
            icon = "❌"

        else:
            icon = "⏳"

        with st.expander(
            f"{icon} "
            f"{row['ticker']} — "
            f"{row['prediction']} — "
            f"{row['trade_date']} — "
            f"{row.get('result_status', 'OPEN')}"
        ):
            st.write(
                f"Tracked at: "
                f"**{row['tracked_at']}**"
            )

            st.write(
                f"Start price: "
                f"**${float(row['start_price']):.2f}**"
            )

            st.write(
                f"Day / Swing / Quality: "
                f"**{row['day_score']} / "
                f"{row['swing_score']} / "
                f"{row['quality_score']}**"
            )

            st.write(
                f"Original signal: "
                f"**{row['action']}**"
            )

            st.subheader(
                "Saved EOD Forecast"
            )

            predicted_close = row.get(
                "eod_predicted_close"
            )

            if predicted_close is not None:
                st.write(
                    f"Predicted close: "
                    f"**${float(predicted_close):.2f}**"
                )

            if (
                row.get(
                    "eod_range_low"
                ) is not None
                and row.get(
                    "eod_range_high"
                ) is not None
            ):
                st.write(
                    f"Predicted range: "
                    f"**${float(row['eod_range_low']):.2f} "
                    f"– "
                    f"${float(row['eod_range_high']):.2f}**"
                )

            if row.get(
                "eod_confidence"
            ) is not None:
                st.write(
                    f"EOD confidence: "
                    f"**{int(row['eod_confidence'])}%**"
                )

            st.divider()

            st.write(
                f"Buy zone: "
                f"**${float(row['entry_low']):.2f} "
                f"– "
                f"${float(row['entry_high']):.2f}**"
            )

            st.write(
                f"Stop: "
                f"**${float(row['stop_price']):.2f}**"
            )

            st.write(
                f"Target 1: "
                f"**${float(row['target1']):.2f}**"
            )

            st.write(
                f"Target 2: "
                f"**${float(row['target2']):.2f}**"
            )

            row_id = row.get(
                "id"
            )

            if row_id is not None:
                if st.button(
                    f"🗑 Remove {row['ticker']}",
                    key=(
                        f"remove_prediction_"
                        f"{row_id}_{index}"
                    ),
                    use_container_width=True,
                ):
                    if remove_prediction(
                        row_id
                    ):
                        st.success(
                            f"{row['ticker']} removed."
                        )

                        st.rerun()

            # =================================================
            # ACTUAL RESULT
            # =================================================

            if (
                row.get(
                    "result_status"
                ) == "CLOSED"
            ):
                close_price = float(
                    row["close_price"]
                )

                start_price = float(
                    row["start_price"]
                )

                change = (
                    close_price
                    / start_price
                    - 1
                )

                st.divider()

                st.subheader(
                    "Actual Result"
                )

                st.write(
                    f"Closing price: "
                    f"**${close_price:.2f}**"
                )

                st.write(
                    f"Start-to-close change: "
                    f"**{change:+.2%}**"
                )

                st.write(
                    f"Day High: "
                    f"**${float(row['day_high']):.2f}**"
                )

                st.write(
                    f"Day Low: "
                    f"**${float(row['day_low']):.2f}**"
                )

                if (
                    row.get(
                        "direction_correct"
                    ) is True
                ):
                    st.success(
                        "Direction prediction: CORRECT"
                    )

                elif (
                    row.get(
                        "direction_correct"
                    ) is False
                ):
                    st.error(
                        "Direction prediction: WRONG"
                    )

                else:
                    st.info(
                        "Neutral prediction — not scored."
                    )

                # EOD forecast result
                if row.get(
                    "eod_error_abs"
                ) is not None:
                    st.subheader(
                        "EOD Forecast Result"
                    )

                    st.write(
                        f"Predicted close: "
                        f"**${float(row['eod_predicted_close']):.2f}**"
                    )

                    st.write(
                        f"Actual close: "
                        f"**${close_price:.2f}**"
                    )

                    st.write(
                        f"Forecast missed by: "
                        f"**${float(row['eod_error_abs']):.2f}**"
                    )

                    st.write(
                        f"Forecast error: "
                        f"**{float(row['eod_error_pct']):.2%}**"
                    )

                    if (
                        row.get(
                            "eod_range_hit"
                        ) is True
                    ):
                        st.success(
                            "Actual close landed inside predicted range."
                        )

                    elif (
                        row.get(
                            "eod_range_hit"
                        ) is False
                    ):
                        st.error(
                            "Actual close finished outside predicted range."
                        )

                st.write(
                    f"Target 1 hit: "
                    f"**{'YES' if row.get('target1_hit') else 'NO'}**"
                )

                st.write(
                    f"Target 2 hit: "
                    f"**{'YES' if row.get('target2_hit') else 'NO'}**"
                )

                st.write(
                    f"Stop hit: "
                    f"**{'YES' if row.get('stop_hit') else 'NO'}**"
                )

    # ========================================================
    # CSV
    # ========================================================

    if closed:
        tracker_df = pd.DataFrame(
            closed
        )

        st.download_button(
            "Download results CSV",
            tracker_df.to_csv(
                index=False
            ),
            "prediction_results.csv",
            "text/csv",
            use_container_width=True,
        )


# ============================================================
# HELP
# ============================================================

with st.expander(
    "How the Prediction Tracker works"
):
    st.markdown(
        """
### End-of-Day forecast

The app now records:

- Current price
- Predicted closing price
- Likely closing range
- Predicted move
- EOD confidence

During the trading day, the forecast can change as live price,
VWAP, RSI, momentum and market conditions change.

### Track a prediction

Press **Track this prediction** to freeze the forecast at that moment.

That is important: once tracked, the saved prediction does not change
later just because the market moved.

### After the trading session

Press **Update results**.

The tracker then records:

- Actual close
- Actual high / low
- Direction correct / wrong
- Target 1 hit
- Target 2 hit
- Stop hit
- EOD price forecast error
- Whether the actual close landed inside the predicted range

Over time this allows us to measure whether the model actually has an edge.
"""
    )


st.divider()

st.caption(
    f"Page refreshed: "
    f"{now_et().strftime('%I:%M:%S %p ET')} "
    f"• Session: {SESSION_LABEL}"
)
