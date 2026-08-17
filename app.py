from datetime import datetime, time
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
    layout="centered"
)

st.title("Live Market Trader")

st.caption(
    "Scanner • trade plan • holdings/watchlist • prediction scorecard"
)

st.warning(
    "Model scores and trade levels are research signals, "
    "not guaranteed outcomes or personalized investment advice."
)


# ============================================================
# TIME
# ============================================================

ET = ZoneInfo("America/Toronto")


def now_et():
    return datetime.now(ET)


def session_mode():

    n = now_et()

    if n.weekday() >= 5:
        return "WEEKEND", "Market closed"

    if n.time() < time(9, 30):
        return "PREMARKET", "Premarket"

    if n.time() <= time(16, 0):
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

    "VEQT": "Vanguard All-Equity ETF Portfolio",
    "VGRO": "Vanguard Growth ETF Portfolio",
    "VBAL": "Vanguard Balanced ETF Portfolio",

    "VFV": "Vanguard S&P 500 Index ETF",
    "XQQ": "iShares NASDAQ 100 Index ETF",
    "VCN": "Vanguard FTSE Canada All Cap Index ETF",
    "XIU": "iShares S&P/TSX 60 Index ETF",

    "ZAG": "BMO Aggregate Bond Index ETF",
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

    ALL_NAMES[
        ticker + ".TO"
    ] = name


# ============================================================
# TICKER NORMALIZATION
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

    return (
        ticker
        .replace(".TO", "")
        in CANADIAN_ETFS
    )


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
def daily_data(
    ticker,
    period="1y"
):

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
def intraday_data(
    ticker
):

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

    if (
        df is None
        or df.empty
        or column not in df.columns
    ):

        return pd.Series(
            dtype=float
        )

    value = df[column]

    if isinstance(
        value,
        pd.DataFrame
    ):

        value = value.iloc[:, 0]

    return pd.to_numeric(
        value,
        errors="coerce"
    )


# ============================================================
# INDICATORS
# ============================================================

def calculate_rsi(
    close,
    period=14
):

    delta = close.diff()

    gains = (
        delta
        .clip(lower=0)
        .rolling(period)
        .mean()
    )

    losses = (
        -delta
        .clip(upper=0)
        .rolling(period)
        .mean()
    )

    rs = (
        gains
        /
        losses.replace(
            0,
            np.nan
        )
    )

    return (
        100
        -
        100 /
        (1 + rs)
    )


def calculate_atr(
    df,
    period=14
):

    high = get_series(
        df,
        "High"
    )

    low = get_series(
        df,
        "Low"
    )

    close = get_series(
        df,
        "Close"
    )

    previous_close = (
        close.shift(1)
    )

    true_range = pd.concat(
        [
            high - low,

            (
                high -
                previous_close
            ).abs(),

            (
                low -
                previous_close
            ).abs()
        ],
        axis=1
    ).max(
        axis=1
    )

    return (
        true_range
        .rolling(period)
        .mean()
    )


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
        return 0.0

    return float(
        close.iloc[-1]
        /
        close.iloc[-2]
        -
        1
    )


# ============================================================
# CURRENT PRICE
# ============================================================

