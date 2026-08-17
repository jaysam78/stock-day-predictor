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
    "Market scanner • Best Today • 2–5 Day setups • EOD forecast • "
    "watchlist • prediction tracker"
)

st.warning(
    "Signals, forecasts and trade levels are model estimates for research only. "
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
        np.clip(
            elapsed / total,
            0.0,
            1.0,
        )
    )


# ============================================================
# CANADIAN ETFs
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
    "ZSP": "BMO S&P 500 Index ETF",
    "QQC": "Invesco NASDAQ 100 Index ETF",
    "ZAG": "BMO Aggregate Bond Index ETF",
    "VAB": "Vanguard Canadian Aggregate Bond Index ETF",
}


# ============================================================
# LARGER TSX SCANNER UNIVERSE
# ============================================================

TSX = {
    # Banks / financials
    "RY.TO": "Royal Bank",
    "TD.TO": "TD Bank",
    "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank",
    "CM.TO": "CIBC",
    "NA.TO": "National Bank",
    "MFC.TO": "Manulife",
    "SLF.TO": "Sun Life",
    "GWO.TO": "Great-West Lifeco",
    "POW.TO": "Power Corporation",
    "IFC.TO": "Intact Financial",
    "FFH.TO": "Fairfax Financial",
    "BAM.TO": "Brookfield Asset Management",
    "BN.TO": "Brookfield Corporation",

    # Energy / pipelines
    "CNQ.TO": "Canadian Natural Resources",
    "SU.TO": "Suncor",
    "CVE.TO": "Cenovus",
    "IMO.TO": "Imperial Oil",
    "MEG.TO": "MEG Energy",
    "ARX.TO": "ARC Resources",
    "TOU.TO": "Tourmaline Oil",
    "WCP.TO": "Whitecap Resources",
    "PEY.TO": "Peyto Exploration",
    "CPG.TO": "Crescent Point / Veren",
    "ENB.TO": "Enbridge",
    "TRP.TO": "TC Energy",
    "PPL.TO": "Pembina Pipeline",
    "KEY.TO": "Keyera",

    # Mining / materials
    "AEM.TO": "Agnico Eagle",
    "ABX.TO": "Barrick Mining",
    "WPM.TO": "Wheaton Precious Metals",
    "K.TO": "Kinross Gold",
    "FNV.TO": "Franco-Nevada",
    "LUG.TO": "Lundin Gold",
    "NTR.TO": "Nutrien",
    "TECK-B.TO": "Teck Resources",
    "FM.TO": "First Quantum Minerals",
    "HBM.TO": "Hudbay Minerals",
    "CCO.TO": "Cameco",
    "IVN.TO": "Ivanhoe Mines",
    "ERO.TO": "Ero Copper",
    "LUN.TO": "Lundin Mining",
    "AGI.TO": "Alamos Gold",

    # Technology
    "SHOP.TO": "Shopify",
    "CSU.TO": "Constellation Software",
    "OTEX.TO": "OpenText",
    "KXS.TO": "Kinaxis",
    "DSG.TO": "Descartes Systems",
    "ENGH.TO": "Enghouse Systems",
    "DCBO.TO": "Docebo",

    # Industrials
    "CNR.TO": "Canadian National Railway",
    "CP.TO": "CPKC",
    "WSP.TO": "WSP Global",
    "TFII.TO": "TFI International",
    "CAE.TO": "CAE",
    "ATS.TO": "ATS Corporation",
    "TIH.TO": "Toromont Industries",
    "STN.TO": "Stantec",
    "GFL.TO": "GFL Environmental",
    "CCL-B.TO": "CCL Industries",

    # Consumer
    "ATD.TO": "Couche-Tard",
    "L.TO": "Loblaw",
    "MRU.TO": "Metro",
    "DOL.TO": "Dollarama",
    "CTC-A.TO": "Canadian Tire",
    "QSR.TO": "Restaurant Brands",
    "MG.TO": "Magna International",
    "GIL.TO": "Gildan Activewear",
    "WN.TO": "George Weston",

    # Utilities
    "FTS.TO": "Fortis",
    "EMA.TO": "Emera",
    "AQN.TO": "Algonquin Power",
    "CPX.TO": "Capital Power",
    "CU.TO": "Canadian Utilities",
    "NPI.TO": "Northland Power",
    "BEPC.TO": "Brookfield Renewable",

    # Telecom / media
    "BCE.TO": "BCE",
    "T.TO": "TELUS",
    "RCI-B.TO": "Rogers Communications",
    "QBR-B.TO": "Quebecor",

    # Real estate
    "CAR-UN.TO": "Canadian Apartment REIT",
    "REI-UN.TO": "RioCan REIT",
    "SRU-UN.TO": "SmartCentres REIT",
    "DIR-UN.TO": "Dream Industrial REIT",
    "GRT-UN.TO": "Granite REIT",

    # Other large / liquid names
    "SAP.TO": "Saputo",
    "CCL-B.TO": "CCL Industries",
    "STLC.TO": "Stelco",
    "SJ.TO": "Stella-Jones",
    "DOO.TO": "BRP",
    "ATZ.TO": "Aritzia",
    "TFPM.TO": "Triple Flag Precious Metals",
    "CLS.TO": "Celestica",
}


# ============================================================
# U.S. UNIVERSES
# ============================================================

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
    "UNH": "UnitedHealth",
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
    "GE": "GE Aerospace",
    "CAT": "Caterpillar",
    "DE": "Deere",
    "BA": "Boeing",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "ABBV": "AbbVie",
    "MRK": "Merck",
    "PFE": "Pfizer",
    "TMO": "Thermo Fisher",
    "AMGN": "Amgen",
    "NOW": "ServiceNow",
    "IBM": "IBM",
    "INTU": "Intuit",
    "PYPL": "PayPal",
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
    "SMCI": "Super Micro Computer",
    "APP": "AppLovin",
    "FTNT": "Fortinet",
    "MELI": "MercadoLibre",
    "BKNG": "Booking Holdings",
    "ABNB": "Airbnb",
    "TEAM": "Atlassian",
    "DDOG": "Datadog",
    "ZS": "Zscaler",
    "MDB": "MongoDB",
    "SNPS": "Synopsys",
    "CDNS": "Cadence Design Systems",
}


