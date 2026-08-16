import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from datetime import datetime, time
from zoneinfo import ZoneInfo


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Live Market Trader",
    page_icon="📈",
    layout="centered"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 4rem;
        max-width: 950px;
    }

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        padding: 10px;
        border-radius: 12px;
    }

    .tradebox {
        padding: 14px;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        margin-top: 8px;
        margin-bottom: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Live Market Trader")

st.caption(
    "Stocks + ETFs • Pre-market • Intraday • 2–5 day swing analysis"
)

st.warning(
    "BUY / SELL levels are model-generated research levels, not guarantees or personalized investment advice."
)


# ============================================================
# TIME
# ============================================================

ET = ZoneInfo("America/Toronto")


def now_et():
    return datetime.now(ET)


def session_mode():

    now = now_et()

    if now.weekday() >= 5:
        return "WEEKEND", "Market closed"

    t = now.time()

    if t < time(9, 30):
        return "PREMARKET", "Premarket"

    if t <= time(16, 0):
        return "REGULAR", "Live"

    return "AFTERHOURS", "After-hours"


SESSION, SESSION_LABEL = session_mode()


# ============================================================
# CANADIAN ETFs
# ============================================================

CANADIAN_ETFS = {
    "XEQT": "iShares Core Equity ETF Portfolio",
    "XGRO": "iShares Core Growth ETF Portfolio",
    "XBAL": "iShares Core Balanced ETF Portfolio",
    "XCNS": "iShares Core Conservative ETF Portfolio",

    "VEQT": "Vanguard All-Equity ETF Portfolio",
    "VGRO": "Vanguard Growth ETF Portfolio",
    "VBAL": "Vanguard Balanced ETF Portfolio",
    "VCNS": "Vanguard Conservative ETF Portfolio",

    "XIU": "iShares S&P/TSX 60 Index ETF",
    "XIC": "iShares Core S&P/TSX Capped Composite ETF",
    "VCN": "Vanguard FTSE Canada All Cap Index ETF",

    "VFV": "Vanguard S&P 500 Index ETF",
    "XUS": "iShares Core S&P 500 Index ETF",
    "ZSP": "BMO S&P 500 Index ETF",

    "XQQ": "iShares NASDAQ 100 Index ETF",
    "ZNQ": "BMO NASDAQ 100 Equity Index ETF",

    "XEG": "iShares S&P/TSX Capped Energy Index ETF",
    "XFN": "iShares S&P/TSX Capped Financials Index ETF",
    "XIT": "iShares S&P/TSX Capped Information Technology ETF",
    "XMA": "iShares S&P/TSX Capped Materials Index ETF",
    "XUT": "iShares S&P/TSX Capped Utilities Index ETF",

    "ZAG": "BMO Aggregate Bond Index ETF",
    "XBB": "iShares Core Canadian Universe Bond Index ETF",
    "VAB": "Vanguard Canadian Aggregate Bond Index ETF"
}


# ============================================================
# STOCK UNIVERSES
# ============================================================

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
    "L.TO": "Loblaw"
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
    "PLTR": "Palantir"
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
    "ARM": "Arm Holdings"
}


ALL_NAMES = {}

ALL_NAMES.update(TSX)
ALL_NAMES.update(SP500)
ALL_NAMES.update(NASDAQ)

for ticker, name in CANADIAN_ETFS.items():
    ALL_NAMES[f"{ticker}.TO"] = name


# ============================================================
# TICKER NORMALIZATION
# ============================================================

def normalize_ticker(raw):

    ticker = raw.strip().upper()

    if not ticker:
        return ""

    if ticker.endswith(".TO"):
        return ticker

    # Known Canadian ETF
    if ticker in CANADIAN_ETFS:
        return ticker + ".TO"

    # Known TSX stock entered without .TO
    possible_tsx = ticker + ".TO"

    if possible_tsx in TSX:
        return possible_tsx

    # U.S. tickers remain unchanged
    return ticker


def is_canadian_etf(ticker):

    base = ticker.replace(
        ".TO",
        ""
    )

    return base in CANADIAN_ETFS


# ============================================================
# SECTOR MAP
# ============================================================

SECTOR = {}

