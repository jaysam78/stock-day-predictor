import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="TSX Morning Trader",
    page_icon="📈",
    layout="centered"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 950px;
    }

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.09);
        padding: 12px;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("TSX Morning Trader")

st.caption(
    "Morning scanner for TSX stocks. "
    "Estimates which stocks are favoured for today and the next 2–5 trading days."
)

st.warning(
    "BUY / HOLD / SELL labels are model signals for research only. "
    "They are not guaranteed investment recommendations."
)


# ---------------------------------------------------------
# TSX STOCK UNIVERSE
# ---------------------------------------------------------

TSX_STOCKS = {
    "RY.TO": "Royal Bank",
    "TD.TO": "TD Bank",
    "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank",
    "CM.TO": "CIBC",
    "NA.TO": "National Bank",

    "CNQ.TO": "Canadian Natural Resources",
    "SU.TO": "Suncor",
    "CVE.TO": "Cenovus",
    "IMO.TO": "Imperial Oil",

    "TRP.TO": "TC Energy",
    "ENB.TO": "Enbridge",

    "SHOP.TO": "Shopify",
    "CSU.TO": "Constellation Software",
    "OTEX.TO": "OpenText",

    "CNR.TO": "Canadian National Railway",
    "CP.TO": "CPKC",

    "ABX.TO": "Barrick Mining",
    "AEM.TO": "Agnico Eagle",
    "WPM.TO": "Wheaton Precious Metals",

    "NTR.TO": "Nutrien",
    "TECK-B.TO": "Teck Resources",

    "MFC.TO": "Manulife",
    "SLF.TO": "Sun Life",

    "FTS.TO": "Fortis",
    "EMA.TO": "Emera",

    "BCE.TO": "BCE",
    "T.TO": "TELUS",

    "ATD.TO": "Couche-Tard",
    "L.TO": "Loblaw",
}


# ---------------------------------------------------------
# SECTOR ETF MAPPING
# ---------------------------------------------------------

SECTOR_ETF = {
    "RY.TO": "XFN.TO",
    "TD.TO": "XFN.TO",
    "BMO.TO": "XFN.TO",
    "BNS.TO": "XFN.TO",
    "CM.TO": "XFN.TO",
    "NA.TO": "XFN.TO",
    "MFC.TO": "XFN.TO",
    "SLF.TO": "XFN.TO",

    "CNQ.TO": "XEG.TO",
    "SU.TO": "XEG.TO",
    "CVE.TO": "XEG.TO",
    "IMO.TO": "XEG.TO",
    "TRP.TO": "XEG.TO",
    "ENB.TO": "XEG.TO",

    "SHOP.TO": "XIT.TO",
    "CSU.TO": "XIT.TO",
    "OTEX.TO": "XIT.TO",

    "ABX.TO": "XMA.TO",
    "AEM.TO": "XMA.TO",
    "WPM.TO": "XMA.TO",
    "NTR.TO": "XMA.TO",
    "TECK-B.TO": "XMA.TO",

    "FTS.TO": "XUT.TO",
    "EMA.TO": "XUT.TO",

    "BCE.TO": "XEI.TO",
    "T.TO": "XEI.TO",

    "ATD.TO": "XST.TO",
    "L.TO": "XST.TO",

    "CNR.TO": "XIU.TO",
    "CP.TO": "XIU.TO",
}


# ---------------------------------------------------------
# DATA FUNCTIONS
# ---------------------------------------------------------

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

    s = df[column]

    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]

    return pd.to_numeric(s, errors="coerce")


# ---------------------------------------------------------
# TECHNICAL INDICATORS
# ---------------------------------------------------------

def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()

    rs = gain / loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def clamp(value, minimum, maximum):

    return max(minimum, min(maximum, value))


# ---------------------------------------------------------
# MARKET SCORING MODEL
# ---------------------------------------------------------