ALL_NAMES = {}
ALL_NAMES.update(TSX)
ALL_NAMES.update(SP500)
ALL_NAMES.update(NASDAQ)

for symbol, name in CANADIAN_ETFS.items():
    ALL_NAMES[f"{symbol}.TO"] = name


# ============================================================
# BASIC HELPERS
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


def pct_distance(current, level):
    if (
        current is None
        or level is None
        or current == 0
    ):
        return None

    return level / current - 1


def confidence_label(score):
    if score < 60:
        return "LOW"

    if score < 70:
        return "MODERATE"

    if score < 80:
        return "HIGH"

    return "VERY HIGH"


def colored_change(value, suffix=""):
    if value is None:
        return "—"

    if value > 0:
        color = "#16a34a"

    elif value < 0:
        color = "#dc2626"

    else:
        color = "#6b7280"

    return (
        f"<span style='color:{color};font-weight:700;'>"
        f"{value:+.2f}{suffix}</span>"
    )


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
    if (
        df is None
        or df.empty
        or column not in df.columns
    ):
        return pd.Series(dtype=float)

    result = df[column]

    if isinstance(result, pd.DataFrame):
        result = result.iloc[:, 0]

    return pd.to_numeric(
        result,
        errors="coerce",
    )


def latest_move(ticker):
    data = daily_data(
        ticker,
        "1mo",
    )

    close = get_series(
        data,
        "Close",
    ).dropna()

    if len(close) < 2:
        return 0.0

    return float(
        close.iloc[-1]
        / close.iloc[-2]
        - 1
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

    rs = gains / losses.replace(
        0,
        np.nan,
    )

    return (
        100
        - 100 / (1 + rs)
    )


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

    return (
        true_range
        .rolling(period)
        .mean()
    )


def calculate_vwap(ticker):
    data = intraday_data(
        ticker
    )

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

    return float(
        vwap.iloc[-1]
    )


# ============================================================
# CURRENT PRICE
# ============================================================

def price_info(ticker):
    intra = intraday_data(
        ticker
    )

    daily = daily_data(
        ticker,
        "1mo",
    )

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
# EOD FORECAST
# ============================================================

def make_eod_forecast(
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
    if (
        previous_close is None
        or previous_close <= 0
    ):
        previous_close = current

    ret1 = float(
        close.pct_change(1).iloc[-1]
    )

    ret3 = float(
        close.pct_change(3).iloc[-1]
    )

    ret5 = float(
        close.pct_change(5).iloc[-1]
    )

    current_move = (
        current
        / previous_close
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

    momentum_expectation = (
        0.30 * ret1
        + 0.20 * (ret3 / 3)
        + 0.15 * (ret5 / 5)
        + 0.20 * market_move
    )

    rsi_bias = (
        (rsi_value - 50)
        / 50
        * 0.0035
    )

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
        expected_return = (
            elapsed * current_move
            + (1 - elapsed)
            * base_expected_move
        )

    elif SESSION == "PREMARKET":
        expected_return = (
            0.20 * current_move
            + 0.80 * base_expected_move
        )

    else:
        expected_return = (
            base_expected_move
        )

    predicted_close = (
        previous_close
        * (
            1
            + expected_return
        )
    )

    movement_cap = max(
        atr_value * 1.50,
        current * 0.01,
    )

    predicted_close = float(
        np.clip(
            predicted_close,
            current - movement_cap,
            current + movement_cap,
        )
    )

    if SESSION == "REGULAR":
        remaining_fraction = max(
            0.10,
            1 - elapsed,
        )

    else:
        remaining_fraction = 1.0

    uncertainty = max(
        atr_value
        * (
            0.30
            + 0.55
            * remaining_fraction
        ),
        current
        * daily_volatility
        * 0.35,
    )

    forecast_low = max(
        0.01,
        predicted_close
        - uncertainty,
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

    predicted_move = (
        predicted_close
        / current
        - 1
    )

    if predicted_move > 0.001:
        direction = "UP"

    elif predicted_move < -0.001:
        direction = "DOWN"

    else:
        direction = "FLAT"

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
            float(predicted_move),

        "eod_direction":
            direction,
    }


# ============================================================
# ENTRY / SETUP INTERPRETATION
# ============================================================

def entry_status(result):
    current = result["current"]
    low = result["entry_low"]
    high = result["entry_high"]
    stop = result["stop"]

    if current <= stop * 1.02:
        return "NEAR STOP — HIGH RISK"

    if current < low:
        return "BELOW BUY ZONE"

    if low <= current <= high:
        return "INSIDE BUY ZONE"

    return "ABOVE BUY ZONE — DON'T CHASE"


def setup_quality(result):
    score = (
        0.35 * result["day"]
        + 0.30 * result["swing"]
        + 0.35 * result["quality"]
    )

    if result["rr1"] < 1.5:
        score -= 8

    if result["rsi"] >= 75:
        score -= 7

    if score >= 78:
        return "STRONG"

    if score >= 68:
        return "GOOD"

    if score >= 55:
        return "MIXED"

    return "WEAK"


# ============================================================
# TODAY RANKING
# ============================================================

def calculate_today_rank(result):
    """
    Designed to answer:
    Which stocks look most attractive for the CURRENT SESSION?
    """

    score = (
        result["day"] * 0.32
        + result["quality"] * 0.24
        + result["eod_confidence"] * 0.12
        + result["swing"] * 0.08
    )

    # Remaining expected EOD movement
    eod_move = result[
        "eod_predicted_move"
    ]

    eod_component = float(
        np.clip(
            eod_move / 0.02,
            -1,
            1,
        )
    )

    score += (
        eod_component * 10
    )

    # Entry status
    status = entry_status(
        result
    )

    if status == "INSIDE BUY ZONE":
        score += 9

    elif status == "BELOW BUY ZONE":
        score += 2

    elif (
        status
        == "ABOVE BUY ZONE — DON'T CHASE"
    ):
        score -= 8

    elif (
        status
        == "NEAR STOP — HIGH RISK"
    ):
        score -= 12

    # Risk / reward
    if result["rr1"] >= 2.0:
        score += 6

    elif result["rr1"] >= 1.5:
        score += 3

    else:
        score -= 8

    # Relative volume
    if result["relative_volume"] >= 1.5:
        score += 7

    elif result["relative_volume"] >= 1.2:
        score += 4

    elif result["relative_volume"] < 0.70:
        score -= 4

    # VWAP
    if (
        SESSION == "REGULAR"
        and result["vwap"] is not None
    ):
        if (
            result["current"]
            >= result["vwap"]
        ):
            score += 6

        else:
            score -= 6

    # RSI
    if 50 <= result["rsi"] <= 68:
        score += 4

    elif result["rsi"] >= 78:
        score -= 10

    elif result["rsi"] >= 72:
        score -= 5

    # Market alignment
    if (
        result["prediction"] == "UP"
        and result["market_move"] > 0
    ):
        score += 3

    elif (
        result["prediction"] == "DOWN"
        and result["market_move"] < 0
    ):
        score += 3

    return float(
        np.clip(
            score,
            0,
            100,
        )
    )


# ============================================================
# SWING RANKING
# ============================================================

def calculate_swing_rank(result):
    """
    Designed to answer:
    Which stocks have the better 2–5 trading day setup?
    """

    score = (
        result["swing"] * 0.42
        + result["quality"] * 0.25
        + result["day"] * 0.15
        + result["eod_confidence"] * 0.08
    )

    if result["rr1"] >= 2.0:
        score += 6

    elif result["rr1"] >= 1.5:
        score += 3

    else:
        score -= 6

    if result["rsi"] >= 80:
        score -= 8

    elif 50 <= result["rsi"] <= 70:
        score += 3

    if result["relative_volume"] >= 1.2:
        score += 3

    if (
        result["prediction"] == "UP"
        and result["market_move"] > 0
    ):
        score += 2

    return float(
        np.clip(
            score,
            0,
            100,
        )
    )


# ============================================================
# MAIN ANALYSIS
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

    ret1 = (
        close
        .pct_change(1)
        .iloc[-1]
    )

    ret3 = (
        close
        .pct_change(3)
        .iloc[-1]
    )

    ret5 = (
        close
        .pct_change(5)
        .iloc[-1]
    )

    ret20 = (
        close
        .pct_change(20)
        .iloc[-1]
    )

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
        calculate_rsi(
            close
        )
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

    if is_canadian_etf(
        ticker
    ):
        day_score = (
            50
            + (
                day_score
                - 50
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

    if is_canadian_etf(
        ticker
    ):
        swing_score = (
            50
            + (
                swing_score
                - 50
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
    # QUALITY
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
    # ATR / LEVELS
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
        resistance
        + atr_value,

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

        "market_move":
            float(market_move),
    }

    result.update(eod)

    result["today_rank"] = (
        calculate_today_rank(
            result
        )
    )

    result["swing_rank"] = (
        calculate_swing_rank(
            result
        )
    )

    return result


# ============================================================
# INSIGHTS
# ============================================================

def build_insights(result):
    insights = []

    if result["day"] >= 70:
        insights.append(
            "Short-term momentum is supportive."
        )

    elif result["day"] <= 45:
        insights.append(
            "Short-term momentum is weak."
        )

    if result["swing"] >= 75:
        insights.append(
            "The 2–5 day swing setup is strong."
        )

    if 50 <= result["rsi"] <= 68:
        insights.append(
            "RSI is in a healthy momentum range."
        )

    elif result["rsi"] >= 75:
        insights.append(
            "RSI is elevated, increasing chase risk."
        )

    if (
        SESSION == "REGULAR"
        and result["vwap"] is not None
    ):
        if (
            result["current"]
            >= result["vwap"]
        ):
            insights.append(
                "Price is above VWAP, supporting the intraday setup."
            )

        else:
            insights.append(
                "Price is below VWAP, weakening the intraday setup."
            )

    if (
        result["relative_volume"]
        >= 1.5
    ):
        insights.append(
            "Volume is materially above normal."
        )

    elif (
        result["relative_volume"]
        < 0.8
    ):
        insights.append(
            "Volume confirmation is currently weak."
        )

    status = entry_status(
        result
    )

    if status == "INSIDE BUY ZONE":
        insights.append(
            "Current price is inside the preferred entry zone."
        )

    elif (
        status
        == "ABOVE BUY ZONE — DON'T CHASE"
    ):
        insights.append(
            "Price is above the preferred entry zone."
        )

    if (
        result[
            "eod_predicted_move"
        ] > 0.005
    ):
        insights.append(
            "The EOD model still sees meaningful upside from the current price."
        )

    elif (
        result[
            "eod_predicted_move"
        ] < -0.005
    ):
        insights.append(
            "The EOD model currently expects downside into the close."
        )

    else:
        insights.append(
            "The EOD model sees limited remaining same-day movement."
        )

    return insights


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
        next_date += timedelta(
            days=1
        )

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

            return (
                response.data
                or []
            )

        except Exception as error:
            st.error(
                f"Could not load tracker: {error}"
            )

            return []

    return list(
        st.session_state.predictions
    )


def fetch_snapshots(
    prediction_id,
):
    if not PERSISTENT_STORAGE:
        return []

    try:
        response = (
            DATABASE
            .table(
                "forecast_snapshots"
            )
            .select("*")
            .eq(
                "prediction_id",
                prediction_id,
            )
            .order(
                "snapshot_at",
                desc=False,
            )
            .execute()
        )

        return (
            response.data
            or []
        )

    except Exception:
        return []


def save_snapshot(
    prediction_id,
    result,
    trade_date,
):
    if not PERSISTENT_STORAGE:
        return False

    row = {
        "prediction_id":
            prediction_id,

        "ticker":
            result[
                "ticker"
            ],

        "trade_date":
            str(
                trade_date
            ),

        "snapshot_at":
            now_et()
            .isoformat(),

        "current_price":
            result[
                "current"
            ],

        "predicted_close":
            result[
                "eod_predicted_close"
            ],

        "predicted_range_low":
            result[
                "eod_range_low"
            ],

        "predicted_range_high":
            result[
                "eod_range_high"
            ],

        "confidence":
            result[
                "eod_confidence"
            ],

        "predicted_move":
            result[
                "eod_predicted_move"
            ],

        "day_score":
            result[
                "day"
            ],

        "swing_score":
            result[
                "swing"
            ],

        "quality_score":
            result[
                "quality"
            ],

        "rsi":
            result[
                "rsi"
            ],

        "relative_volume":
            result[
                "relative_volume"
            ],

        "vwap":
            result[
                "vwap"
            ],
    }

    try:
        (
            DATABASE
            .table(
                "forecast_snapshots"
            )
            .insert(row)
            .execute()
        )

        return True

    except Exception:
        return False


def already_tracked(
    ticker,
    trade_date,
):
    for row in fetch_predictions():
        if (
            row.get(
                "ticker"
            ) == ticker
            and str(
                row.get(
                    "trade_date"
                )
            ) == str(
                trade_date
            )
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
            result[
                "ticker"
            ],

        "tracked_at":
            now_et()
            .isoformat(),

        "trade_date":
            trade_date
            .isoformat(),

        "prediction":
            result[
                "prediction"
            ],

        "action":
            result[
                "action"
            ],

        "day_score":
            result[
                "day"
            ],

        "swing_score":
            result[
                "swing"
            ],

        "quality_score":
            result[
                "quality"
            ],

        "start_price":
            result[
                "current"
            ],

        "entry_low":
            result[
                "entry_low"
            ],

        "entry_high":
            result[
                "entry_high"
            ],

        "stop_price":
            result[
                "stop"
            ],

        "target1":
            result[
                "target1"
            ],

        "target2":
            result[
                "target2"
            ],

        # Frozen original forecast
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

        # Latest forecast
        "latest_eod_predicted_close":
            result[
                "eod_predicted_close"
            ],

        "latest_eod_range_low":
            result[
                "eod_range_low"
            ],

        "latest_eod_range_high":
            result[
                "eod_range_high"
            ],

        "latest_eod_confidence":
            result[
                "eod_confidence"
            ],

        "latest_eod_predicted_move":
            result[
                "eod_predicted_move"
            ],

        "latest_forecast_at":
            now_et()
            .isoformat(),

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
            response = (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .insert(
                    row
                )
                .execute()
            )

            inserted = (
                response.data
                or []
            )

            if inserted:
                prediction_id = (
                    inserted[0]
                    .get(
                        "id"
                    )
                )

                if (
                    prediction_id
                    is not None
                ):
                    save_snapshot(
                        prediction_id,
                        result,
                        trade_date,
                    )

            return "persistent"

        except Exception as error:
            st.error(
                f"Database save failed: {error}"
            )

            return "error"

    ids = [
        item.get(
            "id",
            0,
        )
        for item
        in st.session_state.predictions
    ]

    row["id"] = (
        max(
            ids
            or [0]
        )
        + 1
    )

    st.session_state.predictions.append(
        row
    )

    return "temporary"


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
                .update(
                    values
                )
                .eq(
                    "id",
                    row_id,
                )
                .execute()
            )

            return True

        except Exception as error:
            st.error(
                f"Could not update database: {error}"
            )

            return False

    for row in (
        st.session_state.predictions
    ):
        if (
            row.get("id")
            == row_id
        ):
            row.update(
                values
            )

    return True


def refresh_latest_forecast(row):
    if (
        row.get(
            "result_status"
        ) == "CLOSED"
    ):
        return False

    latest = analyze(
        row[
            "ticker"
        ]
    )

    if latest is None:
        return False

    values = {
        "latest_eod_predicted_close":
            latest[
                "eod_predicted_close"
            ],

        "latest_eod_range_low":
            latest[
                "eod_range_low"
            ],

        "latest_eod_range_high":
            latest[
                "eod_range_high"
            ],

        "latest_eod_confidence":
            latest[
                "eod_confidence"
            ],

        "latest_eod_predicted_move":
            latest[
                "eod_predicted_move"
            ],

        "latest_forecast_at":
            now_et()
            .isoformat(),
    }

    ok = update_prediction(
        row[
            "id"
        ],
        values,
    )

    if ok:
        save_snapshot(
            row[
                "id"
            ],
            latest,
            row[
                "trade_date"
            ],
        )

    return ok


def remove_prediction(
    row_id,
):
    if PERSISTENT_STORAGE:
        try:
            (
                DATABASE
                .table(
                    "forecast_snapshots"
                )
                .delete()
                .eq(
                    "prediction_id",
                    row_id,
                )
                .execute()
            )

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
        if row.get(
            "id"
        ) != row_id
    ]

    return True


def clear_all_predictions():
    if PERSISTENT_STORAGE:
        try:
            (
                DATABASE
                .table(
                    "forecast_snapshots"
                )
                .delete()
                .neq(
                    "id",
                    0,
                )
                .execute()
            )

            (
                DATABASE
                .table(
                    "prediction_tracker"
                )
                .delete()
                .neq(
                    "id",
                    0,
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


# ============================================================
# SETTLE EOD RESULT
# ============================================================

def settle_prediction(row):
    if (
        row.get(
            "result_status"
        ) == "CLOSED"
    ):
        return row

    data = daily_data(
        row[
            "ticker"
        ],
        "3mo",
    )

    if data.empty:
        return row

    target_date = (
        pd.to_datetime(
            row[
                "trade_date"
            ]
        )
        .date()
    )

    dates = (
        pd.to_datetime(
            data.index
        )
        .date
    )

    positions = [
        index
        for index, available_date
        in enumerate(
            dates
        )
        if (
            available_date
            >= target_date
        )
    ]

    if not positions:
        return row

    position = (
        positions[0]
    )

    actual_date = (
        dates[
            position
        ]
    )

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
        value = (
            daily_row[
                column
            ]
        )

        if isinstance(
            value,
            pd.Series,
        ):
            value = (
                value.iloc[0]
            )

        return float(
            value
        )

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
        row[
            "start_price"
        ]
    )

    prediction = (
        row[
            "prediction"
        ]
    )

    if prediction == "UP":
        direction_correct = (
            close_price
            > start_price
        )

    elif prediction == "DOWN":
        direction_correct = (
            close_price
            < start_price
        )

    else:
        direction_correct = None

    original_predicted_close = (
        row.get(
            "eod_predicted_close"
        )
    )

    eod_error_abs = None
    eod_error_pct = None

    if (
        original_predicted_close
        is not None
    ):
        original_predicted_close = float(
            original_predicted_close
        )

        eod_error_abs = abs(
            close_price
            - original_predicted_close
        )

        eod_error_pct = (
            eod_error_abs
            / close_price
        )

    range_low = (
        row.get(
            "eod_range_low"
        )
    )

    range_high = (
        row.get(
            "eod_range_high"
        )
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
                    row[
                        "stop_price"
                    ]
                )
            ),

        "target1_hit":
            (
                day_high
                >= float(
                    row[
                        "target1"
                    ]
                )
            ),

        "target2_hit":
            (
                day_high
                >= float(
                    row[
                        "target2"
                    ]
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
        row[
            "id"
        ],
        values,
    )

    row.update(
        values
    )

    return row


# ============================================================
# DISPLAY
# ============================================================

def show_eod_forecast(result):
    st.subheader(
        "End-of-Day Forecast"
    )

    col1, col2 = st.columns(
        2
    )

    col1.metric(
        "Predicted close",
        f"${result['eod_predicted_close']:.2f}",
        f"{result['eod_predicted_move']:+.2%}",
    )

    col2.metric(
        "Model Confidence",
        f"{result['eod_confidence']}%",
    )

    st.caption(
        f"Confidence level: "
        f"{confidence_label(result['eod_confidence'])}"
    )

    st.write(
        f"Expected direction: "
        f"**{result['eod_direction']}**"
    )

    st.write(
        f"Likely closing range: "
        f"**${result['eod_range_low']:.2f} – "
        f"${result['eod_range_high']:.2f}**"
    )


def show_insights(result):
    st.subheader(
        "Prediction Insights"
    )

    col1, col2 = st.columns(
        2
    )

    col1.metric(
        "Setup Quality",
        setup_quality(
            result
        ),
    )

    col2.metric(
        "Entry Status",
        entry_status(
            result
        ),
    )

    st.write(
        f"**Best Today score:** "
        f"{result['today_rank']:.0f}/100"
    )

    st.write(
        f"**2–5 Day score:** "
        f"{result['swing_rank']:.0f}/100"
    )

    current = result[
        "current"
    ]

    st.write(
        f"To EOD forecast: "
        f"**{pct_distance(current, result['eod_predicted_close']):+.2%}**"
    )

    st.write(
        f"To Target 1: "
        f"**{pct_distance(current, result['target1']):+.2%}**"
    )

    st.write(
        f"To Target 2: "
        f"**{pct_distance(current, result['target2']):+.2%}**"
    )

    st.write(
        f"To stop: "
        f"**{pct_distance(current, result['stop']):+.2%}**"
    )

    with st.expander(
        "Why the model sees it this way"
    ):
        for item in build_insights(
            result
        ):
            st.write(
                f"• {item}"
            )


def show_trade(result):
    st.subheader(
        result[
            "action"
        ]
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

    show_insights(
        result
    )

    st.divider()

    st.markdown(
        f"""
### BUY ZONE — preferred entry area
**${result['entry_low']:.2f} – ${result['entry_high']:.2f}**

### STOP / EXIT — risk level
**${result['stop']:.2f}**

### TARGET 1 — 2–5 day swing objective
**${result['target1']:.2f}**

### TARGET 2 — extended swing objective
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
        f"Relative Volume: "
        f"**{result['relative_volume']:.2f}×**"
    )

    if (
        result[
            "vwap"
        ]
        is not None
    ):
        st.write(
            f"VWAP: "
            f"**${result['vwap']:.2f}**"
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
        result[
            "ticker"
        ],
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

        if mode == "persistent":
            st.success(
                "Original forecast saved permanently."
            )

        elif mode == "temporary":
            st.success(
                "Forecast saved."
            )

        elif mode == "duplicate":
            st.info(
                "Already tracked."
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
    normalize_ticker(
        item
    )
    for item
    in holdings_text.split(",")
    if item.strip()
]


watchlist = [
    normalize_ticker(
        item
    )
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
# MARKET SCANNER
# ============================================================

with scan_tab:
    market_choice = st.selectbox(
        "Market",
        [
            "TSX",
            "S&P 500",
            "Nasdaq",
            "Canadian ETFs",
            "All Markets",
        ],
    )

    results_to_show = st.selectbox(
        "Number of results to show",
        [
            5,
            10,
            15,
            20,
        ],
        index=1,
    )

    st.caption(
        "The app scans the full built-in universe first, "
        "then ranks the best results. This may take longer than the old scanner."
    )

    if st.button(
        "🔎 Scan Market Now",
        type="primary",
        use_container_width=True,
    ):
        if market_choice == "TSX":
            universe = list(
                TSX.keys()
            )

        elif market_choice == "S&P 500":
            universe = list(
                SP500.keys()
            )

        elif market_choice == "Nasdaq":
            universe = list(
                NASDAQ.keys()
            )

        elif (
            market_choice
            == "Canadian ETFs"
        ):
            universe = [
                symbol
                + ".TO"
                for symbol
                in CANADIAN_ETFS
            ]

        else:
            universe = list(
                dict.fromkeys(
                    list(
                        TSX.keys()
                    )
                    + list(
                        SP500.keys()
                    )
                    + list(
                        NASDAQ.keys()
                    )
                    + [
                        symbol
                        + ".TO"
                        for symbol
                        in CANADIAN_ETFS
                    ]
                )
            )

        results = []

        total = len(
            universe
        )

        progress = st.progress(
            0
        )

        status = st.empty()

        for index, ticker in enumerate(
            universe
        ):
            status.write(
                f"Scanning {ticker} "
                f"({index + 1}/{total})..."
            )

            result = analyze(
                ticker
            )

            if result is not None:
                results.append(
                    result
                )

            progress.progress(
                (
                    index + 1
                )
                / total
            )

        progress.empty()
        status.empty()

        st.session_state.scanner_results = (
            results
        )

    results = (
        st.session_state
        .scanner_results
    )

    if results:
        st.success(
            f"Analyzed "
            f"{len(results)} usable securities."
        )

        # ====================================================
        # BEST TODAY
        # ====================================================

        today_results = sorted(
            results,
            key=lambda item:
                item[
                    "today_rank"
                ],
            reverse=True,
        )

        st.subheader(
            "🔥 Best Today"
        )

        st.caption(
            "Ranks stocks for the current trading session using "
            "Day Score, Quality, VWAP, volume, EOD upside, entry location, "
            "risk/reward, RSI and confidence."
        )

        for rank, result in enumerate(
            today_results[
                :results_to_show
            ],
            start=1,
        ):
            title = (
                f"#{rank} "
                f"{result['ticker']} — "
                f"Today {result['today_rank']:.0f}/100 — "
                f"{result['action']}"
            )

            with st.expander(
                title
            ):
                st.write(
                    f"**{result['name']}**"
                )

                show_trade(
                    result
                )

                track_button(
                    result,
                    f"today_track_"
                    f"{rank}_"
                    f"{result['ticker']}",
                )

        # ====================================================
        # BEST 2–5 DAY
        # ====================================================

        swing_results = sorted(
            results,
            key=lambda item:
                item[
                    "swing_rank"
                ],
            reverse=True,
        )

        st.subheader(
            "📈 Best 2–5 Day Setups"
        )

        st.caption(
            "Ranks stocks more heavily on Swing Score, trend quality, "
            "risk/reward and momentum persistence."
        )

        for rank, result in enumerate(
            swing_results[
                :results_to_show
            ],
            start=1,
        ):
            title = (
                f"#{rank} "
                f"{result['ticker']} — "
                f"Swing {result['swing_rank']:.0f}/100 — "
                f"{result['action']}"
            )

            with st.expander(
                title
            ):
                st.write(
                    f"**{result['name']}**"
                )

                show_trade(
                    result
                )

                track_button(
                    result,
                    f"swing_track_"
                    f"{rank}_"
                    f"{result['ticker']}",
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

    for index, result in enumerate(
        st.session_state
        .my_stock_results
    ):
        st.header(
            result[
                "ticker"
            ]
        )

        st.caption(
            "OWNED"
            if (
                result[
                    "ticker"
                ]
                in holdings
            )
            else
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
            result[
                "ticker"
            ]
        )

        st.write(
            result[
                "name"
            ]
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
        len(
            rows
        ),
    )

    open_rows = [
        row
        for row
        in rows
        if (
            row.get(
                "result_status"
            )
            != "CLOSED"
        )
    ]

    if open_rows:
        if st.button(
            "🔄 Refresh Latest Forecasts",
            type="primary",
            use_container_width=True,
        ):
            refreshed = 0

            progress = st.progress(
                0
            )

            status = st.empty()

            for index, row in enumerate(
                open_rows
            ):
                status.write(
                    f"Updating "
                    f"{row['ticker']}..."
                )

                if refresh_latest_forecast(
                    row
                ):
                    refreshed += 1

                progress.progress(
                    (
                        index + 1
                    )
                    / len(
                        open_rows
                    )
                )

            progress.empty()
            status.empty()

            st.success(
                f"Updated "
                f"{refreshed} latest forecast(s). "
                "Original forecasts were not changed."
            )

            rows = fetch_predictions()

    if st.button(
        "✅ Update End-of-Day Results",
        use_container_width=True,
    ):
        updated = 0

        for row in rows:
            before = (
                row.get(
                    "result_status"
                )
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
                updated += 1

        st.success(
            f"Closed "
            f"{updated} prediction(s)."
        )

        rows = fetch_predictions()

    if rows:
        if st.button(
            "🧹 Clear All Tracked Predictions",
            use_container_width=True,
        ):
            if clear_all_predictions():
                st.success(
                    "All predictions removed."
                )

                st.rerun()

    closed = [
        row
        for row
        in rows
        if (
            row.get(
                "result_status"
            )
            == "CLOSED"
        )
    ]

    # ========================================================
    # PERFORMANCE
    # ========================================================

    if closed:
        st.subheader(
            "Model Performance"
        )

        scored = [
            row
            for row
            in closed
            if (
                row.get(
                    "direction_correct"
                )
                is not None
            )
        ]

        correct = sum(
            1
            for row
            in scored
            if (
                row.get(
                    "direction_correct"
                )
                is True
            )
        )

        direction_accuracy = (
            correct / len(scored)
            if scored
            else None
        )

        eod_rows = [
            row
            for row
            in closed
            if (
                row.get(
                    "eod_error_pct"
                )
                is not None
            )
        ]

        avg_error_pct = (
            np.mean(
                [
                    float(
                        row[
                            "eod_error_pct"
                        ]
                    )
                    for row
                    in eod_rows
                ]
            )
            if eod_rows
            else None
        )

        avg_error_dollar = (
            np.mean(
                [
                    float(
                        row[
                            "eod_error_abs"
                        ]
                    )
                    for row
                    in eod_rows
                ]
            )
            if eod_rows
            else None
        )

        range_rows = [
            row
            for row
            in closed
            if (
                row.get(
                    "eod_range_hit"
                )
                is not None
            )
        ]

        range_hit_rate = (
            sum(
                1
                for row
                in range_rows
                if (
                    row.get(
                        "eod_range_hit"
                    )
                    is True
                )
            )
            / len(range_rows)
            if range_rows
            else None
        )

        c1, c2 = st.columns(
            2
        )

        c1.metric(
            "Direction accuracy",
            (
                f"{direction_accuracy:.1%}"
                if direction_accuracy
                is not None
                else "—"
            ),
        )

        c2.metric(
            "Avg forecast error",
            (
                f"{avg_error_pct:.2%}"
                if avg_error_pct
                is not None
                else "—"
            ),
        )

        c3, c4 = st.columns(
            2
        )

        c3.metric(
            "Avg dollar miss",
            (
                f"${avg_error_dollar:.2f}"
                if avg_error_dollar
                is not None
                else "—"
            ),
        )

        c4.metric(
            "Range hit rate",
            (
                f"{range_hit_rate:.1%}"
                if range_hit_rate
                is not None
                else "—"
            ),
        )

        if len(closed) < 20:
            st.info(
                f"Only {len(closed)} completed forecast(s). "
                "Treat these statistics as preliminary."
            )

    if not rows:
        st.info(
            "No tracked predictions yet."
        )

    # ========================================================
    # INDIVIDUAL TRACKED PREDICTIONS
    # ========================================================

    for index, row in enumerate(
        rows
    ):
        if (
            row.get(
                "direction_correct"
            )
            is True
        ):
            icon = "✅"

        elif (
            row.get(
                "direction_correct"
            )
            is False
        ):
            icon = "❌"

        else:
            icon = "⏳"

        with st.expander(
            f"{icon} "
            f"{row['ticker']} — "
            f"{row['trade_date']} — "
            f"{row.get('result_status', 'OPEN')}"
        ):
            st.write(
                f"Start price: "
                f"**${float(row['start_price']):.2f}**"
            )

            st.write(
                f"Original signal: "
                f"**{row['action']}**"
            )

            st.write(
                f"Day / Swing / Quality: "
                f"**{row['day_score']} / "
                f"{row['swing_score']} / "
                f"{row['quality_score']}**"
            )

            # ORIGINAL
            st.subheader(
                "Original Saved Forecast"
            )

            original_close = (
                row.get(
                    "eod_predicted_close"
                )
            )

            original_confidence = (
                row.get(
                    "eod_confidence"
                )
            )

            if (
                original_close
                is not None
            ):
                st.write(
                    f"Predicted close: "
                    f"**${float(original_close):.2f}**"
                )

            if (
                row.get(
                    "eod_predicted_move"
                )
                is not None
            ):
                st.write(
                    f"Predicted move: "
                    f"**{float(row['eod_predicted_move']):+.2%}**"
                )

            if (
                original_confidence
                is not None
            ):
                st.write(
                    f"Confidence: "
                    f"**{int(original_confidence)}% "
                    f"({confidence_label(int(original_confidence))})**"
                )

            # LATEST
            st.subheader(
                "Latest Forecast"
            )

            latest_close = (
                row.get(
                    "latest_eod_predicted_close"
                )
            )

            latest_confidence = (
                row.get(
                    "latest_eod_confidence"
                )
            )

            if (
                latest_close
                is not None
            ):
                st.write(
                    f"Latest predicted close: "
                    f"**${float(latest_close):.2f}**"
                )

            if (
                row.get(
                    "latest_eod_predicted_move"
                )
                is not None
            ):
                st.write(
                    f"Latest predicted move: "
                    f"**{float(row['latest_eod_predicted_move']):+.2%}**"
                )

            if (
                latest_confidence
                is not None
            ):
                st.write(
                    f"Latest confidence: "
                    f"**{int(latest_confidence)}% "
                    f"({confidence_label(int(latest_confidence))})**"
                )

            if (
                original_close is not None
                and latest_close is not None
            ):
                forecast_change = (
                    float(
                        latest_close
                    )
                    - float(
                        original_close
                    )
                )

                st.markdown(
                    "Change in model forecast: "
                    + colored_change(
                        forecast_change
                    ),
                    unsafe_allow_html=True,
                )

            if (
                original_confidence
                is not None
                and latest_confidence
                is not None
            ):
                confidence_change = (
                    int(
                        latest_confidence
                    )
                    - int(
                        original_confidence
                    )
                )

                st.markdown(
                    "Confidence change: "
                    + colored_change(
                        confidence_change,
                        " pts",
                    ),
                    unsafe_allow_html=True,
                )

            # SNAPSHOT HISTORY
            prediction_id = (
                row.get(
                    "id"
                )
            )

            if prediction_id is not None:
                snapshots = fetch_snapshots(
                    prediction_id
                )

                if snapshots:
                    with st.expander(
                        f"Forecast history "
                        f"({len(snapshots)} snapshots)"
                    ):
                        snapshot_df = pd.DataFrame(
                            snapshots
                        )

                        columns = [
                            "snapshot_at",
                            "current_price",
                            "predicted_close",
                            "confidence",
                            "predicted_move",
                            "day_score",
                            "swing_score",
                            "quality_score",
                            "rsi",
                            "relative_volume",
                        ]

                        available = [
                            column
                            for column
                            in columns
                            if (
                                column
                                in snapshot_df.columns
                            )
                        ]

                        snapshot_df = (
                            snapshot_df[
                                available
                            ]
                        )

                        if (
                            "predicted_move"
                            in snapshot_df.columns
                        ):
                            snapshot_df[
                                "predicted_move"
                            ] = (
                                snapshot_df[
                                    "predicted_move"
                                ]
                                * 100
                            )

                        st.dataframe(
                            snapshot_df,
                            use_container_width=True,
                            hide_index=True,
                        )

            st.divider()

            st.write(
                f"Buy zone: "
                f"**${float(row['entry_low']):.2f} – "
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

            # CLOSED RESULT
            if (
                row.get(
                    "result_status"
                )
                == "CLOSED"
            ):
                actual_close = float(
                    row[
                        "close_price"
                    ]
                )

                st.divider()

                st.subheader(
                    "Actual Result"
                )

                st.write(
                    f"Actual close: "
                    f"**${actual_close:.2f}**"
                )

                if (
                    row.get(
                        "eod_error_abs"
                    )
                    is not None
                ):
                    st.write(
                        f"Original forecast missed by: "
                        f"**${float(row['eod_error_abs']):.2f}**"
                    )

                if (
                    row.get(
                        "eod_error_pct"
                    )
                    is not None
                ):
                    st.write(
                        f"Original forecast error: "
                        f"**{float(row['eod_error_pct']):.2%}**"
                    )

                if (
                    row.get(
                        "direction_correct"
                    )
                    is True
                ):
                    st.success(
                        "Direction prediction: CORRECT"
                    )

                elif (
                    row.get(
                        "direction_correct"
                    )
                    is False
                ):
                    st.error(
                        "Direction prediction: WRONG"
                    )

                if (
                    row.get(
                        "eod_range_hit"
                    )
                    is True
                ):
                    st.success(
                        "Actual close landed inside the predicted range."
                    )

                elif (
                    row.get(
                        "eod_range_hit"
                    )
                    is False
                ):
                    st.error(
                        "Actual close finished outside the predicted range."
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

            if st.button(
                f"🗑 Remove "
                f"{row['ticker']}",
                key=(
                    f"remove_"
                    f"{row['id']}_"
                    f"{index}"
                ),
                use_container_width=True,
            ):
                if remove_prediction(
                    row[
                        "id"
                    ]
                ):
                    st.success(
                        f"{row['ticker']} removed."
                    )

                    st.rerun()

    if closed:
        tracker_df = pd.DataFrame(
            closed
        )

        st.download_button(
            "Download Results CSV",
            tracker_df.to_csv(
                index=False
            ),
            "prediction_results.csv",
            "text/csv",
            use_container_width=True,
        )


# ============================================================
# GUIDE
# ============================================================

st.divider()

st.subheader(
    "How to Read This App"
)


with st.expander(
    "Best Today vs Best 2–5 Day"
):
    st.markdown(
        """
**Best Today**

Designed to find stocks with the most attractive setup for the current trading session.

It gives more weight to:

- Day Score
- VWAP
- Relative volume
- Remaining EOD upside
- Current entry location
- RSI
- Risk/reward
- Model confidence

**Best 2–5 Day**

Designed for swing setups.

It gives more weight to:

- Swing Score
- Trend quality
- Risk/reward
- Momentum persistence
- Quality Score

A stock can rank highly for 2–5 days while not being a good entry today.
"""
    )


with st.expander(
    "Model Confidence — what does the % mean?"
):
    st.markdown(
        """
Model Confidence is a **strength score**, not a guaranteed probability.

A displayed **72% confidence does not mean there is exactly a 72% chance**
the stock will close at the predicted price.

Current guide:

- **50–59% — Low**
- **60–69% — Moderate**
- **70–79% — High**
- **80–85% — Very High**

The model intentionally caps confidence at 85%.

Once enough real predictions are collected, we can calibrate these confidence
scores against actual historical results.
"""
    )


with st.expander(
    "Day Score"
):
    st.markdown(
        """
Measures the short-term / same-day setup.

- **75–100:** strong
- **65–74:** favourable
- **45–64:** mixed
- **Below 45:** weak
"""
    )


with st.expander(
    "Swing Score"
):
    st.markdown(
        """
Measures the multi-day momentum and trend setup.

This is especially relevant to the **2–5 Day ranking**, Target 1 and Target 2.
"""
    )


with st.expander(
    "Quality Score"
):
    st.markdown(
        """
Measures how well the setup is confirmed by factors such as:

- Trend
- RSI
- Relative volume
- VWAP

A high Day Score with poor Quality should be treated more cautiously.
"""
    )


with st.expander(
    "RSI"
):
    st.markdown(
        """
- **Below 30:** oversold
- **30–49:** weak / recovering
- **50–68:** healthy momentum
- **69–74:** strong but extended
- **75+:** increasingly overbought / chase risk
"""
    )


with st.expander(
    "VWAP"
):
    st.markdown(
        """
VWAP is the volume-weighted average price for the session.

- **Above VWAP:** generally supportive intraday
- **Below VWAP:** generally weaker intraday

VWAP becomes more useful after trading has been underway for a while.
"""
    )


with st.expander(
    "Relative Volume"
):
    st.markdown(
        """
- **Below 0.8×:** weak confirmation
- **Around 1.0×:** normal
- **1.2×+:** stronger confirmation
- **1.5×+:** strong volume confirmation
"""
    )


with st.expander(
    "Buy Zone / Entry Status"
):
    st.markdown(
        """
The Buy Zone is the preferred entry area based on volatility and risk/reward.

Possible statuses include:

- **BELOW BUY ZONE**
- **INSIDE BUY ZONE**
- **ABOVE BUY ZONE — DON'T CHASE**
- **NEAR STOP — HIGH RISK**

A bullish stock is not automatically a good buy at every price.
"""
    )


with st.expander(
    "EOD Forecast vs Targets"
):
    st.markdown(
        """
**EOD Predicted Close**

The model's estimate for the current trading session's close.

**Target 1**

A broader 2–5 day swing objective.

**Target 2**

A more aggressive extended swing objective.

Target 1 and Target 2 should not be interpreted as today's expected closing price.
"""
    )


with st.expander(
    "Original vs Latest Forecast"
):
    st.markdown(
        """
The **Original Saved Forecast** is frozen when you track the stock.

It is used for official accuracy.

The **Latest Forecast** changes when you press Refresh Latest Forecasts.

Green change means the model's forecast increased.

Red change means the model's forecast decreased.
"""
    )


st.divider()

st.caption(
    f"Page refreshed: "
    f"{now_et().strftime('%I:%M:%S %p ET')} "
    f"• Session: {SESSION_LABEL}"
)