for t in [
    "RY.TO", "TD.TO", "BMO.TO", "BNS.TO",
    "CM.TO", "NA.TO", "MFC.TO", "SLF.TO"
]:
    SECTOR[t] = "XFN.TO"

for t in [
    "CNQ.TO", "SU.TO", "CVE.TO",
    "IMO.TO", "TRP.TO", "ENB.TO"
]:
    SECTOR[t] = "XEG.TO"

for t in [
    "SHOP.TO", "CSU.TO", "OTEX.TO"
]:
    SECTOR[t] = "XIT.TO"

for t in [
    "ABX.TO", "AEM.TO", "WPM.TO",
    "NTR.TO", "TECK-B.TO"
]:
    SECTOR[t] = "XMA.TO"

for t in [
    "AAPL", "MSFT", "CRM", "ORCL"
]:
    SECTOR[t] = "XLK"

for t in [
    "NVDA", "AMD", "AVGO", "QCOM",
    "INTC", "AMAT", "MU", "LRCX",
    "KLAC", "MRVL", "ARM"
]:
    SECTOR[t] = "SMH"

for t in [
    "AMZN", "TSLA", "HD"
]:
    SECTOR[t] = "XLY"

for t in [
    "META", "GOOGL", "NFLX", "DIS"
]:
    SECTOR[t] = "XLC"

for t in [
    "JPM", "BAC", "GS", "V", "MA"
]:
    SECTOR[t] = "XLF"

for t in [
    "XOM", "CVX"
]:
    SECTOR[t] = "XLE"


# ============================================================
# DATA
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
            threads=False
        )

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

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
            threads=False
        )

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

        return df.dropna()

    except Exception:

        return pd.DataFrame()


def get_series(
    df,
    column
):

    if df is None or df.empty:

        return pd.Series(
            dtype=float
        )

    if column not in df.columns:

        return pd.Series(
            dtype=float
        )

    value = df[
        column
    ]

    if isinstance(
        value,
        pd.DataFrame
    ):

        value = value.iloc[
            :,
            0
        ]

    return pd.to_numeric(
        value,
        errors="coerce"
    )


def clamp(
    value,
    low,
    high
):

    return max(
        low,
        min(
            high,
            value
        )
    )


# ============================================================
# PRICE SOURCE
# ============================================================

def current_price_info(
    ticker
):

    intra = intraday_data(
        ticker
    )

    daily = daily_data(
        ticker,
        "1mo"
    )

    daily_close = get_series(
        daily,
        "Close"
    ).dropna()


    previous_close = None

    if not daily_close.empty:

        previous_close = float(
            daily_close.iloc[-1]
        )


    if not intra.empty:

        intra_close = get_series(
            intra,
            "Close"
        ).dropna()

        if not intra_close.empty:

            price = float(
                intra_close.iloc[-1]
            )


            if SESSION == "PREMARKET":

                label = "Premarket"


            elif SESSION == "REGULAR":

                label = "Live / latest available"


            elif SESSION == "AFTERHOURS":

                label = "After-hours"


            else:

                label = "Latest available"


            return {
                "price":
                    price,

                "label":
                    label,

                "previous_close":
                    previous_close,

                "intraday":
                    intra
            }


    return {
        "price":
            previous_close,

        "label":
            "Previous Close",

        "previous_close":
            previous_close,

        "intraday":
            pd.DataFrame()
    }


# ============================================================
# INDICATORS
# ============================================================

def calculate_rsi(
    close,
    period=14
):

    delta = close.diff()

    gains = (
        delta.clip(
            lower=0
        )
        .rolling(
            period
        )
        .mean()
    )

    losses = (
        -delta.clip(
            upper=0
        )
        .rolling(
            period
        )
        .mean()
    )

    rs = (
        gains /
        losses.replace(
            0,
            np.nan
        )
    )

    return 100 - (
        100 /
        (
            1 +
            rs
        )
    )