def analyze_stock(ticker):

    stock = download_data(ticker)

    if stock.empty or len(stock) < 70:
        return None

    market = download_data("^GSPTSE")

    sector_symbol = SECTOR_ETF.get(ticker, "XIU.TO")
    sector = download_data(sector_symbol)

    close = get_series(stock, "Close")
    volume = get_series(stock, "Volume")

    if len(close) < 70:
        return None

    # Price momentum
    ret1 = close.pct_change(1).iloc[-1]
    ret3 = close.pct_change(3).iloc[-1]
    ret5 = close.pct_change(5).iloc[-1]
    ret20 = close.pct_change(20).iloc[-1]

    # Moving averages
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    # RSI
    rsi_value = calculate_rsi(close).iloc[-1]

    # Volume
    volume_mean = volume.rolling(20).mean().iloc[-1]
    volume_std = volume.rolling(20).std().iloc[-1]

    if volume_std and not np.isnan(volume_std):
        volume_z = (
            volume.iloc[-1] - volume_mean
        ) / volume_std
    else:
        volume_z = 0

    # TSX direction
    market_close = get_series(market, "Close")

    if len(market_close) >= 2:
        market_move = (
            market_close.iloc[-1] /
            market_close.iloc[-2]
            - 1
        )
    else:
        market_move = 0

    # Sector direction
    sector_close = get_series(sector, "Close")

    if len(sector_close) >= 2:
        sector_move = (
            sector_close.iloc[-1] /
            sector_close.iloc[-2]
            - 1
        )
    else:
        sector_move = 0


    # -----------------------------------------------------
    # TODAY SCORE
    # -----------------------------------------------------

    today_score = 0

    today_score += 0.22 * np.tanh(ret1 / 0.015)
    today_score += 0.15 * np.tanh(ret3 / 0.025)
    today_score += 0.10 * np.tanh(ret5 / 0.04)

    today_score += 0.15 * np.tanh(
        market_move / 0.012
    )

    today_score += 0.18 * np.tanh(
        sector_move / 0.015
    )

    today_score += 0.08 * np.tanh(
        volume_z / 2
    )

    ma_signal = (
        ma5 / ma20
    ) - 1

    today_score += 0.12 * np.tanh(
        ma_signal / 0.025
    )


    # RSI adjustment

    if not np.isnan(rsi_value):

        if rsi_value > 78:
            today_score -= 0.08

        elif rsi_value > 70:
            today_score -= 0.03

        elif rsi_value < 30:
            today_score += 0.04


    today_probability = clamp(
        0.50 + today_score * 0.25,
        0.30,
        0.78
    )


    # -----------------------------------------------------
    # NEXT 2–5 DAYS SCORE
    # -----------------------------------------------------

    swing_score = 0

    swing_score += 0.18 * np.tanh(
        ret3 / 0.025
    )

    swing_score += 0.22 * np.tanh(
        ret5 / 0.04
    )

    swing_score += 0.18 * np.tanh(
        ret20 / 0.09
    )

    swing_score += 0.15 * np.tanh(
        ((ma5 / ma20) - 1) / 0.03
    )

    swing_score += 0.16 * np.tanh(
        ((ma20 / ma50) - 1) / 0.05
    )

    swing_score += 0.11 * np.tanh(
        sector_move / 0.015
    )


    if not np.isnan(rsi_value):

        if 45 <= rsi_value <= 68:
            swing_score += 0.04

        elif rsi_value > 78:
            swing_score -= 0.07


    swing_probability = clamp(
        0.50 + swing_score * 0.27,
        0.30,
        0.80
    )


    latest_price = float(close.iloc[-1])


    return {

        "ticker": ticker,

        "company":
            TSX_STOCKS.get(
                ticker,
                ticker
            ),

        "price":
            latest_price,

        "today":
            today_probability,

        "swing":
            swing_probability,

        "ret1":
            ret1,

        "ret5":
            ret5,

        "ret20":
            ret20,

        "rsi":
            rsi_value,

        "market":
            market_move,

        "sector":
            sector_move,

        "volume_z":
            volume_z
    }


