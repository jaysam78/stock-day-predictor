import numpy as np

import pandas as pd

import streamlit as st

import yfinance as yf

# ============================================================

# PAGE SETUP

# ============================================================

st.set_page_config(

    page_title="Morning Market Trader",

    page_icon="📈",

    layout="centered"

)

st.markdown(

    """

    <style>

    .block-container {

        padding-top: 1rem;

        padding-bottom: 4rem;

        max-width: 900px;

    }

    div[data-testid="stMetric"] {

        background: rgba(128,128,128,0.08);

        padding: 10px;

        border-radius: 12px;

    }

    </style>

    """,

    unsafe_allow_html=True

)

st.title("Morning Market Trader")

st.caption(

    "Morning stock scanner with entry zones, stops, targets and short-term trade plans."

)

st.warning(

    "Trade plans are model-generated research signals, not guarantees or personalized financial advice."

)

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

# ============================================================

# SECTOR MAPPING

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

def download_data(ticker, period="1y"):

    try:

        df = yf.download(

            ticker,

            period=period,

            interval="1d",

            auto_adjust=True,

            progress=False,

            threads=False

        )

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        return df.dropna()

    except Exception:

        return pd.DataFrame()

def get_series(df, column):

    if df is None or df.empty:

        return pd.Series(dtype=float)

    if column not in df.columns:

        return pd.Series(dtype=float)

    x = df[column]

    if isinstance(x, pd.DataFrame):

        x = x.iloc[:, 0]

    return pd.to_numeric(

        x,

        errors="coerce"

    )

def clamp(value, low, high):

    return max(

        low,

        min(

            high,

            value

        )

    )

# ============================================================

# INDICATORS

# ============================================================

def calculate_rsi(close, period=14):

    delta = close.diff()

    gains = delta.clip(

        lower=0

    ).rolling(

        period

    ).mean()

    losses = (

        -delta.clip(

            upper=0

        )

    ).rolling(

        period

    ).mean()

    rs = gains / losses.replace(

        0,

        np.nan

    )

    return 100 - (

        100 /

        (1 + rs)

    )

def calculate_atr(df, period=14):

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

    previous_close = close.shift(1)

    tr1 = high - low

    tr2 = (

        high -

        previous_close

    ).abs()

    tr3 = (

        low -

        previous_close

    ).abs()

    true_range = pd.concat(

        [

            tr1,

            tr2,

            tr3

        ],

        axis=1

    ).max(

        axis=1

    )

    return true_range.rolling(

        period

    ).mean()

def rsi_label(value):

    if np.isnan(value):

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

# MARKET INDEX

# ============================================================

def market_index(ticker):

    if ticker.endswith(".TO"):

        return "^GSPTSE"

    if ticker in NASDAQ:

        return "^IXIC"

    return "^GSPC"

# ============================================================

# TRADE PLAN

# ============================================================