def calculate_atr(
    data,
    period=14
):

    high = get_series(
        data,
        "High"
    )

    low = get_series(
        data,
        "Low"
    )

    close = get_series(
        data,
        "Close"
    )

    prev_close = (
        close.shift(1)
    )


    true_range = pd.concat(
        [
            high - low,

            (
                high -
                prev_close
            ).abs(),

            (
                low -
                prev_close
            ).abs()
        ],
        axis=1
    ).max(
        axis=1
    )


    return (
        true_range
        .rolling(
            period
        )
        .mean()
    )


def rsi_label(
    value
):

    if pd.isna(value):

        return "Unknown"

    if value < 30:

        return "Oversold"

    if value < 45:

        return "Weak"

    if value < 55:

        return "Neutral"

    if value < 65:

        return "Healthy momentum"

    if value < 70:

        return "Strong momentum"

    if value < 80:

        return "Extended"

    return "Very extended"


# ============================================================
# VWAP
# ============================================================

def calculate_vwap(
    ticker
):

    data = intraday_data(
        ticker
    )

    if data.empty:

        return None


    high = get_series(
        data,
        "High"
    )

    low = get_series(
        data,
        "Low"
    )

    close = get_series(
        data,
        "Close"
    )

    volume = get_series(
        data,
        "Volume"
    )


    if close.empty:

        return None


    typical = (
        high +
        low +
        close
    ) / 3


    cumulative_volume = (
        volume.cumsum()
    )


    if (
        cumulative_volume.empty
        or
        cumulative_volume.iloc[-1]
        <= 0
    ):

        return None


    vwap = (
        (
            typical *
            volume
        ).cumsum()
        /
        cumulative_volume
    )


    return float(
        vwap.iloc[-1]
    )


# ============================================================
# MARKET INDEX
# ============================================================

def market_index(
    ticker
):

    if ticker.endswith(
        ".TO"
    ):

        return "^GSPTSE"

    if ticker in NASDAQ:

        return "^IXIC"

    return "^GSPC"


# ============================================================
# SIMPLE MARKET MOVE
# ============================================================

def latest_move(
    ticker
):

    data = daily_data(
        ticker,
        "1mo"
    )

    close = get_series(
        data,
        "Close"
    ).dropna()


    if len(close) < 2:

        return 0


    return (
        close.iloc[-1]
        /
        close.iloc[-2]
        -
        1
    )


# ============================================================
# ANALYSIS
# ============================================================