# ---------------------------------------------------------
# BUY / HOLD / SELL SIGNAL
# ---------------------------------------------------------

def get_signal(today, swing, owned=False):

    if owned:

        if today >= 0.64 and swing >= 0.62:
            return "ADD / BUY"

        elif today <= 0.42 and swing <= 0.45:
            return "SELL / REVIEW"

        elif today <= 0.46 or swing <= 0.46:
            return "HOLD — CAUTION"

        else:
            return "HOLD"


    else:

        if today >= 0.64 and swing >= 0.62:
            return "BUY CANDIDATE"

        elif today >= 0.59 and swing >= 0.57:
            return "WATCH / POSSIBLE BUY"

        elif today <= 0.42 and swing <= 0.45:
            return "AVOID / BEARISH"

        else:
            return "NEUTRAL"


def confidence(today, swing):

    strongest_edge = max(
        abs(today - 0.50),
        abs(swing - 0.50)
    )

    if strongest_edge >= 0.16:
        return "HIGH"

    elif strongest_edge >= 0.10:
        return "MEDIUM"

    else:
        return "LOW"


# ---------------------------------------------------------
# FAVOURITES
# ---------------------------------------------------------

st.subheader("My Holdings / Favourites")

default_favourites = "TRP.TO"

favourites_text = st.text_input(
    "Enter stocks you own or want to watch",
    value=default_favourites,
    help="Example: TRP.TO, RY.TO, CNQ.TO"
)

favourites = [
    x.strip().upper()
    for x in favourites_text.split(",")
    if x.strip()
]


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------

scanner_tab, stock_tab = st.tabs(
    [
        "Morning TSX Scanner",
        "Analyze One Stock"
    ]
)


# =========================================================
# MORNING SCANNER
# =========================================================