def create_trade_plan(

    df,

    day_score,

    swing_score,

    rsi_value

):

    close = get_series(

        df,

        "Close"

    )

    high = get_series(

        df,

        "High"

    )

    low = get_series(

        df,

        "Low"

    )

    atr_series = calculate_atr(

        df

    )

    price = float(

        close.iloc[-1]

    )

    atr = float(

        atr_series.iloc[-1]

    )

    if np.isnan(atr) or atr <= 0:

        atr = price * 0.02

    # --------------------------------------------------------

    # SUPPORT / RESISTANCE

    # --------------------------------------------------------

    recent_low_10 = float(

        low.tail(10).min()

    )

    recent_low_20 = float(

        low.tail(20).min()

    )

    recent_high_10 = float(

        high.tail(10).max()

    )

    recent_high_20 = float(

        high.tail(20).max()

    )

    support = max(

        recent_low_10,

        price - 1.5 * atr

    )

    stronger_support = max(

        recent_low_20,

        price - 2.2 * atr

    )

    resistance = max(

        recent_high_10,

        price + 1.0 * atr

    )

    stronger_resistance = max(

        recent_high_20,

        price + 2.0 * atr

    )

    # --------------------------------------------------------

    # ENTRY ZONE

    # --------------------------------------------------------

    entry_low = max(

        support + 0.20 * atr,

        price - 0.50 * atr

    )

    entry_high = min(

        price + 0.15 * atr,

        resistance - 0.20 * atr

    )

    if entry_high < entry_low:

        entry_high = price

    # --------------------------------------------------------

    # STOP

    # --------------------------------------------------------

    stop = min(

        stronger_support,

        entry_low - 0.90 * atr

    )

    # --------------------------------------------------------

    # TARGETS

    # --------------------------------------------------------

    target1 = max(

        resistance,

        entry_high + 1.30 * atr

    )

    target2 = max(

        stronger_resistance,

        entry_high + 2.40 * atr

    )

    # --------------------------------------------------------

    # RISK / REWARD

    # --------------------------------------------------------

    entry_mid = (

        entry_low +

        entry_high

    ) / 2

    risk = (

        entry_mid -

        stop

    )

    reward1 = (

        target1 -

        entry_mid

    )

    reward2 = (

        target2 -

        entry_mid

    )

    if risk > 0:

        rr1 = reward1 / risk

        rr2 = reward2 / risk

    else:

        rr1 = 0

        rr2 = 0

    # --------------------------------------------------------

    # ENTRY STATUS

    # --------------------------------------------------------

    if rsi_value >= 80:

        entry_status = "DON'T CHASE"

        entry_reason = (

            "Momentum is extremely extended. "

            "Wait for a pullback before considering an entry."

        )

    elif (

        rsi_value >= 70

        and

        day_score >= 65

    ):

        entry_status = "WAIT FOR PULLBACK"

        entry_reason = (

            "The setup is bullish, but price momentum is already stretched."

        )

    elif (

        day_score >= 75

        and

        swing_score >= 70

        and

        rr1 >= 1.3

    ):

        entry_status = "GOOD ENTRY SETUP"

        entry_reason = (

            "Momentum, trend and estimated risk/reward are favourable."

        )

    elif (

        day_score >= 65

        or

        swing_score >= 70

    ):

        entry_status = "WAIT FOR CONFIRMATION"

        entry_reason = (

            "The setup is promising, but stronger confirmation or a better entry price would improve the trade."

        )

    elif (

        day_score <= 40

        and

        swing_score <= 45

    ):

        entry_status = "AVOID"

        entry_reason = (

            "Short-term price momentum and trend are currently unfavourable."

        )

    else:

        entry_status = "NO CLEAR ENTRY"

        entry_reason = (

            "The current setup does not show a strong enough edge."

        )

    return {

        "atr":

            atr,

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

        "entry_status":

            entry_status,

        "entry_reason":

            entry_reason,

        "support":

            support,

        "resistance":

            resistance

    }

# ============================================================

# ANALYZE STOCK

# ============================================================