def price_info(
    ticker
):

    intraday = intraday_data(
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

    previous_close = (
        float(
            daily_close.iloc[-1]
        )
        if len(daily_close)
        else None
    )

    if not intraday.empty:

        intraday_close = get_series(
            intraday,
            "Close"
        ).dropna()

        if len(intraday_close):

            if SESSION == "PREMARKET":

                label = "Premarket"

            elif SESSION == "REGULAR":

                label = (
                    "Live / latest available"
                )

            elif SESSION == "AFTERHOURS":

                label = "After-hours"

            else:

                label = (
                    "Latest available"
                )

            return (
                float(
                    intraday_close.iloc[-1]
                ),
                label,
                previous_close
            )

    return (
        previous_close,
        "Previous Close",
        previous_close
    )


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

    cumulative_volume = (
        volume.cumsum()
    )

    if (
        len(close) == 0
        or
        len(cumulative_volume) == 0
        or
        cumulative_volume.iloc[-1]
        <= 0
    ):

        return None

    typical_price = (
        high +
        low +
        close
    ) / 3

    vwap = (
        (
            typical_price *
            volume
        )
        .cumsum()
        /
        cumulative_volume
    )

    return float(
        vwap.iloc[-1]
    )


# ============================================================
# STOCK ANALYSIS
# ============================================================

def analyze(
    raw_ticker
):

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
        "Close"
    )

    volume = get_series(
        data,
        "Volume"
    )

    high = get_series(
        data,
        "High"
    )

    low = get_series(
        data,
        "Low"
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


    # --------------------------------------------------------
    # RETURNS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # MOVING AVERAGES
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    rsi_value = (
        calculate_rsi(
            close
        )
        .iloc[-1]
    )


    # --------------------------------------------------------
    # RELATIVE VOLUME
    # --------------------------------------------------------

    average_volume = (
        volume
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    if (
        average_volume
        and
        not pd.isna(
            average_volume
        )
    ):

        relative_volume = (
            float(
                volume.iloc[-1]
                /
                average_volume
            )
        )

    else:

        relative_volume = 1.0


    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    market_move = latest_move(
        market_index(
            ticker
        )
    )


    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    sector_ticker = (
        "XIU.TO"
        if ticker.endswith(".TO")
        else "SPY"
    )

    sector_move = latest_move(
        sector_ticker
    )


    # ========================================================
    # DAY SCORE
    # ========================================================

    day_score = 50

    day_score += (
        11 *
        np.tanh(
            ret1 /
            0.015
        )
    )

    day_score += (
        8 *
        np.tanh(
            ret3 /
            0.025
        )
    )

    day_score += (
        7 *
        np.tanh(
            market_move /
            0.012
        )
    )

    day_score += (
        8 *
        np.tanh(
            sector_move /
            0.015
        )
    )

    day_score += (
        8 *
        np.tanh(
            (
                ma5 /
                ma20
                -
                1
            )
            /
            0.025
        )
    )

    if relative_volume >= 1.5:

        day_score += 5

    elif relative_volume >= 1.2:

        day_score += 3


    if (
        55 <=
        rsi_value <=
        68
    ):

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
            +
            (
                day_score -
                50
            )
            *
            0.80
        )


    day_score = int(
        max(
            0,
            min(
                100,
                round(
                    day_score
                )
            )
        )
    )


    # ========================================================
    # SWING SCORE
    # ========================================================

    swing_score = 50

    swing_score += (
        8 *
        np.tanh(
            ret3 /
            0.025
        )
    )

    swing_score += (
        11 *
        np.tanh(
            ret5 /
            0.04
        )
    )

    swing_score += (
        10 *
        np.tanh(
            ret20 /
            0.09
        )
    )

    swing_score += (
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

    swing_score += (
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

    swing_score += (
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

        swing_score += 4


    if rsi_value >= 80:

        swing_score -= 8


    if is_canadian_etf(
        ticker
    ):

        swing_score = (
            50
            +
            (
                swing_score -
                50
            )
            *
            0.85
        )


    swing_score = int(
        max(
            0,
            min(
                100,
                round(
                    swing_score
                )
            )
        )
    )


    # ========================================================
    # QUALITY SCORE
    # ========================================================

    quality_score = 50


    if (
        50 <=
        rsi_value <=
        68
    ):

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
        and
        SESSION == "REGULAR"
    ):

        if current >= vwap:

            quality_score += 10

        else:

            quality_score -= 10


    quality_score = int(
        max(
            0,
            min(
                100,
                round(
                    quality_score
                )
            )
        )
    )


    # ========================================================
    # ATR / BUY / SELL LEVELS
    # ========================================================

    atr_values = calculate_atr(
        data
    )


    if (
        len(atr_values)
        and
        not pd.isna(
            atr_values.iloc[-1]
        )
    ):

        atr_value = float(
            atr_values.iloc[-1]
        )

    else:

        atr_value = (
            current *
            0.02
        )


    support = max(
        float(
            low.tail(10).min()
        ),

        current
        -
        1.5 *
        atr_value
    )


    resistance = float(
        high.tail(10).max()
    )


    if is_canadian_etf(
        ticker
    ):

        entry_low = (
            current
            -
            0.30 *
            atr_value
        )

        entry_high = (
            current
            +
            0.08 *
            atr_value
        )

        stop = min(
            support
            -
            0.15 *
            atr_value,

            entry_low
            -
            0.75 *
            atr_value
        )

    else:

        entry_low = (
            current
            -
            0.45 *
            atr_value
        )

        entry_high = (
            current
            +
            0.10 *
            atr_value
        )

        stop = min(
            support
            -
            0.20 *
            atr_value,

            entry_low
            -
            0.85 *
            atr_value
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
        resistance,

        entry_mid
        +
        1.5 *
        risk
    )


    target2 = max(
        resistance
        +
        atr_value,

        entry_mid
        +
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
    # PREDICTION
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
        and
        not is_canadian_etf(
            ticker
        )
    ):

        action = (
            "WAIT FOR PULLBACK"
        )

        prediction = (
            "UP"
            if day_score >= 55
            else "NEUTRAL"
        )


    elif rr1 < 1.5:

        action = (
            "WAIT — POOR RISK/REWARD"
        )

        prediction = (
            "UP"
            if day_score >= 55
            else "NEUTRAL"
        )


    elif (
        day_score >= 75
        and
        quality_score >= 70
    ):

        action = (
            "BUY SETUP / ENTRY FAVOURABLE"
        )

        prediction = "UP"


    elif (
        day_score >= 65
        or
        swing_score >= 70
    ):

        action = (
            "WATCH FOR ENTRY"
        )

        prediction = "UP"


    elif (
        day_score <= 40
        and
        swing_score <= 45
    ):

        action = (
            "AVOID / SELL REVIEW"
        )

        prediction = "DOWN"


    else:

        action = (
            "NO CLEAR ENTRY"
        )

        prediction = "NEUTRAL"


    return {

        "ticker":
            ticker,

        "name":
            ALL_NAMES.get(
                ticker,
                ticker
            ),

        "current":
            float(
                current
            ),

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
            float(
                rsi_value
            ),

        "relative_volume":
            relative_volume,

        "vwap":
            vwap,

        "entry_low":
            float(
                entry_low
            ),

        "entry_high":
            float(
                entry_high
            ),

        "stop":
            float(
                stop
            ),

        "target1":
            float(
                target1
            ),

        "target2":
            float(
                target2
            ),

        "rr1":
            float(
                rr1
            ),

        "rr2":
            float(
                rr2
            ),

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
# SUPABASE / TEMPORARY STORAGE
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
            ]
        )

    except Exception:

        return None


DATABASE = get_database()

PERSISTENT_STORAGE = (
    DATABASE is not None
)


if (
    "predictions"
    not in st.session_state
):

    st.session_state[
        "predictions"
    ] = []


# ============================================================
# SAVE PREDICTION
# ============================================================

def save_prediction(
    result
):

    row = {

        "ticker":
            result[
                "ticker"
            ],

        "tracked_at":
            now_et()
            .isoformat(),

        "trade_date":
            now_et()
            .date()
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

        "result_status":
            "OPEN"
    }


    if PERSISTENT_STORAGE:

        DATABASE.table(
            "prediction_tracker"
        ).insert(
            row
        ).execute()

        return "persistent"


    temporary_ids = [

        item.get(
            "id",
            0
        )

        for item
        in st.session_state[
            "predictions"
        ]
    ]


    row["id"] = (
        max(
            temporary_ids
            or [0]
        )
        +
        1
    )


    st.session_state[
        "predictions"
    ].append(
        row
    )


    return "temporary"


# ============================================================
# FETCH PREDICTIONS
# ============================================================

def fetch_predictions():

    if PERSISTENT_STORAGE:

        try:

            response = (

                DATABASE

                .table(
                    "prediction_tracker"
                )

                .select(
                    "*"
                )

                .order(
                    "tracked_at",
                    desc=True
                )

                .execute()
            )

            return (
                response.data
                or []
            )

        except Exception:

            return []


    return list(
        st.session_state[
            "predictions"
        ]
    )


# ============================================================
# UPDATE PREDICTION
# ============================================================

def update_prediction(
    row_id,
    values
):

    if PERSISTENT_STORAGE:

        DATABASE.table(
            "prediction_tracker"
        ).update(
            values
        ).eq(
            "id",
            row_id
        ).execute()

        return


    for row in (
        st.session_state[
            "predictions"
        ]
    ):

        if (
            row.get(
                "id"
            )
            ==
            row_id
        ):

            row.update(
                values
            )


# ============================================================
# SETTLE / CHECK RESULT
# ============================================================

def settle_prediction(
    row
):

    if (
        row.get(
            "result_status"
        )
        ==
        "CLOSED"
    ):

        return row


    data = daily_data(
        row[
            "ticker"
        ],
        "1mo"
    )


    if data.empty:

        return row


    dates = (
        pd.to_datetime(
            data.index
        )
        .date
    )


    target_date = (
        pd.to_datetime(
            row[
                "trade_date"
            ]
        )
        .date()
    )


    mask = np.array(
        [
            d ==
            target_date

            for d
            in dates
        ]
    )


    if not mask.any():

        return row


    daily_row = (
        data.loc[
            mask
        ]
        .iloc[-1]
    )


    def value(
        column
    ):

        item = (
            daily_row[
                column
            ]
        )

        if isinstance(
            item,
            pd.Series
        ):

            item = (
                item.iloc[0]
            )

        return float(
            item
        )


    close_price = value(
        "Close"
    )

    day_high = value(
        "High"
    )

    day_low = value(
        "Low"
    )


    start_price = float(
        row[
            "start_price"
        ]
    )


    prediction = row[
        "prediction"
    ]


    if prediction == "UP":

        direction_correct = (
            close_price >
            start_price
        )


    elif prediction == "DOWN":

        direction_correct = (
            close_price <
            start_price
        )


    else:

        direction_correct = None


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
                <=
                float(
                    row[
                        "stop_price"
                    ]
                )
            ),

        "target1_hit":
            (
                day_high
                >=
                float(
                    row[
                        "target1"
                    ]
                )
            ),

        "target2_hit":
            (
                day_high
                >=
                float(
                    row[
                        "target2"
                    ]
                )
            ),

        "result_status":
            "CLOSED"
    }


    update_prediction(
        row[
            "id"
        ],
        values
    )


    row.update(
        values
    )


    return row