with scanner_tab:

    st.subheader(
        "Stocks favoured to rise"
    )

    st.write(
        "Run this before the market opens or early in the trading day."
    )

    scan_size = st.selectbox(
        "Number of TSX stocks to scan",
        [
            10,
            20,
            30
        ],
        index=1
    )

    if st.button(
        "Scan TSX Now",
        type="primary",
        use_container_width=True
    ):

        universe = list(
            TSX_STOCKS.keys()
        )[:scan_size]

        for favourite in favourites:

            if favourite not in universe:
                universe.insert(
                    0,
                    favourite
                )


        results = []


        progress = st.progress(0)

        status = st.empty()


        for index, ticker in enumerate(universe):

            status.write(
                f"Analyzing {ticker}..."
            )

            analysis = analyze_stock(
                ticker
            )

            if analysis:

                analysis["owned"] = (
                    ticker in favourites
                )

                analysis["signal"] = get_signal(
                    analysis["today"],
                    analysis["swing"],
                    analysis["owned"]
                )

                analysis["confidence"] = confidence(
                    analysis["today"],
                    analysis["swing"]
                )

                analysis["rank_score"] = (
                    analysis["today"] * 0.55
                    +
                    analysis["swing"] * 0.45
                )

                results.append(
                    analysis
                )


            progress.progress(
                (index + 1)
                /
                len(universe)
            )


        status.empty()

        progress.empty()


        if not results:

            st.error(
                "No scanner results were returned."
            )

        else:

            df = pd.DataFrame(
                results
            )

            df = df.sort_values(
                "rank_score",
                ascending=False
            )


            # -------------------------------------------------
            # HOLDINGS
            # -------------------------------------------------

            owned_df = df[
                df["owned"]
            ]


            if not owned_df.empty:

                st.subheader(
                    "My Holdings / Favourites"
                )


                for _, row in owned_df.iterrows():

                    st.markdown(
                        f"""
### {row['ticker']} — {row['signal']}

**Today:** {row['today']:.0%} probability UP  
**Next 2–5 days:** {row['swing']:.0%} probability UP  
**Confidence:** {row['confidence']}  
**Latest price:** ${row['price']:,.2f}
"""
                    )


            # -------------------------------------------------
            # TOP OPPORTUNITIES
            # -------------------------------------------------

            st.subheader(
                "Top TSX Opportunities"
            )


            display = df[
                [
                    "ticker",
                    "company",
                    "today",
                    "swing",
                    "signal",
                    "confidence",
                    "ret1",
                    "ret5",
                    "rsi"
                ]
            ].copy()


            display.columns = [
                "Ticker",
                "Company",
                "Today",
                "2–5 Days",
                "Signal",
                "Confidence",
                "1 Day",
                "5 Days",
                "RSI"
            ]


            display["Today"] = (
                display["Today"]
                .map(
                    lambda x:
                    f"{x:.0%}"
                )
            )


            display["2–5 Days"] = (
                display["2–5 Days"]
                .map(
                    lambda x:
                    f"{x:.0%}"
                )
            )


            display["1 Day"] = (
                display["1 Day"]
                .map(
                    lambda x:
                    f"{x:+.1%}"
                )
            )


            display["5 Days"] = (
                display["5 Days"]
                .map(
                    lambda x:
                    f"{x:+.1%}"
                )
            )


            display["RSI"] = (
                display["RSI"]
                .map(
                    lambda x:
                    f"{x:.0f}"
                    if not np.isnan(x)
                    else "—"
                )
            )


            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True
            )


            # -------------------------------------------------
            # BEST SETUP
            # -------------------------------------------------

            best = df.iloc[0]


            st.subheader(
                "Best current setup"
            )


            st.metric(
                "Stock",
                best["ticker"]
            )


            a, b = st.columns(2)


            a.metric(
                "Today UP",
                f"{best['today']:.0%}"
            )


            b.metric(
                "Next 2–5 days UP",
                f"{best['swing']:.0%}"
            )


            st.write(
                f"**Model signal:** "
                f"{best['signal']}"
            )


            st.write(
                f"**Confidence:** "
                f"{best['confidence']}"
            )


            if (
                best["today"] < 0.59
                and
                best["swing"] < 0.60
            ):

                st.warning(
                    "No strong BUY setup was found. "
                    "The model is not forcing a trade."
                )


# =========================================================
# SINGLE STOCK ANALYSIS
# =========================================================

with stock_tab:

    st.subheader(
        "Analyze one stock"
    )


    ticker = st.text_input(
        "TSX ticker",
        value="CNQ.TO",
        key="single_stock"
    ).upper()


    if st.button(
        "Analyze Stock",
        use_container_width=True
    ):

        with st.spinner(
            f"Analyzing {ticker}..."
        ):

            result = analyze_stock(
                ticker
            )


        if result is None:

            st.error(
                "Not enough market data was available."
            )

        else:

            owned = ticker in favourites


            signal = get_signal(
                result["today"],
                result["swing"],
                owned
            )


            st.header(
                signal
            )


            c1, c2 = st.columns(2)


            c1.metric(
                "Today — UP probability",
                f"{result['today']:.0%}"
            )


            c2.metric(
                "Next 2–5 days",
                f"{result['swing']:.0%}"
            )


            st.metric(
                "Latest price",
                f"${result['price']:,.2f}"
            )


            st.subheader(
                "Current signals"
            )


            st.write(
                f"""
**1-day move:** {result['ret1']:+.2%}

**5-day move:** {result['ret5']:+.2%}

**20-day move:** {result['ret20']:+.2%}

**RSI:** {result['rsi']:.0f}

**TSX direction:** {result['market']:+.2%}

**Sector direction:** {result['sector']:+.2%}
"""
            )


            if owned:

                st.info(
                    "This ticker is in your "
                    "Holdings / Favourites list."
                )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Best used as an early-morning screening tool. "
    "Market conditions can change quickly after the open. "
    "Confirm important news and use your own risk limits before trading."
)
