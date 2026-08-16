import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Morning Market Scanner",
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

    .stock-card {
        padding: 14px;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 15px;
        margin-bottom: 12px;
    }

    .big-score {
        font-size: 1.4rem;
        font-weight: 700;
    }

    .muted {
        opacity: 0.75;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Morning Market Scanner")

st.caption(
    "Find stocks with favourable short-term setups across Canada and the U.S."
)

st.warning(
    "Scores and BUY/WATCH/SELL labels are model signals for research only. "
    "They are not guarantees or personalized investment advice."
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
    "BRK-B": "Berkshire Hathaway",
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
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",

    "NFLX": "Netflix",
    "AMD": "AMD",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "DIS": "Disney",
    "UBER": "Uber",
    "PLTR": "Palantir",
    "CAT": "Caterpillar",
    "GE": "GE Aerospace"
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
    "MELI": "MercadoLibre",
    "BKNG": "Booking Holdings",
    "CSCO": "Cisco",
    "INTU": "Intuit",
    "ISRG": "Intuitive Surgical",
    "MRVL": "Marvell",
    "LRCX": "Lam Research",
    "KLAC": "KLA",
    "SNPS": "Synopsys",
    "CDNS": "Cadence",
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

for ticker in [
    "RY.TO", "TD.TO", "BMO.TO", "BNS.TO",
    "CM.TO", "NA.TO", "MFC.TO", "SLF.TO"
]:
    SECTOR[ticker] = "XFN.TO"

for ticker in [
    "CNQ.TO", "SU.TO", "CVE.TO",
    "IMO.TO", "TRP.TO", "ENB.TO"
]:
    SECTOR[ticker] = "XEG.TO"

for ticker in [
    "SHOP.TO", "CSU.TO", "OTEX.TO"
]:
    SECTOR[ticker] = "XIT.TO"

for ticker in [
    "ABX.TO", "AEM.TO", "WPM.TO",
    "NTR.TO", "TECK-B.TO"
]:
    SECTOR[ticker] = "XMA.TO"

for ticker in [
    "FTS.TO", "EMA.TO"
]:
    SECTOR[ticker] = "XUT.TO"


for ticker in [
    "AAPL", "MSFT", "CRM", "ORCL"
]:
    SECTOR[ticker] = "XLK"

for ticker in [
    "NVDA", "AMD", "AVGO", "QCOM",
    "INTC", "AMAT", "MU", "LRCX",
    "KLAC", "MRVL", "ARM"
]:
    SECTOR[ticker] = "SMH"

for ticker in [
    "AMZN", "TSLA", "HD"
]:
    SECTOR[ticker] = "XLY"

for ticker in [
    "META", "GOOGL", "NFLX", "DIS"
]:
    SECTOR[ticker] = "XLC"

for ticker in [
    "JPM", "BAC", "GS", "V", "MA"
]:
    SECTOR[ticker] = "XLF"

for ticker in [
    "XOM", "CVX"
]:
    SECTOR[ticker] = "XLE"


# ============================================================
# DATA FUNCTIONS
# ============================================================

@st.cache_data(ttl=600)
def download_data(ticker, period="1y"):

    try:

        data = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data.dropna()

    except Exception:

        return pd.DataFrame()


def series(data, column):

    if data is None or data.empty:
        return pd.Series(dtype=float)

    if column not in data.columns:
        return pd.Series(dtype=float)

    result = data[column]

    if isinstance(result, pd.DataFrame):
        result = result.iloc[:, 0]

    return pd.to_numeric(
        result,
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
# RSI
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
        np.nan
    )

    return 100 - (
        100 /
        (1 + rs)
    )


def rsi_description(value):

    if np.isnan(value):
        return "Unknown"

    if value < 30:
        return "Oversold"

    if value < 45:
        return "Weak momentum"

    if value < 55:
        return "Neutral"

    if value < 65:
        return "Healthy momentum"

    if value < 70:
        return "Strong momentum"

    if value < 80:
        return "Getting extended"

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
# STOCK ANALYSIS
# ============================================================

def analyze_stock(ticker):

    stock = download_data(ticker)

    if stock.empty:
        return None

    close = series(
        stock,
        "Close"
    )

    volume = series(
        stock,
        "Volume"
    )

    if len(close) < 70:
        return None


    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price = float(
        close.iloc[-1]
    )


    # --------------------------------------------------------
    # RETURNS
    # --------------------------------------------------------

    ret1 = close.pct_change(1).iloc[-1]

    ret3 = close.pct_change(3).iloc[-1]

    ret5 = close.pct_change(5).iloc[-1]

    ret20 = close.pct_change(20).iloc[-1]


    # --------------------------------------------------------
    # MOVING AVERAGES
    # --------------------------------------------------------

    ma5 = close.rolling(5).mean().iloc[-1]

    ma20 = close.rolling(20).mean().iloc[-1]

    ma50 = close.rolling(50).mean().iloc[-1]


    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    rsi_value = calculate_rsi(
        close
    ).iloc[-1]


    # --------------------------------------------------------
    # RELATIVE VOLUME
    # --------------------------------------------------------

    avg_volume = (
        volume
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    latest_volume = (
        volume.iloc[-1]
    )


    if (
        avg_volume > 0
        and not np.isnan(avg_volume)
    ):

        relative_volume = (
            latest_volume /
            avg_volume
        )

    else:

        relative_volume = 1.0


    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    market = download_data(
        market_index(ticker)
    )

    market_close = series(
        market,
        "Close"
    )

    if len(market_close) >= 2:

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
        if ticker.endswith(".TO")
        else "SPY"
    )

    sector_ticker = SECTOR.get(
        ticker,
        default_sector
    )

    sector = download_data(
        sector_ticker
    )

    sector_close = series(
        sector,
        "Close"
    )


    if len(sector_close) >= 2:

        sector_move = (
            sector_close.iloc[-1]
            /
            sector_close.iloc[-2]
            - 1
        )

    else:

        sector_move = 0


    # ========================================================
    # DAY TRADE SCORE
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


    short_trend = (
        ma5 /
        ma20
        - 1
    )


    day += (
        8 *
        np.tanh(
            short_trend /
            0.025
        )
    )


    # Relative volume bonus

    if relative_volume >= 2.0:

        day += 7

    elif relative_volume >= 1.5:

        day += 5

    elif relative_volume >= 1.2:

        day += 3


    # RSI adjustment

    if not np.isnan(rsi_value):

        if 55 <= rsi_value <= 68:

            day += 4

        elif rsi_value > 80:

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
    # 2–5 DAY SWING SCORE
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


    if not np.isnan(rsi_value):

        if 50 <= rsi_value <= 68:

            swing += 4

        elif rsi_value > 80:

            swing -= 8


    swing_score = int(
        clamp(
            round(swing),
            0,
            100
        )
    )


    # ========================================================
    # SETUP SIGNAL
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


    # ========================================================
    # ENTRY STATUS
    # ========================================================

    if (
        rsi_value >= 80
    ):

        entry_status = "DON'T CHASE"

        entry_reason = (
            "Momentum is very extended. "
            "Wait for the stock to cool off or pull back."
        )


    elif (
        rsi_value >= 70
        and
        (
            day_score >= 65
            or
            swing_score >= 70
        )
    ):

        entry_status = "WAIT FOR PULLBACK"

        entry_reason = (
            "The trend is bullish, but RSI suggests "
            "the stock may already be stretched."
        )


    elif (
        day_score >= 75
        and
        swing_score >= 70
        and
        relative_volume >= 1.2
        and
        rsi_value < 70
    ):

        entry_status = "GOOD ENTRY SETUP"

        entry_reason = (
            "Strong scores, healthy momentum and "
            "above-average trading volume are confirming each other."
        )


    elif (
        day_score >= 65
        or
        swing_score >= 70
    ):

        entry_status = "WAIT FOR CONFIRMATION"

        entry_reason = (
            "The setup looks promising, but stronger "
            "price or volume confirmation would improve it."
        )


    elif (
        day_score <= 40
        and
        swing_score <= 45
    ):

        entry_status = "AVOID"

        entry_reason = (
            "Short-term trend and momentum are currently unfavourable."
        )


    else:

        entry_status = "NO CLEAR ENTRY"

        entry_reason = (
            "There is not enough bullish confirmation yet."
        )


    # ========================================================
    # WHY?
    # ========================================================

    positives = []

    cautions = []


    if ret5 > 0.03:

        positives.append(
            "Strong recent price momentum"
        )


    if ma5 > ma20:

        positives.append(
            "Short-term trend is rising"
        )


    if ma5 > ma20 > ma50:

        positives.append(
            "Moving averages are strongly aligned"
        )


    if sector_move > 0.005:

        positives.append(
            "Sector is performing well"
        )


    if market_move > 0.005:

        positives.append(
            "Broad market is supportive"
        )


    if relative_volume >= 1.5:

        positives.append(
            "Trading volume is well above normal"
        )


    elif relative_volume >= 1.2:

        positives.append(
            "Trading volume is above normal"
        )


    if 55 <= rsi_value <= 68:

        positives.append(
            "RSI shows healthy upward momentum"
        )


    if rsi_value >= 70:

        cautions.append(
            "RSI is elevated — avoid chasing"
        )


    if relative_volume < 0.8:

        cautions.append(
            "Volume is below normal"
        )


    if sector_move < -0.005:

        cautions.append(
            "Sector is currently weak"
        )


    if market_move < -0.005:

        cautions.append(
            "Broad market is weak"
        )


    if not positives:

        positives.append(
            "No major bullish confirmation"
        )


    return {
        "ticker": ticker,

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

        "entry_status":
            entry_status,

        "entry_reason":
            entry_reason,

        "rsi":
            rsi_value,

        "rsi_description":
            rsi_description(
                rsi_value
            ),

        "relative_volume":
            relative_volume,

        "ret1":
            ret1,

        "ret5":
            ret5,

        "ret20":
            ret20,

        "market_move":
            market_move,

        "sector_move":
            sector_move,

        "positives":
            positives,

        "cautions":
            cautions,

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
# SAVED HOLDINGS + WATCHLIST
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


st.subheader("My Holdings")

holdings_text = st.text_input(
    "Stocks you already own",
    value=saved_holdings,
    help="Example: TRP.TO, RY.TO, NVDA"
)


st.subheader("⭐ My Watchlist")

watchlist_text = st.text_input(
    "Stocks you want to follow",
    value=saved_watchlist,
    help="Example: CVE.TO, CNQ.TO, NVDA, AAPL"
)


holdings = [
    item.strip().upper()
    for item
    in holdings_text.split(",")
    if item.strip()
]


watchlist = [
    item.strip().upper()
    for item
    in watchlist_text.split(",")
    if item.strip()
]


if st.button(
    "💾 Save Holdings & Watchlist",
    use_container_width=True
):

    cleaned_holdings = ",".join(
        holdings
    )

    cleaned_watchlist = ",".join(
        watchlist
    )

    st.query_params[
        "holdings"
    ] = cleaned_holdings

    st.query_params[
        "watchlist"
    ] = cleaned_watchlist

    st.success(
        "Saved. Bookmark this exact page or add it "
        "to your iPhone Home Screen to keep this list."
    )


# ============================================================
# MAIN TABS
# ============================================================

scanner_tab, favourites_tab, stock_tab = st.tabs(
    [
        "Morning Scan",
        "⭐ My Stocks",
        "Analyze Stock"
    ]
)


# ============================================================
# MORNING SCAN
# ============================================================

with scanner_tab:

    st.subheader(
        "Find today's strongest setups"
    )


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
        "How many stocks?",
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
                    list(TSX.keys())
                    +
                    list(SP500.keys())
                    +
                    list(NASDAQ.keys())
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


        for index, ticker in enumerate(
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
                    index + 1
                )
                /
                len(universe)
            )


        progress.empty()

        status.empty()


        if not results:

            st.error(
                "No scanner results were returned."
            )


        else:

            df = pd.DataFrame(
                results
            )


            # ==================================================
            # BEST OVERALL
            # ==================================================

            overall = df.sort_values(
                "rank_score",
                ascending=False
            )


            best = overall.iloc[0]


            st.subheader(
                "🏆 Best Overall Setup"
            )


            st.header(
                best["ticker"]
            )


            st.write(
                best["company"]
            )


            a, b = st.columns(2)


            a.metric(
                "Day Trade",
                f"{best['day_score']}/100"
            )


            b.metric(
                "2–5 Day",
                f"{best['swing_score']}/100"
            )


            st.subheader(
                best["setup"]
            )


            st.info(
                f"**ENTRY STATUS: {best['entry_status']}**\n\n"
                f"{best['entry_reason']}"
            )


            st.write(
                f"**RSI:** "
                f"{best['rsi']:.0f} "
                f"— {best['rsi_description']}"
            )


            st.write(
                f"**Relative Volume:** "
                f"{best['relative_volume']:.1f}× normal"
            )


            st.write(
                "**Why it ranked highly:**"
            )


            for reason in best[
                "positives"
            ]:

                st.write(
                    f"✓ {reason}"
                )


            for caution in best[
                "cautions"
            ]:

                st.write(
                    f"⚠ {caution}"
                )


            st.divider()


            # ==================================================
            # TOP DAY TRADES
            # ==================================================

            st.subheader(
                "Top Day Trade Setups"
            )


            day_results = df.sort_values(
                "day_score",
                ascending=False
            ).head(7)


            for _, row in day_results.iterrows():

                with st.expander(
                    f"{row['ticker']} — "
                    f"{row['day_score']}/100 — "
                    f"{row['entry_status']}"
                ):

                    st.write(
                        f"**{row['company']}**"
                    )

                    st.write(
                        f"Day score: "
                        f"**{row['day_score']}/100**"
                    )

                    st.write(
                        f"2–5 day score: "
                        f"**{row['swing_score']}/100**"
                    )

                    st.write(
                        f"Setup: "
                        f"**{row['setup']}**"
                    )

                    st.write(
                        f"Entry: "
                        f"**{row['entry_status']}**"
                    )

                    st.write(
                        row[
                            "entry_reason"
                        ]
                    )

                    st.write(
                        f"RSI: "
                        f"**{row['rsi']:.0f}** "
                        f"— {row['rsi_description']}"
                    )

                    st.write(
                        f"Relative volume: "
                        f"**{row['relative_volume']:.1f}×**"
                    )


            # ==================================================
            # SWING SETUPS
            # ==================================================

            st.subheader(
                "Top 2–5 Day Setups"
            )


            swing_results = df.sort_values(
                "swing_score",
                ascending=False
            ).head(7)


            for _, row in swing_results.iterrows():

                with st.expander(
                    f"{row['ticker']} — "
                    f"{row['swing_score']}/100 — "
                    f"{row['entry_status']}"
                ):

                    st.write(
                        f"**{row['company']}**"
                    )

                    st.write(
                        f"Day score: "
                        f"**{row['day_score']}/100**"
                    )

                    st.write(
                        f"2–5 day score: "
                        f"**{row['swing_score']}/100**"
                    )

                    st.write(
                        f"Setup: "
                        f"**{row['setup']}**"
                    )

                    st.write(
                        f"Entry: "
                        f"**{row['entry_status']}**"
                    )

                    st.write(
                        row[
                            "entry_reason"
                        ]
                    )

                    st.write(
                        f"RSI: "
                        f"**{row['rsi']:.0f}** "
                        f"— {row['rsi_description']}"
                    )

                    st.write(
                        f"Relative volume: "
                        f"**{row['relative_volume']:.1f}×**"
                    )


# ============================================================
# MY STOCKS
# ============================================================

with favourites_tab:

    st.subheader(
        "My Holdings & Watchlist"
    )


    all_personal = list(
        dict.fromkeys(
            holdings +
            watchlist
        )
    )


    if not all_personal:

        st.info(
            "Add stocks above to My Holdings "
            "or My Watchlist."
        )


    else:

        if st.button(
            "Refresh My Stocks",
            use_container_width=True
        ):

            for ticker in all_personal:

                with st.spinner(
                    f"Analyzing {ticker}..."
                ):

                    result = analyze_stock(
                        ticker
                    )


                if not result:

                    st.warning(
                        f"Could not analyze {ticker}."
                    )

                    continue


                owned = ticker in holdings


                label = (
                    "OWNED"
                    if owned
                    else "WATCHLIST"
                )


                st.markdown(
                    f"### {ticker} — {label}"
                )


                st.write(
                    result["company"]
                )


                c1, c2 = st.columns(2)


                c1.metric(
                    "Day",
                    f"{result['day_score']}/100"
                )


                c2.metric(
                    "2–5 Day",
                    f"{result['swing_score']}/100"
                )


                st.write(
                    f"**Setup:** "
                    f"{result['setup']}"
                )


                st.info(
                    f"**{result['entry_status']}**\n\n"
                    f"{result['entry_reason']}"
                )


                st.write(
                    f"RSI: "
                    f"**{result['rsi']:.0f}** "
                    f"— {result['rsi_description']}"
                )


                st.write(
                    f"Volume: "
                    f"**{result['relative_volume']:.1f}× normal**"
                )


                st.divider()


# ============================================================
# SINGLE STOCK
# ============================================================

with stock_tab:

    ticker = st.text_input(
        "Ticker",
        value="NVDA",
        key="single_ticker"
    ).upper()


    if st.button(
        "Analyze This Stock",
        use_container_width=True
    ):

        with st.spinner(
            f"Analyzing {ticker}..."
        ):

            result = analyze_stock(
                ticker
            )


        if not result:

            st.error(
                "Not enough market data was available."
            )


        else:

            st.header(
                ticker
            )

            st.write(
                result[
                    "company"
                ]
            )


            c1, c2 = st.columns(2)


            c1.metric(
                "Day Trade",
                f"{result['day_score']}/100"
            )


            c2.metric(
                "2–5 Day",
                f"{result['swing_score']}/100"
            )


            st.metric(
                "Latest Price",
                f"${result['price']:,.2f}"
            )


            st.subheader(
                result[
                    "setup"
                ]
            )


            st.info(
                f"**ENTRY STATUS: "
                f"{result['entry_status']}**\n\n"
                f"{result['entry_reason']}"
            )


            st.write(
                f"**RSI:** "
                f"{result['rsi']:.0f} "
                f"— {result['rsi_description']}"
            )


            st.write(
                f"**Relative Volume:** "
                f"{result['relative_volume']:.1f}× normal"
            )


            st.write(
                f"**1-Day move:** "
                f"{result['ret1']:+.2%}"
            )


            st.write(
                f"**5-Day move:** "
                f"{result['ret5']:+.2%}"
            )


            st.write(
                f"**20-Day move:** "
                f"{result['ret20']:+.2%}"
            )


            st.subheader(
                "Why?"
            )


            for reason in result[
                "positives"
            ]:

                st.write(
                    f"✓ {reason}"
                )


            for caution in result[
                "cautions"
            ]:

                st.write(
                    f"⚠ {caution}"
                )


# ============================================================
# EXPLANATION
# ============================================================

with st.expander(
    "What do the scores mean?"
):

    st.markdown(
        """
**Day Trade Score**

- 75–100: strong setup
- 65–74: worth watching closely
- 55–64: modest bullish lean
- 45–54: neutral
- Below 45: weak

**2–5 Day Score**

Same scale, but focused on the next several trading sessions.

**RSI**

- 55–65: healthy upward momentum
- 65–70: strong momentum
- 70+: becoming extended
- 80+: very extended

**Relative Volume**

- 1.0× = normal volume
- 1.5× = 50% above normal
- 2.0× = twice normal volume

A score of 80/100 does **not** mean an 80% probability of making money.
It is a model ranking score.
"""
    )


st.divider()

st.caption(
    "Best used before the market opens and again after the first "
    "15–30 minutes of trading. Market conditions can change quickly."
)