def analyze_stock(ticker):

    stock = download_data(

        ticker

    )

    if stock.empty:

        return None

    close = get_series(

        stock,

        "Close"

    )

    volume = get_series(

        stock,

        "Volume"

    )

    if len(close) < 70:

        return None

    price = float(

        close.iloc[-1]

    )

    ret1 = close.pct_change(

        1

    ).iloc[-1]

    ret3 = close.pct_change(

        3

    ).iloc[-1]

    ret5 = close.pct_change(

        5

    ).iloc[-1]

    ret20 = close.pct_change(

        20

    ).iloc[-1]

    ma5 = close.rolling(

        5

    ).mean().iloc[-1]

    ma20 = close.rolling(

        20

    ).mean().iloc[-1]

    ma50 = close.rolling(

        50

    ).mean().iloc[-1]

    rsi_value = calculate_rsi(

        close

    ).iloc[-1]

    average_volume = volume.rolling(

        20

    ).mean().iloc[-1]

    if (

        average_volume > 0

        and

        not np.isnan(

            average_volume

        )

    ):

        relative_volume = (

            volume.iloc[-1] /

            average_volume

        )

    else:

        relative_volume = 1.0

    # --------------------------------------------------------

    # MARKET

    # --------------------------------------------------------

    market = download_data(

        market_index(

            ticker

        )

    )

    market_close = get_series(

        market,

        "Close"

    )

    if len(

        market_close

    ) >= 2:

        market_move = (

            market_close.iloc[-1]

            /

            market_close.iloc[-2]

            - 1

        )

    else:

        market_move = 0

    # --------------------------------------------------------

    # SECTOR

    # --------------------------------------------------------

    default_sector = (

        "XIU.TO"

        if ticker.endswith(

            ".TO"

        )

        else

        "SPY"

    )

    sector_symbol = SECTOR.get(

        ticker,

        default_sector

    )

    sector = download_data(

        sector_symbol

    )

    sector_close = get_series(

        sector,

        "Close"

    )

    if len(

        sector_close

    ) >= 2:

        sector_move = (

            sector_close.iloc[-1]

            /

            sector_close.iloc[-2]

            - 1

        )

    else:

        sector_move = 0

    # ========================================================

    # DAY SCORE

    # ========================================================

    day = 50

    day += (

        12 *

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

        9 *

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

                ma20

                - 1

            )

            /

            0.025

        )

    )

    if relative_volume >= 2:

        day += 7

    elif relative_volume >= 1.5:

        day += 5

    elif relative_volume >= 1.2:

        day += 3

    if 55 <= rsi_value <= 68:

        day += 4

    if rsi_value > 80:

        day -= 8

    elif rsi_value > 73:

        day -= 4

    day_score = int(

        clamp(

            round(day),

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

                ma20

                - 1

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

                ma50

                - 1

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

    if 50 <= rsi_value <= 68:

        swing += 4

    if rsi_value > 80:

        swing -= 8

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

    # SETUP LABEL

    # ========================================================

    if (

        day_score >= 75

        and

        swing_score >= 70

    ):

        setup = "STRONG SETUP"

    elif day_score >= 70:

        setup = "DAY TRADE WATCH"

    elif swing_score >= 75:

        setup = "SWING BUY CANDIDATE"

    elif (

        day_score >= 60

        or

        swing_score >= 65

    ):

        setup = "WATCH"

    elif (

        day_score <= 40

        and

        swing_score <= 45

    ):

        setup = "AVOID / BEARISH"

    else:

        setup = "NEUTRAL"

    plan = create_trade_plan(

        stock,

        day_score,

        swing_score,

        rsi_value

    )

    return {

        "ticker":

            ticker,

        "company":

            ALL_NAMES.get(

                ticker,

                ticker

            ),

        "price":

            price,

        "day_score":

            day_score,

        "swing_score":

            swing_score,

        "setup":

            setup,

        "rsi":

            rsi_value,

        "rsi_label":

            rsi_label(

                rsi_value

            ),

        "relative_volume":

            relative_volume,

        "ret1":

            ret1,

        "ret5":

            ret5,

        "market_move":

            market_move,

        "sector_move":

            sector_move,

        "plan":

            plan,

        "rank_score":

            (

                day_score *

                0.55

                +

                swing_score *

                0.45

            )

    }

# ============================================================

# HOLDING SIGNAL

# ============================================================

def holding_signal(

    result,

    purchase_price=None

):

    day = result[

        "day_score"

    ]

    swing = result[

        "swing_score"

    ]

    price = result[

        "price"

    ]

    stop = result[

        "plan"

    ][

        "stop"

    ]

    target1 = result[

        "plan"

    ][

        "target1"

    ]

    if price <= stop:

        return (

            "SELL / REVIEW",

            "Price is at or below the model's stop level."

        )

    if (

        day <= 40

        and

        swing <= 45

    ):

        return (

            "SELL / REVIEW",

            "Both short-term model scores have weakened materially."

        )

    if price >= target1:

        return (

            "TAKE PROFIT / TRIM",

            "Price has reached the first model target."

        )

    if (

        day >= 70

        or

        swing >= 70

    ):

        return (

            "HOLD / ADD WATCH",

            "The trend remains favourable."

        )

    if (

        day <= 45

        or

        swing <= 45

    ):

        return (

            "HOLD — CAUTION",

            "Momentum is weakening, so monitor the stop level."

        )

    return (

        "HOLD",

        "The setup remains neutral to moderately favourable."

    )

# ============================================================

# SAVED LISTS

# ============================================================

try:

    saved_holdings = st.query_params.get(

        "holdings",

        "TRP.TO"

    )

    saved_watchlist = st.query_params.get(

        "watchlist",

        ""

    )

except Exception:

    saved_holdings = "TRP.TO"

    saved_watchlist = ""

st.subheader(

    "My Holdings"

)

holdings_text = st.text_input(

    "Stocks you already own",

    value=saved_holdings,

    help="Example: TRP.TO, RY.TO, NVDA"

)

st.subheader(

    "⭐ My Watchlist"

)

watchlist_text = st.text_input(

    "Stocks you want to follow",

    value=saved_watchlist,

    help="Example: CVE.TO, CNQ.TO, NVDA"

)

holdings = [

    x.strip().upper()

    for x in holdings_text.split(",")

    if x.strip()

]

watchlist = [

    x.strip().upper()

    for x in watchlist_text.split(",")

    if x.strip()

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

        "Saved in this app URL."

    )

# ============================================================

# TABS

# ============================================================

scan_tab, my_tab, single_tab = st.tabs(

    [

        "Morning Scan",

        "⭐ My Stocks",

        "Analyze Stock"

    ]

)

# ============================================================

# MORNING SCAN

# ============================================================

with scan_tab:

    market_choice = st.selectbox(

        "Market",

        [

            "TSX",

            "S&P 500",

            "Nasdaq-100",

            "All Markets"

        ]

    )

    scan_size = st.selectbox(

        "Stocks to scan",

        [

            10,

            20,

            30,

            50

        ],

        index=1

    )

    if st.button(

        "🔎 Run Morning Scan",

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

        progress = st.progress(

            0

        )

        status = st.empty()

        for i, ticker in enumerate(

            universe

        ):

            status.write(

                f"Analyzing {ticker}..."

            )

            result = analyze_stock(

                ticker

            )

            if result:

                results.append(

                    result

                )

            progress.progress(

                (

                    i + 1

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

                "No scan results."

            )

        else:

            results = sorted(

                results,

                key=lambda x:

                x[

                    "rank_score"

                ],

                reverse=True

            )

            best = results[

                0

            ]

            st.subheader(

                "🏆 Best Overall Setup"

            )

            st.header(

                best[

                    "ticker"

                ]

            )

            st.write(

                best[

                    "company"

                ]

            )

            c1, c2 = st.columns(

                2

            )

            c1.metric(

                "Day",

                f"{best['day_score']}/100"

            )

            c2.metric(

                "2–5 Day",

                f"{best['swing_score']}/100"

            )

            st.subheader(

                best[

                    "setup"

                ]

            )

            st.info(

                f"**{best['plan']['entry_status']}**\n\n"

                f"{best['plan']['entry_reason']}"

            )

            st.subheader(

                "Trade Plan"

            )

            st.write(

                f"**Current price:** "

                f"${best['price']:.2f}"

            )

            st.write(

                f"**Entry zone:** "

                f"${best['plan']['entry_low']:.2f} "

                f"– "

                f"${best['plan']['entry_high']:.2f}"

            )

            st.write(

                f"**Stop:** "

                f"${best['plan']['stop']:.2f}"

            )

            st.write(

                f"**Target 1:** "

                f"${best['plan']['target1']:.2f}"

            )

            st.write(

                f"**Target 2:** "

                f"${best['plan']['target2']:.2f}"

            )

            st.write(

                f"**Risk / Reward:** "

                f"1 : {best['plan']['rr1']:.1f} "

                f"to Target 1"

            )

            st.write(

                f"**ATR:** "

                f"${best['plan']['atr']:.2f}"

            )

            st.write(

                f"**RSI:** "

                f"{best['rsi']:.0f} "

                f"— "

                f"{best['rsi_label']}"

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

                    f"Day {result['day_score']} — "

                    f"Swing {result['swing_score']} — "

                    f"{result['plan']['entry_status']}"

                )

                with st.expander(

                    title

                ):

                    st.write(

                        f"**{result['company']}**"

                    )

                    st.write(

                        f"Setup: "

                        f"**{result['setup']}**"

                    )

                    st.write(

                        f"Current: "

                        f"**${result['price']:.2f}**"

                    )

                    st.write(

                        f"Entry: "

                        f"**${result['plan']['entry_low']:.2f} "

                        f"– "

                        f"${result['plan']['entry_high']:.2f}**"

                    )

                    st.write(

                        f"Stop: "

                        f"**${result['plan']['stop']:.2f}**"

                    )

                    st.write(

                        f"Target 1: "

                        f"**${result['plan']['target1']:.2f}**"

                    )

                    st.write(

                        f"Target 2: "

                        f"**${result['plan']['target2']:.2f}**"

                    )

                    st.write(

                        f"Risk/Reward: "

                        f"**1:{result['plan']['rr1']:.1f}**"

                    )

                    st.write(

                        f"RSI: "

                        f"**{result['rsi']:.0f}** "

                        f"— "

                        f"{result['rsi_label']}"

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

    if not personal:

        st.info(

            "Add stocks to Holdings or Watchlist first."

        )

    else:

        if st.button(

            "Refresh My Stocks",

            use_container_width=True

        ):

            for ticker in personal:

                result = analyze_stock(

                    ticker

                )

                if not result:

                    continue

                st.subheader(

                    ticker

                )

                if ticker in holdings:

                    action, reason = holding_signal(

                        result

                    )

                    st.header(

                        action

                    )

                    st.write(

                        reason

                    )

                else:

                    st.header(

                        result[

                            "plan"

                        ][

                            "entry_status"

                        ]

                    )

                c1, c2 = st.columns(

                    2

                )

                c1.metric(

                    "Day",

                    f"{result['day_score']}/100"

                )

                c2.metric(

                    "2–5 Day",

                    f"{result['swing_score']}/100"

                )

                st.write(

                    f"Current: "

                    f"**${result['price']:.2f}**"

                )

                st.write(

                    f"Entry zone: "

                    f"**${result['plan']['entry_low']:.2f} "

                    f"– "

                    f"${result['plan']['entry_high']:.2f}**"

                )

                st.write(

                    f"Stop: "

                    f"**${result['plan']['stop']:.2f}**"

                )

                st.write(

                    f"Target 1: "

                    f"**${result['plan']['target1']:.2f}**"

                )

                st.write(

                    f"Target 2: "

                    f"**${result['plan']['target2']:.2f}**"

                )

                st.write(

                    f"Risk/Reward: "

                    f"**1:{result['plan']['rr1']:.1f}**"

                )

                st.write(

                    f"RSI: "

                    f"**{result['rsi']:.0f}** "

                    f"— "

                    f"{result['rsi_label']}"

                )

                st.divider()

# ============================================================

# SINGLE STOCK

# ============================================================

with single_tab:

    ticker = st.text_input(

        "Ticker",

        value="CVE.TO",

        key="single_stock"

    ).upper()

    if st.button(

        "Analyze This Stock",

        use_container_width=True

    ):

        result = analyze_stock(

            ticker

        )

        if not result:

            st.error(

                "Not enough market data."

            )

        else:

            st.header(

                ticker

            )

            st.subheader(

                result[

                    "setup"

                ]

            )

            c1, c2 = st.columns(

                2

            )

            c1.metric(

                "Day",

                f"{result['day_score']}/100"

            )

            c2.metric(

                "2–5 Day",

                f"{result['swing_score']}/100"

            )

            st.info(

                f"**{result['plan']['entry_status']}**\n\n"

                f"{result['plan']['entry_reason']}"

            )

            st.subheader(

                "Trade Plan"

            )

            st.write(

                f"Current price: "

                f"**${result['price']:.2f}**"

            )

            st.write(

                f"Entry zone: "

                f"**${result['plan']['entry_low']:.2f} "

                f"– "

                f"${result['plan']['entry_high']:.2f}**"

            )

            st.write(

                f"Stop: "

                f"**${result['plan']['stop']:.2f}**"

            )

            st.write(

                f"Target 1: "

                f"**${result['plan']['target1']:.2f}**"

            )

            st.write(

                f"Target 2: "

                f"**${result['plan']['target2']:.2f}**"

            )

            st.write(

                f"Risk/Reward Target 1: "

                f"**1:{result['plan']['rr1']:.1f}**"

            )

            st.write(

                f"Risk/Reward Target 2: "

                f"**1:{result['plan']['rr2']:.1f}**"

            )

            st.write(

                f"Support: "

                f"**${result['plan']['support']:.2f}**"

            )

            st.write(

                f"Resistance: "

                f"**${result['plan']['resistance']:.2f}**"

            )

            st.write(

                f"ATR: "

                f"**${result['plan']['atr']:.2f}**"

            )

            st.write(

                f"RSI: "

                f"**{result['rsi']:.0f}** "

                f"— "

                f"{result['rsi_label']}"

            )

# ============================================================

# HELP

# ============================================================

with st.expander(

    "How to read the Trade Plan"

):

    st.markdown(

        """

**Entry Zone**  

A price range where the model considers the risk/reward more reasonable.

**Stop**  

The model's estimated level where the setup has likely broken down.

**Target 1**  

The first reasonable profit-taking area.

**Target 2**  

A more aggressive target if momentum continues.

**Risk / Reward 1:2**  

Means roughly $2 of potential upside for every $1 of downside to the stop.

**ATR**  

Average True Range. It measures how much the stock normally moves each day.

These levels are estimates based on recent price action and volatility.

They should not be treated as guaranteed support or resistance.

"""

    )

st.divider()

st.caption(

    "Best used as a screening and trade-planning tool. "

    "Re-check the stock after the market opens because price, volume and news can change quickly."

)
