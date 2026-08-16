import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# =========================================================
# PAGE SETUP
# =========================================================

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
        padding-bottom: 3rem;
        max-width: 1000px;
    }

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.09);
        padding: 12px;
        border-radius: 14px;
    }

    .small-note {
        opacity: 0.72;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Morning Market Scanner")

st.caption(
    "Early-morning stock scanner for TSX, S&P 500 and Nasdaq-100 stocks."
)

st.warning(
    "Signals are model-based research indicators only. "
    "They are not guaranteed buy or sell recommendations."
)


# =========================================================
# STOCK UNIVERSES
# =========================================================

TSX = {
    "RY.TO": "Royal Bank",
    "TD.TO": "TD Bank",
    "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank",
    "CM.TO": "CIBC",
    "NA.TO": "National Bank",

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

    "MFC.TO": "Manulife",
    "SLF.TO": "Sun Life",

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
    "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan",
    "V": "Visa",
    "MA": "Mastercard",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "LLY": "Eli Lilly",
    "AVGO": "Broadcom",
    "WMT": "Walmart",
    "COST": "Costco",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "HD": "Home Depot",
    "BAC": "Bank of America",
    "GS": "Goldman Sachs",
    "CAT": "Caterpillar",
    "GE": "GE Aerospace",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "DIS": "Disney",
    "UBER": "Uber",
    "PLTR": "Palantir",
}


NASDAQ100 = {
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
    "ARM": "Arm Holdings",
}


ALL_NAMES = {}

ALL_NAMES.update(TSX)
ALL_NAMES.update(SP500)
ALL_NAMES.update(NASDAQ100)


# =========================================================
# SECTOR ETF MAPPING
# =========================================================

SECTOR = {
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

    "AAPL": "XLK",
    "MSFT": "XLK",
    "NVDA": "SMH",
    "AMD": "SMH",
    "AVGO": "SMH",
    "QCOM": "SMH",
    "INTC": "SMH",
    "AMAT": "SMH",
    "MU": "SMH",
    "LRCX": "SMH",
    "KLAC": "SMH",
    "MRVL": "SMH",

    "AMZN": "XLY",
    "TSLA": "XLY",
    "HD": "XLY",

    "META": "XLC",
    "GOOGL": "XLC",
    "NFLX": "XLC",
    "DIS": "XLC",

    "JPM": "XLF",
    "BAC": "XLF",
    "GS": "XLF",
    "V": "XLF",
    "MA": "XLF",

    "XOM": "XLE",
    "CVX": "XLE",

    "WMT": "XLP",
    "COST": "XLP",
    "KO": "XLP",
    "PEP": "XLP",
}


# =========================================================
# MARKET INDEX
# =========================================================

def market_index(ticker):

    if ticker.endswith(".TO"):
        return "^GSPTSE"

    if ticker in NASDAQ100:
        return "^IXIC"

    return "^GSPC"


# =========================================================
# DATA
# =========================================================

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

    value = df[column]

    if isinstance(value, pd.DataFrame):
        value = value.iloc[:, 0]

    return pd.to_numeric(
        value,
        errors="coerce"
    )


# =========================================================
# INDICATORS
# =========================================================

def rsi(close, period=14):

    delta = close.diff()

    gains = delta.clip(lower=0).rolling(period).mean()

    losses = (
        -delta.clip(upper=0)
    ).rolling(period).mean()

    rs = gains / losses.replace(
        0,
        np.nan
    )

    return 100 - (
        100 /
        (1 + rs)
    )


def clamp(value, minimum, maximum):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# =========================================================
# RSI INTERPRETATION
# =========================================================

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
        return "Overbought risk"

    return "Very extended"


# =========================================================
# STOCK ANALYSIS
# =========================================================

def analyze_stock(ticker):

    stock = download_data(
        ticker
    )

    if stock.empty:
        return None

    if len(stock) < 70:
        return None


    index_ticker = market_index(
        ticker
    )

    market = download_data(
        index_ticker
    )


    sector_ticker = SECTOR.get(
        ticker,
        "XIU.TO"
        if ticker.endswith(".TO")
        else "SPY"
    )

    sector = download_data(
        sector_ticker
    )


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


    # -----------------------------------------
    # RETURNS
    # -----------------------------------------

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


    # -----------------------------------------
    # MOVING AVERAGES
    # -----------------------------------------

    ma5 = close.rolling(
        5
    ).mean().iloc[-1]

    ma20 = close.rolling(
        20
    ).mean().iloc[-1]

    ma50 = close.rolling(
        50
    ).mean().iloc[-1]


    # -----------------------------------------
    # RSI
    # -----------------------------------------

    rsi_value = rsi(
        close
    ).iloc[-1]


    # -----------------------------------------
    # VOLUME
    # -----------------------------------------

    volume_avg = volume.rolling(
        20
    ).mean().iloc[-1]

    latest_volume = volume.iloc[-1]

    if (
        volume_avg
        and not np.isnan(volume_avg)
    ):

        relative_volume = (
            latest_volume /
            volume_avg
        )

    else:

        relative_volume = 1


    # -----------------------------------------
    # MARKET DIRECTION
    # -----------------------------------------

    market_close = get_series(
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


    # -----------------------------------------
    # SECTOR DIRECTION
    # -----------------------------------------

    sector_close = get_series(
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


    # =====================================================
    # DAY TRADE SCORE
    # =====================================================

    day_score = 50


    day_score += (
        12 *
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
        9 *
        np.tanh(
            sector_move /
            0.015
        )
    )


    ma_short = (
        ma5 /
        ma20
        - 1
    )


    day_score += (
        7 *
        np.tanh(
            ma_short /
            0.025
        )
    )


    # Volume bonus

    if relative_volume >= 2:
        day_score += 6

    elif relative_volume >= 1.5:
        day_score += 4

    elif relative_volume >= 1.2:
        day_score += 2


    # RSI

    if not np.isnan(
        rsi_value
    ):

        if (
            55 <=
            rsi_value <=
            68
        ):
            day_score += 4

        elif (
            rsi_value >
            78
        ):
            day_score -= 6


    day_score = int(
        clamp(
            round(day_score),
            0,
            100
        )
    )


    # =====================================================
    # SWING SCORE
    # =====================================================

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
                ma20
                - 1
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
                ma50
                - 1
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
        45 <=
        rsi_value <=
        68
    ):
        swing_score += 4


    if (
        rsi_value >
        80
    ):
        swing_score -= 7


    swing_score = int(
        clamp(
            round(
                swing_score
            ),
            0,
            100
        )
    )


    # =====================================================
    # SIGNAL
    # =====================================================

    if (
        day_score >= 75
        and
        swing_score >= 70
    ):

        signal = (
            "STRONG SETUP"
        )


    elif (
        day_score >= 65
    ):

        signal = (
            "DAY TRADE WATCH"
        )


    elif (
        swing_score >= 70
    ):

        signal = (
            "SWING BUY CANDIDATE"
        )


    elif (
        day_score >= 58
        or
        swing_score >= 60
    ):

        signal = (
            "WATCH"
        )


    elif (
        day_score <= 40
        and
        swing_score <= 45
    ):

        signal = (
            "AVOID / BEARISH"
        )


    else:

        signal = (
            "NEUTRAL"
        )


    # =====================================================
    # EXPLANATION
    # =====================================================

    reasons = []


    if ret5 > 0.03:

        reasons.append(
            "Strong 5-day momentum"
        )


    if sector_move > 0.005:

        reasons.append(
            "Sector is strong"
        )


    if market_move > 0.005:

        reasons.append(
            "Broad market is positive"
        )


    if relative_volume >= 1.5:

        reasons.append(
            "Above-average volume"
        )


    if (
        55 <=
        rsi_value <=
        68
    ):

        reasons.append(
            "Healthy RSI momentum"
        )


    if (
        ma5 >
        ma20 >
        ma50
    ):

        reasons.append(
            "Strong moving-average trend"
        )


    if not reasons:

        reasons.append(
            "No major confirming signal"
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

        "signal":
            signal,

        "ret1":
            ret1,

        "ret5":
            ret5,

        "ret20":
            ret20,

        "rsi":
            rsi_value,

        "rsi_label":
            rsi_label(
                rsi_value
            ),

        "relative_volume":
            relative_volume,

        "market_move":
            market_move,

        "sector_move":
            sector_move,

        "reasons":
            reasons,

        "rank":
            (
                day_score *
                0.55
                +
                swing_score *
                0.45
            )
    }


# =========================================================
# HOLDINGS AND WATCHLIST
# =========================================================

st.subheader(
    "My Holdings"
)

holdings_text = st.text_input(
    "Stocks you already own",
    value="TRP.TO",
    help=(
        "Example: "
        "TRP.TO, RY.TO, NVDA"
    )
)

holdings = [
    ticker.strip().upper()
    for ticker
    in holdings_text.split(",")
    if ticker.strip()
]


st.subheader(
    "My Watchlist"
)

watchlist_text = st.text_input(
    "Stocks you want to watch",
    value="",
    help=(
        "Example: "
        "CVE.TO, CNQ.TO, NVDA, AAPL"
    )
)

watchlist = [
    ticker.strip().upper()
    for ticker
    in watchlist_text.split(",")
    if ticker.strip()
]


# =========================================================
# TABS
# =========================================================

scanner_tab, stock_tab = st.tabs(
    [
        "Morning Scanner",
        "Analyze One Stock"
    ]
)


# =========================================================
# MORNING SCANNER
# =========================================================

with scanner_tab:

    market_choice = st.selectbox(
        "Market to scan",
        [
            "TSX",
            "S&P 500",
            "Nasdaq-100",
            "All Markets"
        ]
    )


    scan_size = st.selectbox(
        "Number of stocks to scan",
        [
            10,
            20,
            30,
            50
        ],
        index=1
    )


    if st.button(
        "Run Morning Scan",
        type="primary",
        use_container_width=True
    ):

        if (
            market_choice ==
            "TSX"
        ):

            universe = list(
                TSX.keys()
            )


        elif (
            market_choice ==
            "S&P 500"
        ):

            universe = list(
                SP500.keys()
            )


        elif (
            market_choice ==
            "Nasdaq-100"
        ):

            universe = list(
                NASDAQ100.keys()
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
                        NASDAQ100.keys()
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
                len(
                    universe
                )
            )


        progress.empty()

        status.empty()


        if not results:

            st.error(
                "No stocks could be analyzed."
            )


        else:

            df = pd.DataFrame(
                results
            )


            df = df.sort_values(
                "rank",
                ascending=False
            )


            # =================================================
            # HOLDINGS
            # =================================================

            if holdings:

                st.subheader(
                    "My Holdings"
                )


                for ticker in holdings:

                    row = df[
                        df["ticker"]
                        ==
                        ticker
                    ]


                    if row.empty:
                        continue


                    row = row.iloc[0]


                    if (
                        row[
                            "day_score"
                        ]
                        <= 40
                        and
                        row[
                            "swing_score"
                        ]
                        <= 45
                    ):

                        holding_signal = (
                            "SELL / REVIEW"
                        )


                    elif (
                        row[
                            "day_score"
                        ]
                        <= 45
                        or
                        row[
                            "swing_score"
                        ]
                        <= 45
                    ):

                        holding_signal = (
                            "HOLD — CAUTION"
                        )


                    elif (
                        row[
                            "day_score"
                        ]
                        >= 70
                        or
                        row[
                            "swing_score"
                        ]
                        >= 70
                    ):

                        holding_signal = (
                            "HOLD / ADD WATCH"
                        )


                    else:

                        holding_signal = (
                            "HOLD"
                        )


                    st.markdown(
                        f"""
### {ticker} — {holding_signal}

**Day Trade Score:** {row['day_score']}/100  
**2–5 Day Score:** {row['swing_score']}/100  
**Latest Price:** ${row['price']:,.2f}  
**RSI:** {row['rsi']:.0f} — {row['rsi_label']}  
"""
                    )


            # =================================================
            # WATCHLIST
            # =================================================

            if watchlist:

                st.subheader(
                    "My Watchlist"
                )


                for ticker in watchlist:

                    row = df[
                        df["ticker"]
                        ==
                        ticker
                    ]


                    if row.empty:
                        continue


                    row = row.iloc[0]


                    st.markdown(
                        f"""
### {ticker}

**Signal:** {row['signal']}  
**Day Trade Score:** {row['day_score']}/100  
**2–5 Day Score:** {row['swing_score']}/100  
**RSI:** {row['rsi']:.0f} — {row['rsi_label']}
"""
                    )


            # =================================================
            # TOP DAY TRADE SETUPS
            # =================================================

            st.subheader(
                "Top Day Trade Setups"
            )


            day_df = df.sort_values(
                "day_score",
                ascending=False
            ).head(
                10
            )


            display_day = day_df[
                [
                    "ticker",
                    "company",
                    "day_score",
                    "swing_score",
                    "signal",
                    "rsi",
                    "relative_volume"
                ]
            ].copy()


            display_day.columns = [
                "Ticker",
                "Company",
                "Day",
                "2–5 Day",
                "Signal",
                "RSI",
                "Rel Volume"
            ]


            display_day[
                "RSI"
            ] = display_day[
                "RSI"
            ].map(
                lambda x:
                f"{x:.0f}"
            )


            display_day[
                "Rel Volume"
            ] = display_day[
                "Rel Volume"
            ].map(
                lambda x:
                f"{x:.1f}x"
            )


            st.dataframe(
                display_day,
                hide_index=True,
                use_container_width=True
            )


            # =================================================
            # TOP SWING SETUPS
            # =================================================

            st.subheader(
                "Top 2–5 Day Swing Setups"
            )


            swing_df = df.sort_values(
                "swing_score",
                ascending=False
            ).head(
                10
            )


            display_swing = swing_df[
                [
                    "ticker",
                    "company",
                    "swing_score",
                    "day_score",
                    "signal",
                    "rsi",
                    "ret5"
                ]
            ].copy()


            display_swing.columns = [
                "Ticker",
                "Company",
                "2–5 Day",
                "Day",
                "Signal",
                "RSI",
                "5-Day Move"
            ]


            display_swing[
                "RSI"
            ] = display_swing[
                "RSI"
            ].map(
                lambda x:
                f"{x:.0f}"
            )


            display_swing[
                "5-Day Move"
            ] = display_swing[
                "5-Day Move"
            ].map(
                lambda x:
                f"{x:+.1%}"
            )


            st.dataframe(
                display_swing,
                hide_index=True,
                use_container_width=True
            )


            # =================================================
            # BEST CURRENT SETUP
            # =================================================

            best = df.iloc[
                0
            ]


            st.subheader(
                "Best Overall Setup"
            )


            st.header(
                best[
                    "ticker"
                ]
            )


            c1, c2 = st.columns(
                2
            )


            c1.metric(
                "Day Trade Score",
                f"{best['day_score']}/100"
            )


            c2.metric(
                "2–5 Day Score",
                f"{best['swing_score']}/100"
            )


            st.write(
                f"**Signal:** "
                f"{best['signal']}"
            )


            st.write(
                f"**RSI:** "
                f"{best['rsi']:.0f} "
                f"— "
                f"{best['rsi_label']}"
            )


            st.write(
                f"**Relative Volume:** "
                f"{best['relative_volume']:.1f}x"
            )


            st.write(
                "**Why it ranked highly:**"
            )


            for reason in best[
                "reasons"
            ]:

                st.write(
                    f"- {reason}"
                )


# =========================================================
# SINGLE STOCK ANALYSIS
# =========================================================

with stock_tab:

    ticker = st.text_input(
        "Ticker",
        value="NVDA",
        key="single"
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


        if not result:

            st.error(
                "Not enough market data was available."
            )


        else:

            st.header(
                result[
                    "ticker"
                ]
            )


            st.subheader(
                result[
                    "signal"
                ]
            )


            c1, c2 = st.columns(
                2
            )


            c1.metric(
                "Day Trade Score",
                f"{result['day_score']}/100"
            )


            c2.metric(
                "2–5 Day Score",
                f"{result['swing_score']}/100"
            )


            st.metric(
                "Latest Price",
                f"${result['price']:,.2f}"
            )


            st.write(
                f"**RSI:** "
                f"{result['rsi']:.0f} "
                f"— "
                f"{result['rsi_label']}"
            )


            st.write(
                f"**Relative Volume:** "
                f"{result['relative_volume']:.1f}x"
            )


            st.write(
                f"**1-Day Move:** "
                f"{result['ret1']:+.2%}"
            )


            st.write(
                f"**5-Day Move:** "
                f"{result['ret5']:+.2%}"
            )


            st.write(
                f"**20-Day Move:** "
                f"{result['ret20']:+.2%}"
            )


            st.write(
                f"**Market Direction:** "
                f"{result['market_move']:+.2%}"
            )


            st.write(
                f"**Sector Direction:** "
                f"{result['sector_move']:+.2%}"
            )


            st.subheader(
                "Why"
            )


            for reason in result[
                "reasons"
            ]:

                st.write(
                    f"- {reason}"
                )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Best used before the market opens and again shortly after the open. "
    "Scores are screening indicators, not guaranteed predictions. "
    "Free market data may be delayed."
)