def analyze_stock(
    raw_ticker
):

    ticker = normalize_ticker(
        raw_ticker
    )


    daily = daily_data(
        ticker
    )


    if daily.empty:

        return None


    close = get_series(
        daily,
        "Close"
    )

    volume = get_series(
        daily,
        "Volume"
    )


    if len(close) < 70:

        return None


    price_info = (
        current_price_info(
            ticker
        )
    )


    current = (
        price_info[
            "price"
        ]
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


    avg_volume = (
        volume
        .rolling(20)
        .mean()
        .iloc[-1]
    )


    if (
        avg_volume > 0
        and
        not pd.isna(
            avg_volume
        )
    ):

        rel_volume = (
            volume.iloc[-1]
            /
            avg_volume
        )

    else:

        rel_volume = 1


    market_move = latest_move(
        market_index(
            ticker
        )
    )


    default_sector = (
        "XIU.TO"
        if ticker.endswith(
            ".TO"
        )
        else
        "SPY"
    )


    sector_symbol = (
        SECTOR.get(
            ticker,
            default_sector
        )
    )


    sector_move = (
        latest_move(
            sector_symbol
        )
    )


    # ========================================================
    # DAY SCORE
    # ========================================================

    day = 50


    day += (
        11 *
        np.tanh(
            ret1 /
            0.015
        )
    )


    day += (
        8 *
        np.tanh(
            ret3 /
            0.025
        )
    )


    day += (
        7 *
        np.tanh(
            market_move /
            0.012
        )
    )


    day += (
        8 *
        np.tanh(
            sector_move /
            0.015
        )
    )


    day += (
        8 *
        np.tanh(
            (
                ma5 /
                ma20 -
                1
            )
            /
            0.025
        )
    )


    if rel_volume >= 1.5:

        day += 5


    elif rel_volume >= 1.2:

        day += 3


    if (
        55 <=
        rsi_value <=
        68
    ):

        day += 4


    if rsi_value >= 80:

        day -= 8


    elif rsi_value >= 73:

        day -= 4


    # ETFs are generally less volatile.
    if is_canadian_etf(
        ticker
    ):

        day = (
            50 +
            (
                day -
                50
            )
            *
            0.80
        )


    day_score = int(
        clamp(
            round(
                day
            ),
            0,
            100
        )
    )


    # ========================================================
    # SWING SCORE
    # ========================================================

    swing = 50


    swing += (
        8 *
        np.tanh(
            ret3 /
            0.025
        )
    )


    swing += (
        11 *
        np.tanh(
            ret5 /
            0.04
        )
    )


    swing += (
        10 *
        np.tanh(
            ret20 /
            0.09
        )
    )


    swing += (
        8 *
        np.tanh(
            (
                ma5 /
                ma20 -
                1
            )
            /
            0.03
        )
    )


    swing += (
        8 *
        np.tanh(
            (
                ma20 /
                ma50 -
                1
            )
            /
            0.05
        )
    )


    swing += (
        6 *
        np.tanh(
            sector_move /
            0.015
        )
    )


    if (
        50 <=
        rsi_value <=
        68
    ):

        swing += 4


    if rsi_value >= 80:

        swing -= 8


    if is_canadian_etf(
        ticker
    ):

        swing = (
            50 +
            (
                swing -
                50
            )
            *
            0.85
        )


    swing_score = int(
        clamp(
            round(
                swing
            ),
            0,
            100
        )
    )


    # ========================================================
    # QUALITY SCORE
    # ========================================================

    quality = 50


    if (
        50 <=
        rsi_value <=
        68
    ):

        quality += 12


    elif rsi_value >= 80:

        quality -= 18


    if rel_volume >= 1.5:

        quality += 8


    elif rel_volume >= 1.2:

        quality += 4


    if ma5 > ma20 > ma50:

        quality += 10


    vwap = calculate_vwap(
        ticker
    )


    if (
        vwap is not None
        and
        SESSION ==
        "REGULAR"
    ):

        if current >= vwap:

            quality += 10

        else:

            quality -= 10


    quality_score = int(
        clamp(
            round(
                quality
            ),
            0,
            100
        )
    )


    # ========================================================
    # ATR / TRADE PLAN
    # ========================================================

    atr_values = (
        calculate_atr(
            daily
        )
    )


    if (
        atr_values.empty
        or
        pd.isna(
            atr_values.iloc[-1]
        )
    ):

        atr = (
            current *
            0.02
        )

    else:

        atr = float(
            atr_values.iloc[-1]
        )


    high = get_series(
        daily,
        "High"
    )

    low = get_series(
        daily,
        "Low"
    )


    recent_support = float(
        low.tail(10).min()
    )


    recent_resistance = float(
        high.tail(10).max()
    )


    support = max(
        recent_support,
        current -
        1.5 *
        atr
    )


    # ETF entries are tighter
    if is_canadian_etf(
        ticker
    ):

        entry_low = (
            current -
            0.30 *
            atr
        )

        entry_high = (
            current +
            0.08 *
            atr
        )

        stop = min(
            support -
            0.15 *
            atr,
            entry_low -
            0.75 *
            atr
        )

    else:

        entry_low = (
            current -
            0.45 *
            atr
        )

        entry_high = (
            current +
            0.10 *
            atr
        )

        stop = min(
            support -
            0.20 *
            atr,
            entry_low -
            0.85 *
            atr
        )


    entry_mid = (
        entry_low +
        entry_high
    ) / 2


    risk = max(
        entry_mid -
        stop,
        0.01
    )


    target1 = max(
        recent_resistance,
        entry_mid +
        1.5 *
        risk
    )


    target2 = max(
        recent_resistance +
        atr,
        entry_mid +
        2.2 *
        risk
    )


    rr1 = (
        target1 -
        entry_mid
    ) / risk


    rr2 = (
        target2 -
        entry_mid
    ) / risk


    # ========================================================
    # ENTRY STATUS
    # ========================================================

    if rsi_value >= 80:

        action = (
            "DON'T CHASE"
        )

        reason = (
            "The price is very extended. "
            "Wait for a pullback."
        )


    elif (
        rsi_value >= 70
        and
        not is_canadian_etf(
            ticker
        )
    ):

        action = (
            "WAIT FOR PULLBACK"
        )

        reason = (
            "Momentum is strong, but the stock is getting stretched."
        )


    elif rr1 < 1.5:

        action = (
            "WAIT — POOR RISK/REWARD"
        )

        reason = (
            "The first profit target does not offer enough reward relative to the stop."
        )


    elif (
        day_score >= 75
        and
        quality_score >= 70
    ):

        action = (
            "BUY SETUP / ENTRY FAVOURABLE"
        )

        reason = (
            "Short-term momentum, trend and trade quality are aligned."
        )


    elif (
        day_score >= 65
        or
        swing_score >= 70
    ):

        action = (
            "WATCH FOR ENTRY"
        )

        reason = (
            "The setup is promising, but stronger confirmation or a better price would improve the trade."
        )


    elif (
        day_score <= 40
        and
        swing_score <= 45
    ):

        action = (
            "AVOID / SELL REVIEW"
        )

        reason = (
            "Momentum and trend are currently weak."
        )


    else:

        action = (
            "NO CLEAR ENTRY"
        )

        reason = (
            "There is not enough evidence for a strong trade setup."
        )


    return {
        "ticker":
            ticker,

        "name":
            ALL_NAMES.get(
                ticker,
                ticker
            ),

        "is_etf":
            is_canadian_etf(
                ticker
            ),

        "current":
            current,

        "price_label":
            price_info[
                "label"
            ],

        "day":
            day_score,

        "swing":
            swing_score,

        "quality":
            quality_score,

        "rsi":
            rsi_value,

        "rsi_label":
            rsi_label(
                rsi_value
            ),

        "relative_volume":
            rel_volume,

        "vwap":
            vwap,

        "action":
            action,

        "reason":
            reason,

        "entry_low":
            entry_low,

        "entry_high":
            entry_high,

        "stop":
            stop,

        "target1":
            target1,

        "target2":
            target2,

        "rr1":
            rr1,

        "rr2":
            rr2,

        "atr":
            atr,

        "rank":
            (
                day_score *
                0.45
                +
                swing_score *
                0.25
                +
                quality_score *
                0.30
            )
    }


# ============================================================
# TRADE BOX
# ============================================================

def show_trade_plan(
    result
):

    st.subheader(
        result[
            "action"
        ]
    )


    st.write(
        result[
            "reason"
        ]
    )


    st.markdown(
        "---"
    )


    st.metric(
        "CURRENT PRICE",
        f"${result['current']:.2f}"
    )


    st.caption(
        f"Price source: {result['price_label']}"
    )


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

**Risk / Reward to Target 1:** 1 : {result['rr1']:.1f}  
**Risk / Reward to Target 2:** 1 : {result['rr2']:.1f}
"""
    )


    if result[
        "vwap"
    ] is not None:

        st.write(
            f"VWAP: "
            f"**${result['vwap']:.2f}**"
        )


    st.write(
        f"RSI: "
        f"**{result['rsi']:.0f} — "
        f"{result['rsi_label']}**"
    )


    st.write(
        f"Relative volume: "
        f"**{result['relative_volume']:.1f}× normal**"
    )


    st.write(
        f"ATR: "
        f"**${result['atr']:.2f}**"
    )


# ============================================================
# SAVED HOLDINGS / WATCHLIST
# ============================================================

try:

    saved_holdings = (
        st.query_params.get(
            "holdings",
            "TRP.TO"
        )
    )

    saved_watchlist = (
        st.query_params.get(
            "watchlist",
            ""
        )
    )

except Exception:

    saved_holdings = (
        "TRP.TO"
    )

    saved_watchlist = (
        ""
    )


st.subheader(
    "My Holdings"
)


holdings_text = (
    st.text_input(
        "Stocks / ETFs you own",
        value=
            saved_holdings,
        help=
            "Example: TRP, XEQT, VBAL, NVDA"
    )
)


st.subheader(
    "⭐ My Watchlist"
)


watchlist_text = (
    st.text_input(
        "Stocks / ETFs you want to watch",
        value=
            saved_watchlist,
        help=
            "Example: CVE, CNQ, XEQT, NVDA"
    )
)


holdings = [
    normalize_ticker(
        ticker
    )

    for ticker
    in holdings_text.split(
        ","
    )

    if ticker.strip()
]


watchlist = [
    normalize_ticker(
        ticker
    )

    for ticker
    in watchlist_text.split(
        ","
    )

    if ticker.strip()
]


if st.button(
    "💾 Save My Stocks",
    use_container_width=True
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

scan_tab, personal_tab, analyze_tab = (
    st.tabs(
        [
            "Market Scanner",
            "⭐ My Stocks",
            "Analyze Stock / ETF"
        ]
    )
)


# ============================================================
# SCANNER
# ============================================================

with scan_tab:

    market_choice = (
        st.selectbox(
            "Market",
            [
                "TSX",
                "S&P 500",
                "Nasdaq-100",
                "Canadian ETFs",
                "All Markets"
            ]
        )
    )


    scan_size = (
        st.selectbox(
            "Number to scan",
            [
                10,
                20,
                30,
                50
            ],
            index=1
        )
    )


    if st.button(
        "🔎 Scan Now",
        type="primary",
        use_container_width=True
    ):


        if market_choice == "TSX":

            universe = list(
                TSX.keys()
            )


        elif market_choice == "S&P 500":

            universe = list(
                SP500.keys()
            )


        elif market_choice == "Nasdaq-100":

            universe = list(
                NASDAQ.keys()
            )


        elif market_choice == "Canadian ETFs":

            universe = [
                ticker +
                ".TO"

                for ticker
                in CANADIAN_ETFS.keys()
            ]


        else:

            universe = list(
                dict.fromkeys(
                    list(
                        TSX.keys()
                    )
                    +
                    list(
                        SP500.keys()
                    )
                    +
                    list(
                        NASDAQ.keys()
                    )
                    +
                    [
                        ticker +
                        ".TO"

                        for ticker
                        in CANADIAN_ETFS.keys()
                    ]
                )
            )


        universe = universe[
            :scan_size
        ]


        for ticker in (
            holdings +
            watchlist
        ):

            if ticker not in universe:

                universe.insert(
                    0,
                    ticker
                )


        results = []


        progress = (
            st.progress(
                0
            )
        )


        status = (
            st.empty()
        )


        for i, ticker in enumerate(
            universe
        ):

            status.write(
                f"Analyzing {ticker}..."
            )


            result = (
                analyze_stock(
                    ticker
                )
            )


            if result:

                results.append(
                    result
                )


            progress.progress(
                (
                    i +
                    1
                )
                /
                len(
                    universe
                )
            )


        progress.empty()

        status.empty()


        if not results:

            st.error(
                "No usable results were returned."
            )


        else:

            results = sorted(
                results,
                key=lambda x:
                    x[
                        "rank"
                    ],
                reverse=True
            )


            best = (
                results[
                    0
                ]
            )


            st.subheader(
                "🏆 Best Current Setup"
            )


            st.header(
                best[
                    "ticker"
                ]
            )


            st.write(
                best[
                    "name"
                ]
            )


            c1, c2, c3 = (
                st.columns(
                    3
                )
            )


            c1.metric(
                "Day",
                f"{best['day']}/100"
            )


            c2.metric(
                "Swing",
                f"{best['swing']}/100"
            )


            c3.metric(
                "Quality",
                f"{best['quality']}/100"
            )


            show_trade_plan(
                best
            )


            st.divider()


            st.subheader(
                "Top Opportunities"
            )


            for result in results[
                :10
            ]:


                title = (
                    f"{result['ticker']} — "
                    f"{result['action']}"
                )


                with st.expander(
                    title
                ):


                    st.write(
                        f"**{result['name']}**"
                    )


                    st.write(
                        f"Current: "
                        f"**${result['current']:.2f}** "
                        f"({result['price_label']})"
                    )


                    st.write(
                        f"BUY: "
                        f"**${result['entry_low']:.2f}"
                        f"–${result['entry_high']:.2f}**"
                    )


                    st.write(
                        f"STOP / EXIT: "
                        f"**${result['stop']:.2f}**"
                    )


                    st.write(
                        f"SELL T1: "
                        f"**${result['target1']:.2f}**"
                    )


                    st.write(
                        f"SELL T2: "
                        f"**${result['target2']:.2f}**"
                    )


                    st.write(
                        f"Risk/Reward: "
                        f"**1:{result['rr1']:.1f}**"
                    )


                    st.write(
                        f"Day / Swing / Quality: "
                        f"**{result['day']} / "
                        f"{result['swing']} / "
                        f"{result['quality']}**"
                    )


# ============================================================
# MY STOCKS
# ============================================================

with personal_tab:

    personal = list(
        dict.fromkeys(
            holdings +
            watchlist
        )
    )


    if not personal:

        st.info(
            "Add stocks or ETFs to Holdings or Watchlist above."
        )


    elif st.button(
        "Refresh My Stocks",
        use_container_width=True
    ):


        for ticker in personal:

            result = (
                analyze_stock(
                    ticker
                )
            )


            if result is None:

                st.warning(
                    f"Could not analyze {ticker}."
                )

                continue


            st.header(
                ticker
            )


            st.write(
                result[
                    "name"
                ]
            )


            if ticker in holdings:

                st.caption(
                    "OWNED"
                )

            else:

                st.caption(
                    "WATCHLIST"
                )


            c1, c2, c3 = (
                st.columns(
                    3
                )
            )


            c1.metric(
                "Day",
                result[
                    "day"
                ]
            )


            c2.metric(
                "Swing",
                result[
                    "swing"
                ]
            )


            c3.metric(
                "Quality",
                result[
                    "quality"
                ]
            )


            show_trade_plan(
                result
            )


            st.divider()


# ============================================================
# ANALYZE ONE
# ============================================================

with analyze_tab:

    raw_ticker = (
        st.text_input(
            "Enter ticker",
            value=
                "XEQT",
            help=
                "You can type XEQT, VBAL, TRP, NVDA, AAPL, etc."
        )
    )


    normalized = (
        normalize_ticker(
            raw_ticker
        )
    )


    if normalized != raw_ticker.strip().upper():

        st.caption(
            f"Using ticker: **{normalized}**"
        )


    if st.button(
        "Analyze",
        use_container_width=True
    ):


        with st.spinner(
            f"Analyzing {normalized}..."
        ):


            result = (
                analyze_stock(
                    normalized
                )
            )


        if result is None:

            st.error(
                "No usable market data was found. "
                "Check the ticker and try again."
            )


        else:

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


            if result[
                "is_etf"
            ]:

                st.info(
                    "ETF mode: scoring is moderated because diversified ETFs "
                    "normally move less than individual stocks."
                )


            c1, c2, c3 = (
                st.columns(
                    3
                )
            )


            c1.metric(
                "Day",
                f"{result['day']}/100"
            )


            c2.metric(
                "Swing",
                f"{result['swing']}/100"
            )


            c3.metric(
                "Quality",
                f"{result['quality']}/100"
            )


            show_trade_plan(
                result
            )


# ============================================================
# HELP
# ============================================================

with st.expander(
    "How to read the price levels"
):

    st.markdown(
        """
### CURRENT PRICE

The latest price available to the app.

It will also say whether it is:

- Premarket
- Live / latest available
- After-hours
- Previous Close

### BUY ZONE

The model's preferred entry range.

You do **not** automatically buy just because the stock reaches this price.
The trend and trade status should still be favourable.

### STOP / EXIT

The approximate level where the bullish trade setup is considered broken.

### SELL TARGET 1

The first profit-taking area.

### SELL TARGET 2

A more aggressive target if momentum continues.

### Risk / Reward

**1 : 2** means approximately $2 of possible reward for each $1 risked to the stop.

The app generally prefers Target 1 risk/reward of at least **1 : 1.5**.

### Canadian ETFs

You can simply enter:

- XEQT
- XGRO
- VBAL
- VEQT
- VGRO
- VFV
- XQQ

The app automatically adds `.TO`.
"""
    )


st.divider()


st.caption(
    f"Page refreshed: "
    f"{now_et().strftime('%I:%M:%S %p ET')} • "
    f"Current session: {SESSION_LABEL}"
)