# ============================================================
# TRADE DISPLAY
# ============================================================

def show_trade(
    result,
    button_key
):

    st.subheader(
        result[
            "action"
        ]
    )


    st.metric(
        "CURRENT PRICE",
        f"${result['current']:.2f}"
    )


    st.caption(
        f"Price source: "
        f"{result['price_label']}"
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
"""
    )


    st.write(
        f"Day / Swing / Quality: "
        f"**{result['day']} / "
        f"{result['swing']} / "
        f"{result['quality']}**"
    )


    st.write(
        f"Risk / Reward T1: "
        f"**1:{result['rr1']:.1f}**"
    )


    if st.button(
        "📌 Track this prediction today",
        key=button_key,
        use_container_width=True
    ):

        storage_mode = (
            save_prediction(
                result
            )
        )


        if (
            storage_mode
            ==
            "persistent"
        ):

            st.success(
                "Prediction saved permanently."
            )

        else:

            st.success(
                "Prediction saved for this session. "
                "Connect Supabase for permanent history."
            )


# ============================================================
# HOLDINGS / WATCHLIST
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
            saved_holdings
    )
)


st.subheader(
    "⭐ My Watchlist"
)


watchlist_text = (
    st.text_input(
        "Stocks / ETFs you want to watch",
        value=
            saved_watchlist
    )
)


holdings = [

    normalize_ticker(
        item
    )

    for item
    in holdings_text.split(
        ","
    )

    if item.strip()
]


watchlist = [

    normalize_ticker(
        item
    )

    for item
    in watchlist_text.split(
        ","
    )

    if item.strip()
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

scan_tab, my_tab, analyze_tab, tracker_tab = (

    st.tabs(
        [
            "Market Scanner",
            "⭐ My Stocks",
            "Analyze",
            "📊 Prediction Tracker"
        ]
    )
)


# ============================================================
# MARKET SCANNER
# ============================================================

with scan_tab:

    market = st.selectbox(
        "Market",
        [
            "TSX",
            "S&P 500",
            "Nasdaq-100",
            "Canadian ETFs",
            "All Markets"
        ]
    )


    count = st.selectbox(
        "Number to scan",
        [
            10,
            20,
            30,
            50
        ],
        index=1
    )


    if st.button(
        "🔎 Scan Now",
        type="primary",
        use_container_width=True
    ):


        if market == "TSX":

            universe = list(
                TSX
            )


        elif market == "S&P 500":

            universe = list(
                SP500
            )


        elif market == "Nasdaq-100":

            universe = list(
                NASDAQ
            )


        elif market == "Canadian ETFs":

            universe = [

                item +
                ".TO"

                for item
                in CANADIAN_ETFS
            ]


        else:

            universe = list(
                dict.fromkeys(
                    list(TSX)
                    +
                    list(SP500)
                    +
                    list(NASDAQ)
                    +
                    [
                        item +
                        ".TO"

                        for item
                        in CANADIAN_ETFS
                    ]
                )
            )


        universe = universe[
            :count
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


        progress = st.progress(
            0
        )


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
                (
                    index +
                    1
                )
                /
                len(
                    universe
                )
            )


        progress.empty()

        status.empty()


        results = sorted(
            results,
            key=lambda item:
                item[
                    "rank"
                ],
            reverse=True
        )


        if not results:

            st.error(
                "No usable results."
            )


        else:

            st.subheader(
                "🏆 Best Current Setup"
            )


            st.header(
                results[0][
                    "ticker"
                ]
            )


            st.write(
                results[0][
                    "name"
                ]
            )


            show_trade(
                results[0],
                "track_best"
            )


            st.divider()


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

                    show_trade(
                        result,
                        f"scan_{index}_"
                        f"{result['ticker']}"
                    )


# ============================================================
# MY STOCKS
# ============================================================

with my_tab:

    personal = list(
        dict.fromkeys(
            holdings +
            watchlist
        )
    )


    if st.button(
        "Refresh My Stocks",
        use_container_width=True
    ):


        for index, ticker in enumerate(
            personal
        ):

            result = analyze(
                ticker
            )


            if result:

                st.header(
                    ticker
                )


                if ticker in holdings:

                    st.caption(
                        "OWNED"
                    )

                else:

                    st.caption(
                        "WATCHLIST"
                    )


                show_trade(
                    result,
                    f"my_{index}_"
                    f"{ticker}"
                )


                st.divider()


# ============================================================
# ANALYZE ONE
# ============================================================

with analyze_tab:

    raw_ticker = (
        st.text_input(
            "Enter ticker",
            value="XEQT"
        )
    )


    ticker = normalize_ticker(
        raw_ticker
    )


    if (
        ticker
        !=
        raw_ticker
        .strip()
        .upper()
    ):

        st.caption(
            f"Using ticker: "
            f"**{ticker}**"
        )


    if st.button(
        "Analyze",
        use_container_width=True
    ):

        result = analyze(
            ticker
        )


        if not result:

            st.error(
                "No usable market data was found."
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


            show_trade(
                result,
                f"single_"
                f"{result['ticker']}"
            )


# ============================================================
# PREDICTION TRACKER
# ============================================================

with tracker_tab:

    st.subheader(
        "Prediction Tracker"
    )


    # FIXED VERSION:
    # This prevents Streamlit from printing code/object text.

    if PERSISTENT_STORAGE:

        st.success(
            "Persistent storage connected."
        )

    else:

        st.warning(
            "Temporary storage only. "
            "Connect Supabase for permanent multi-day history."
        )


    if st.button(
        "🔄 Update results",
        use_container_width=True
    ):

        updated_count = 0


        for row in fetch_predictions():

            before = row.get(
                "result_status"
            )


            after = settle_prediction(
                row
            )


            if (
                before
                !=
                "CLOSED"
                and
                after.get(
                    "result_status"
                )
                ==
                "CLOSED"
            ):

                updated_count += 1


        st.success(
            f"Updated "
            f"{updated_count} "
            f"prediction(s)."
        )


    rows = fetch_predictions()

    settled_rows = []


    for row in rows:

        trade_date = (
            pd.to_datetime(
                row[
                    "trade_date"
                ]
            )
            .date()
        )


        if (
            row.get(
                "result_status"
            )
            !=
            "CLOSED"
            and
            (
                trade_date
                <
                now_et().date()
                or
                (
                    trade_date
                    ==
                    now_et().date()
                    and
                    SESSION
                    ==
                    "AFTERHOURS"
                )
            )
        ):

            row = settle_prediction(
                row
            )


        settled_rows.append(
            row
        )


    rows = settled_rows


    closed = [

        row

        for row
        in rows

        if row.get(
            "result_status"
        )
        ==
        "CLOSED"
    ]


    if closed:

        scored = [

            row

            for row
            in closed

            if row.get(
                "direction_correct"
            )
            is not None
        ]


        correct = sum(

            1

            for row
            in scored

            if row.get(
                "direction_correct"
            )
            is True
        )


        accuracy = (

            correct
            /
            len(
                scored
            )

            if scored

            else None
        )


        col1, col2, col3, col4 = (
            st.columns(
                4
            )
        )


        col1.metric(
            "Closed",
            len(
                closed
            )
        )


        col2.metric(
            "Accuracy",
            (
                f"{accuracy:.1%}"

                if accuracy
                is not None

                else "—"
            )
        )


        col3.metric(
            "T1 hit",
            sum(
                bool(
                    row.get(
                        "target1_hit"
                    )
                )

                for row
                in closed
            )
        )


        col4.metric(
            "Stop hit",
            sum(
                bool(
                    row.get(
                        "stop_hit"
                    )
                )

                for row
                in closed
            )
        )


    if not rows:

        st.info(
            "No tracked predictions yet."
        )


    for row in rows:


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

            icon = ""


        with st.expander(

            f"{icon} "
            f"{row['ticker']} — "
            f"{row['prediction']} — "
            f"{row['trade_date']} — "
            f"{row.get('result_status','OPEN')}"
        ):


            st.write(
                f"Start price: "
                f"**${float(row['start_price']):.2f}**"
            )


            st.write(
                f"Scores Day / Swing / Quality: "
                f"**{row['day_score']} / "
                f"{row['swing_score']} / "
                f"{row['quality_score']}**"
            )


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
                f"Targets: "
                f"**${float(row['target1']):.2f} / "
                f"${float(row['target2']):.2f}**"
            )


            if (
                row.get(
                    "result_status"
                )
                ==
                "CLOSED"
            ):


                change = (

                    float(
                        row[
                            "close_price"
                        ]
                    )

                    /

                    float(
                        row[
                            "start_price"
                        ]
                    )

                    -

                    1
                )


                st.divider()


                st.write(
                    f"Closing price: "
                    f"**${float(row['close_price']):.2f}**"
                )


                st.write(
                    f"Tracked-to-close change: "
                    f"**{change:+.2%}**"
                )


                st.write(
                    f"High / Low: "
                    f"**${float(row['day_high']):.2f} / "
                    f"${float(row['day_low']):.2f}**"
                )


                if (
                    row.get(
                        "direction_correct"
                    )
                    is True
                ):

                    st.success(
                        "Directional prediction: CORRECT"
                    )


                elif (
                    row.get(
                        "direction_correct"
                    )
                    is False
                ):

                    st.error(
                        "Directional prediction: WRONG"
                    )


                else:

                    st.info(
                        "Neutral prediction — "
                        "not counted as correct or wrong."
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


    if closed:

        tracker_dataframe = (
            pd.DataFrame(
                closed
            )
        )


        st.download_button(
            "Download closed predictions CSV",

            tracker_dataframe.to_csv(
                index=False
            ),

            "prediction_tracker.csv",

            "text/csv",

            use_container_width=True
        )


# ============================================================
# HELP
# ============================================================

with st.expander(
    "How the Prediction Tracker works"
):

    st.markdown(
        """
1. Scan or analyze a stock.
2. Tap **Track this prediction today**.
3. The app saves the prediction, starting price, scores, buy zone, stop and targets.
4. After the trading day ends, open **Prediction Tracker**.
5. Tap **Update results**.
6. The app compares the prediction with the actual closing price.
7. It records whether the direction was correct and whether Target 1, Target 2 or the stop were reached.

The tracker can calculate your running directional accuracy.

Without Supabase, the history is temporary and may disappear when Streamlit restarts.

Once Supabase is connected, predictions can be saved permanently across days.
"""
    )


st.divider()


st.caption(
    f"Page refreshed: "
    f"{now_et().strftime('%I:%M:%S %p ET')} "
    f"• Session: {SESSION_LABEL}"
)
