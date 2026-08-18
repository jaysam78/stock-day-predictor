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
st.set_page_config(page_title="Live Market Trader", page_icon="📈", layout="centered")
st.title("Live Market Trader")
st.caption("Market scanner • EOD forecast • Market Context • 2–5 day setups • prediction tracker")
st.warning(
    "Signals, forecasts and trade levels are research estimates. "
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
    start = current.replace(hour=9, minute=30, second=0, microsecond=0)
    end = current.replace(hour=16, minute=0, second=0, microsecond=0)
    return float(np.clip((current - start).total_seconds() / (end - start).total_seconds(), 0.0, 1.0))


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
    "ZSP": "BMO S&P 500 Index ETF",
    "QQC": "Invesco NASDAQ 100 Index ETF",
    "ZAG": "BMO Aggregate Bond Index ETF",
    "VAB": "Vanguard Canadian Aggregate Bond Index ETF",
}

TSX = {
    "RY.TO": "Royal Bank", "TD.TO": "TD Bank", "BMO.TO": "Bank of Montreal",
    "BNS.TO": "Scotiabank", "CM.TO": "CIBC", "NA.TO": "National Bank",
    "MFC.TO": "Manulife", "SLF.TO": "Sun Life", "GWO.TO": "Great-West Lifeco",
    "POW.TO": "Power Corporation", "IFC.TO": "Intact Financial", "FFH.TO": "Fairfax Financial",
    "BAM.TO": "Brookfield Asset Management", "BN.TO": "Brookfield Corporation",
    "CNQ.TO": "Canadian Natural Resources", "SU.TO": "Suncor", "CVE.TO": "Cenovus",
    "IMO.TO": "Imperial Oil", "MEG.TO": "MEG Energy", "ARX.TO": "ARC Resources",
    "TOU.TO": "Tourmaline Oil", "WCP.TO": "Whitecap Resources", "PEY.TO": "Peyto Exploration",
    "ENB.TO": "Enbridge", "TRP.TO": "TC Energy", "PPL.TO": "Pembina Pipeline", "KEY.TO": "Keyera",
    "AEM.TO": "Agnico Eagle", "ABX.TO": "Barrick Mining", "WPM.TO": "Wheaton Precious Metals",
    "K.TO": "Kinross Gold", "FNV.TO": "Franco-Nevada", "LUG.TO": "Lundin Gold",
    "NTR.TO": "Nutrien", "TECK-B.TO": "Teck Resources", "FM.TO": "First Quantum Minerals",
    "HBM.TO": "Hudbay Minerals", "CCO.TO": "Cameco", "IVN.TO": "Ivanhoe Mines",
    "ERO.TO": "Ero Copper", "LUN.TO": "Lundin Mining", "AGI.TO": "Alamos Gold",
    "SHOP.TO": "Shopify", "CSU.TO": "Constellation Software", "OTEX.TO": "OpenText",
    "KXS.TO": "Kinaxis", "DSG.TO": "Descartes Systems", "DCBO.TO": "Docebo", "CLS.TO": "Celestica",
    "CNR.TO": "Canadian National Railway", "CP.TO": "CPKC", "WSP.TO": "WSP Global",
    "TFII.TO": "TFI International", "CAE.TO": "CAE", "ATS.TO": "ATS Corporation",
    "TIH.TO": "Toromont Industries", "STN.TO": "Stantec", "GFL.TO": "GFL Environmental",
    "CCL-B.TO": "CCL Industries", "ATD.TO": "Couche-Tard", "L.TO": "Loblaw",
    "MRU.TO": "Metro", "DOL.TO": "Dollarama", "CTC-A.TO": "Canadian Tire",
    "QSR.TO": "Restaurant Brands", "MG.TO": "Magna International", "GIL.TO": "Gildan Activewear",
    "WN.TO": "George Weston", "ATZ.TO": "Aritzia", "FTS.TO": "Fortis", "EMA.TO": "Emera",
    "AQN.TO": "Algonquin Power", "CPX.TO": "Capital Power", "CU.TO": "Canadian Utilities",
    "NPI.TO": "Northland Power", "BEPC.TO": "Brookfield Renewable", "BCE.TO": "BCE",
    "T.TO": "TELUS", "RCI-B.TO": "Rogers Communications", "QBR-B.TO": "Quebecor",
    "CAR-UN.TO": "Canadian Apartment REIT", "REI-UN.TO": "RioCan REIT",
    "SRU-UN.TO": "SmartCentres REIT", "DIR-UN.TO": "Dream Industrial REIT", "GRT-UN.TO": "Granite REIT",
}

SP500 = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon", "META": "Meta",
    "GOOGL": "Alphabet", "AVGO": "Broadcom", "JPM": "JPMorgan", "BAC": "Bank of America",
    "GS": "Goldman Sachs", "V": "Visa", "MA": "Mastercard", "XOM": "Exxon Mobil", "CVX": "Chevron",
    "LLY": "Eli Lilly", "UNH": "UnitedHealth", "WMT": "Walmart", "COST": "Costco", "HD": "Home Depot",
    "NFLX": "Netflix", "AMD": "AMD", "CRM": "Salesforce", "ORCL": "Oracle", "DIS": "Disney",
    "UBER": "Uber", "PLTR": "Palantir", "GE": "GE Aerospace", "CAT": "Caterpillar", "DE": "Deere",
    "BA": "Boeing", "KO": "Coca-Cola", "PEP": "PepsiCo", "ABBV": "AbbVie", "MRK": "Merck",
    "PFE": "Pfizer", "NOW": "ServiceNow", "IBM": "IBM", "INTU": "Intuit", "PYPL": "PayPal",
}

NASDAQ = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon", "META": "Meta",
    "GOOGL": "Alphabet", "AVGO": "Broadcom", "TSLA": "Tesla", "COST": "Costco", "NFLX": "Netflix",
    "AMD": "AMD", "ADBE": "Adobe", "INTC": "Intel", "QCOM": "Qualcomm", "AMAT": "Applied Materials",
    "MU": "Micron", "PANW": "Palo Alto Networks", "CRWD": "CrowdStrike", "CSCO": "Cisco",
    "MRVL": "Marvell", "LRCX": "Lam Research", "KLAC": "KLA", "MSTR": "Strategy", "ARM": "Arm Holdings",
    "SMCI": "Super Micro Computer", "APP": "AppLovin", "FTNT": "Fortinet", "MELI": "MercadoLibre",
    "BKNG": "Booking Holdings", "ABNB": "Airbnb", "DDOG": "Datadog", "ZS": "Zscaler",
    "MDB": "MongoDB", "SNPS": "Synopsys", "CDNS": "Cadence Design Systems",
}

ALL_NAMES = {}
ALL_NAMES.update(TSX)
ALL_NAMES.update(SP500)
ALL_NAMES.update(NASDAQ)
for symbol, name in CANADIAN_ETFS.items():
    ALL_NAMES[f"{symbol}.TO"] = name


# ============================================================
# SECTOR / COMMODITY MAPS
# ============================================================
CANADA_FINANCIALS = {"RY.TO", "TD.TO", "BMO.TO", "BNS.TO", "CM.TO", "NA.TO", "MFC.TO", "SLF.TO", "GWO.TO", "POW.TO", "IFC.TO", "FFH.TO", "BAM.TO", "BN.TO"}
CANADA_ENERGY = {"CNQ.TO", "SU.TO", "CVE.TO", "IMO.TO", "MEG.TO", "ARX.TO", "TOU.TO", "WCP.TO", "PEY.TO", "ENB.TO", "TRP.TO", "PPL.TO", "KEY.TO"}
CANADA_GOLD = {"AEM.TO", "ABX.TO", "WPM.TO", "K.TO", "FNV.TO", "LUG.TO", "AGI.TO"}
CANADA_METALS = {"TECK-B.TO", "FM.TO", "HBM.TO", "IVN.TO", "ERO.TO", "LUN.TO"}
CANADA_TECH = {"SHOP.TO", "CSU.TO", "OTEX.TO", "KXS.TO", "DSG.TO", "DCBO.TO", "CLS.TO"}
CANADA_UTILITIES = {"FTS.TO", "EMA.TO", "AQN.TO", "CPX.TO", "CU.TO", "NPI.TO", "BEPC.TO"}
CANADA_REAL_ESTATE = {"CAR-UN.TO", "REI-UN.TO", "SRU-UN.TO", "DIR-UN.TO", "GRT-UN.TO"}
CANADA_CONSUMER = {"ATD.TO", "L.TO", "MRU.TO", "DOL.TO", "CTC-A.TO", "QSR.TO", "MG.TO", "GIL.TO", "WN.TO", "ATZ.TO"}
CANADA_INDUSTRIAL = {"CNR.TO", "CP.TO", "WSP.TO", "TFII.TO", "CAE.TO", "ATS.TO", "TIH.TO", "STN.TO", "GFL.TO", "CCL-B.TO"}
US_TECH = {"AAPL", "MSFT", "NVDA", "META", "GOOGL", "AVGO", "AMD", "CRM", "ORCL", "ADBE", "INTC", "QCOM", "AMAT", "MU", "PANW", "CRWD", "CSCO", "MRVL", "LRCX", "KLAC", "SMCI", "APP", "FTNT", "DDOG", "ZS", "MDB", "SNPS", "CDNS", "NOW", "IBM", "INTU"}
US_ENERGY = {"XOM", "CVX"}
US_FINANCIALS = {"JPM", "BAC", "GS", "V", "MA", "PYPL"}
US_HEALTHCARE = {"LLY", "UNH", "ABBV", "MRK", "PFE"}
US_INDUSTRIALS = {"GE", "CAT", "DE", "BA"}
US_CONSUMER = {"AMZN", "TSLA", "WMT", "COST", "HD", "NFLX", "DIS", "ABNB", "BKNG", "MELI", "KO", "PEP"}


def normalize_ticker(raw):
    ticker = raw.strip().upper()
    if not ticker:
        return ""
    if ticker.endswith(".TO"):
        return ticker
    if ticker in CANADIAN_ETFS or f"{ticker}.TO" in TSX:
        return f"{ticker}.TO"
    return ticker


def is_canadian_etf(ticker):
    return ticker.replace(".TO", "") in CANADIAN_ETFS


def market_index(ticker):
    if ticker.endswith(".TO"):
        return "^GSPTSE"
    if ticker in NASDAQ:
        return "^IXIC"
    return "^GSPC"


def sector_context_for_ticker(ticker):
    if ticker in CANADA_FINANCIALS: return "Canadian Financials", "XFN.TO"
    if ticker in CANADA_ENERGY: return "Canadian Energy", "XEG.TO"
    if ticker in CANADA_GOLD: return "Gold Miners", "XGD.TO"
    if ticker in CANADA_METALS: return "Materials / Metals", "XMA.TO"
    if ticker in CANADA_TECH: return "Canadian Technology", "XIT.TO"
    if ticker in CANADA_UTILITIES: return "Canadian Utilities", "XUT.TO"
    if ticker in CANADA_REAL_ESTATE: return "Canadian Real Estate", "XRE.TO"
    if ticker in CANADA_CONSUMER: return "Canadian Consumer", "XST.TO"
    if ticker in CANADA_INDUSTRIAL: return "Canadian Industrials", "XGI.TO"
    if ticker in US_TECH: return "U.S. Technology", "XLK"
    if ticker in US_ENERGY: return "U.S. Energy", "XLE"
    if ticker in US_FINANCIALS: return "U.S. Financials", "XLF"
    if ticker in US_HEALTHCARE: return "U.S. Healthcare", "XLV"
    if ticker in US_INDUSTRIALS: return "U.S. Industrials", "XLI"
    if ticker in US_CONSUMER: return "U.S. Consumer", "XLY"
    return "Broad Market", market_index(ticker)


def commodity_context_for_ticker(ticker):
    if ticker in CANADA_ENERGY or ticker in US_ENERGY:
        if ticker in {"TOU.TO", "ARX.TO", "PEY.TO"}:
            return "Natural Gas", "NG=F"
        return "Crude Oil", "CL=F"
    if ticker in CANADA_GOLD:
        return "Gold", "GC=F"
    if ticker in CANADA_METALS:
        return "Copper", "HG=F"
    return None, None


# ============================================================
# MARKET DATA
# ============================================================
@st.cache_data(ttl=600)
def daily_data(ticker, period="1y"):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def intraday_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="5m", auto_adjust=False, prepost=True, progress=False, threads=False)
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
    return pd.to_numeric(result, errors="coerce")


def latest_move(ticker):
    data = daily_data(ticker, "1mo")
    close = get_series(data, "Close").dropna()
    return float(close.iloc[-1] / close.iloc[-2] - 1) if len(close) >= 2 else 0.0


def latest_level(ticker):
    data = daily_data(ticker, "1mo")
    close = get_series(data, "Close").dropna()
    return float(close.iloc[-1]) if len(close) else None


def price_info(ticker):
    intra = intraday_data(ticker)
    daily = daily_data(ticker, "1mo")
    daily_close = get_series(daily, "Close").dropna()
    previous_close = float(daily_close.iloc[-1]) if len(daily_close) else None
    if not intra.empty:
        intra_close = get_series(intra, "Close").dropna()
        if len(intra_close):
            label = "Premarket" if SESSION == "PREMARKET" else "Live / latest available" if SESSION == "REGULAR" else "After-hours" if SESSION == "AFTERHOURS" else "Latest available"
            return float(intra_close.iloc[-1]), label, previous_close
    return previous_close, "Previous Close", previous_close


# ============================================================
# INDICATORS
# ============================================================
def calculate_rsi(close, period=14):
    change = close.diff()
    gains = change.clip(lower=0).rolling(period).mean()
    losses = (-change.clip(upper=0)).rolling(period).mean()
    rs = gains / losses.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def calculate_atr(df, period=14):
    high, low, close = get_series(df, "High"), get_series(df, "Low"), get_series(df, "Close")
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calculate_vwap(ticker):
    data = intraday_data(ticker)
    if data.empty:
        return None
    high, low, close, volume = (get_series(data, c) for c in ["High", "Low", "Close", "Volume"])
    cumulative_volume = volume.cumsum()
    if len(close) == 0 or len(cumulative_volume) == 0 or cumulative_volume.iloc[-1] <= 0:
        return None
    typical_price = (high + low + close) / 3
    return float(((typical_price * volume).cumsum() / cumulative_volume).iloc[-1])


# ============================================================
# EARNINGS / EVENT RISK
# ============================================================
@st.cache_data(ttl=21600)
def next_earnings_date(ticker):
    if is_canadian_etf(ticker):
        return None
    try:
        earnings = yf.Ticker(ticker).get_earnings_dates(limit=6)
        if earnings is None or earnings.empty:
            return None
        today = now_et().date()
        for value in earnings.index:
            d = pd.Timestamp(value).date()
            if d >= today:
                return d
    except Exception:
        return None
    return None


def event_risk_from_date(earnings_date):
    if earnings_date is None:
        return "NONE KNOWN"
    days = (earnings_date - now_et().date()).days
    if days <= 1:
        return "HIGH"
    if days <= 7:
        return "MEDIUM"
    return "LOW"


# ============================================================
# MARKET CONTEXT
# ============================================================
def calculate_market_regime(market_move, vix_level, vix_move):
    if vix_level is None:
        return "BULLISH" if market_move >= 0.005 else "BEARISH" if market_move <= -0.005 else "NEUTRAL"
    if vix_level >= 30 or vix_move >= 0.10:
        return "RISK-OFF"
    if market_move > 0 and vix_level < 20 and vix_move <= 0:
        return "BULLISH / RISK-ON"
    if market_move < 0 and (vix_level >= 22 or vix_move > 0.04):
        return "BEARISH"
    if vix_level >= 25:
        return "VOLATILE"
    return "NEUTRAL"


def get_market_context(ticker, include_event=False):
    market_symbol = market_index(ticker)
    market_move = latest_move(market_symbol)
    vix_level = latest_level("^VIX")
    vix_move = latest_move("^VIX")
    market_regime = calculate_market_regime(market_move, vix_level, vix_move)
    sector_name, sector_symbol = sector_context_for_ticker(ticker)
    sector_move = latest_move(sector_symbol) if sector_symbol else 0.0
    sector_relative_strength = sector_move - market_move
    commodity_name, commodity_symbol = commodity_context_for_ticker(ticker)
    commodity_move = latest_move(commodity_symbol) if commodity_symbol else None
    earnings_date = next_earnings_date(ticker) if include_event else None
    event_risk = event_risk_from_date(earnings_date) if include_event else "NOT CHECKED"
    return {
        "market_symbol": market_symbol,
        "market_move": float(market_move),
        "market_regime": market_regime,
        "vix_level": vix_level,
        "vix_move": float(vix_move),
        "sector_name": sector_name,
        "sector_symbol": sector_symbol,
        "sector_move": float(sector_move),
        "sector_relative_strength": float(sector_relative_strength),
        "commodity_name": commodity_name,
        "commodity_symbol": commodity_symbol,
        "commodity_move": float(commodity_move) if commodity_move is not None else None,
        "earnings_date": earnings_date,
        "event_risk": event_risk,
    }


def ensure_event_context(result):
    if result.get("event_risk") != "NOT CHECKED":
        return result
    earnings_date = next_earnings_date(result["ticker"])
    result["earnings_date"] = earnings_date
    result["event_risk"] = event_risk_from_date(earnings_date)
    return result


# ============================================================
# EOD FORECAST
# ============================================================
def make_eod_forecast(current, previous_close, close, atr_value, rsi_value, market_move, day_score, quality_score, vwap):
    if previous_close is None or previous_close <= 0:
        previous_close = current
    ret1 = float(close.pct_change(1).iloc[-1])
    ret3 = float(close.pct_change(3).iloc[-1])
    ret5 = float(close.pct_change(5).iloc[-1])
    current_move = current / previous_close - 1
    daily_vol = close.pct_change().tail(20).std()
    if pd.isna(daily_vol):
        daily_vol = 0.015
    atr_pct = atr_value / current if current > 0 else 0.02
    momentum = 0.30 * ret1 + 0.20 * (ret3 / 3) + 0.15 * (ret5 / 5) + 0.20 * market_move
    rsi_bias = (rsi_value - 50) / 50 * 0.0035
    vwap_bias = 0.0
    if vwap is not None and vwap > 0:
        vwap_bias = float(np.clip((current / vwap - 1) * 0.15, -0.004, 0.004))
    base_expected = float(np.clip(momentum + rsi_bias + vwap_bias, -max(0.005, atr_pct * 1.25), max(0.005, atr_pct * 1.25)))
    elapsed = regular_session_fraction()
    if SESSION == "REGULAR":
        expected_return = elapsed * current_move + (1 - elapsed) * base_expected
    elif SESSION == "PREMARKET":
        expected_return = 0.20 * current_move + 0.80 * base_expected
    else:
        expected_return = base_expected
    predicted_close = previous_close * (1 + expected_return)
    movement_cap = max(atr_value * 1.50, current * 0.01)
    predicted_close = float(np.clip(predicted_close, current - movement_cap, current + movement_cap))
    remaining = max(0.10, 1 - elapsed) if SESSION == "REGULAR" else 1.0
    uncertainty = max(atr_value * (0.30 + 0.55 * remaining), current * daily_vol * 0.35)
    low = max(0.01, predicted_close - uncertainty)
    high = predicted_close + uncertainty
    confidence = 50 + 20 * abs(day_score - 50) / 50 + 12 * quality_score / 100
    if SESSION == "REGULAR":
        confidence += elapsed * 6
    confidence = int(np.clip(round(confidence), 50, 85))
    predicted_move = predicted_close / current - 1
    direction = "UP" if predicted_move > 0.001 else "DOWN" if predicted_move < -0.001 else "FLAT"
    return {
        "eod_predicted_close": float(predicted_close),
        "eod_range_low": float(low),
        "eod_range_high": float(high),
        "eod_confidence": confidence,
        "eod_predicted_move": float(predicted_move),
        "eod_direction": direction,
    }


def entry_status(result):
    current, low, high, stop = result["current"], result["entry_low"], result["entry_high"], result["stop"]
    if current <= stop * 1.02:
        return "NEAR STOP — HIGH RISK"
    if current < low:
        return "BELOW BUY ZONE"
    if low <= current <= high:
        return "INSIDE BUY ZONE"
    return "ABOVE BUY ZONE — DON'T CHASE"


def setup_quality(result):
    score = 0.35 * result["day"] + 0.30 * result["swing"] + 0.35 * result["quality"]
    if result["rr1"] < 1.5: score -= 8
    if result["rsi"] >= 75: score -= 7
    return "STRONG" if score >= 78 else "GOOD" if score >= 68 else "MIXED" if score >= 55 else "WEAK"


def context_alignment(result):
    score = 50
    regime = result.get("market_regime")
    if regime == "BULLISH / RISK-ON": score += 12
    elif regime == "BULLISH": score += 7
    elif regime in {"BEARISH", "RISK-OFF"}: score -= 12
    elif regime == "VOLATILE": score -= 5
    rel = result.get("sector_relative_strength", 0.0)
    if rel >= 0.01: score += 12
    elif rel >= 0.003: score += 6
    elif rel <= -0.01: score -= 12
    elif rel <= -0.003: score -= 6
    commodity = result.get("commodity_move")
    if commodity is not None:
        if commodity >= 0.01: score += 7
        elif commodity <= -0.01: score -= 7
    if result.get("event_risk") == "HIGH": score -= 15
    elif result.get("event_risk") == "MEDIUM": score -= 6
    return float(np.clip(score, 0, 100))


def calculate_today_rank(result):
    score = result["day"] * 0.29 + result["quality"] * 0.21 + result["eod_confidence"] * 0.10 + result["swing"] * 0.07 + context_alignment(result) * 0.13
    score += float(np.clip(result["eod_predicted_move"] / 0.02, -1, 1)) * 10
    status = entry_status(result)
    score += 9 if status == "INSIDE BUY ZONE" else 2 if status == "BELOW BUY ZONE" else -8 if status == "ABOVE BUY ZONE — DON'T CHASE" else -12
    score += 6 if result["rr1"] >= 2.0 else 3 if result["rr1"] >= 1.5 else -8
    score += 7 if result["relative_volume"] >= 1.5 else 4 if result["relative_volume"] >= 1.2 else -4 if result["relative_volume"] < 0.70 else 0
    if SESSION == "REGULAR" and result["vwap"] is not None:
        score += 6 if result["current"] >= result["vwap"] else -6
    if 50 <= result["rsi"] <= 68: score += 4
    elif result["rsi"] >= 78: score -= 10
    elif result["rsi"] >= 72: score -= 5
    return float(np.clip(score, 0, 100))


def calculate_swing_rank(result):
    score = result["swing"] * 0.38 + result["quality"] * 0.22 + result["day"] * 0.12 + result["eod_confidence"] * 0.07 + context_alignment(result) * 0.12
    score += 6 if result["rr1"] >= 2.0 else 3 if result["rr1"] >= 1.5 else -6
    if result["rsi"] >= 80: score -= 8
    elif 50 <= result["rsi"] <= 70: score += 3
    if result["relative_volume"] >= 1.2: score += 3
    return float(np.clip(score, 0, 100))


# ============================================================
# MAIN ANALYSIS
# ============================================================
def analyze(raw_ticker, include_event=False):
    ticker = normalize_ticker(raw_ticker)
    data = daily_data(ticker)
    if data.empty:
        return None
    close, volume, high, low = (get_series(data, c) for c in ["Close", "Volume", "High", "Low"])
    if len(close) < 70:
        return None
    current, price_label, previous_close = price_info(ticker)
    if current is None:
        return None

    ret1, ret3, ret5, ret20 = close.pct_change(1).iloc[-1], close.pct_change(3).iloc[-1], close.pct_change(5).iloc[-1], close.pct_change(20).iloc[-1]
    ma5, ma20, ma50 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(50).mean().iloc[-1]
    rsi_value = calculate_rsi(close).iloc[-1]
    avg_volume = volume.rolling(20).mean().iloc[-1]
    relative_volume = float(volume.iloc[-1] / avg_volume) if avg_volume and not pd.isna(avg_volume) else 1.0
    context = get_market_context(ticker, include_event=include_event)
    market_move = context["market_move"]

    day = 50 + 11*np.tanh(ret1/0.015) + 8*np.tanh(ret3/0.025) + 7*np.tanh(market_move/0.012) + 8*np.tanh(((ma5/ma20)-1)/0.025)
    if relative_volume >= 1.5: day += 5
    elif relative_volume >= 1.2: day += 3
    if 55 <= rsi_value <= 68: day += 4
    if rsi_value >= 80: day -= 8
    elif rsi_value >= 73: day -= 4
    if is_canadian_etf(ticker): day = 50 + (day - 50) * 0.80
    day = int(np.clip(round(day), 0, 100))

    swing = 50 + 8*np.tanh(ret3/0.025) + 11*np.tanh(ret5/0.04) + 10*np.tanh(ret20/0.09) + 8*np.tanh(((ma5/ma20)-1)/0.03) + 8*np.tanh(((ma20/ma50)-1)/0.05)
    if 50 <= rsi_value <= 68: swing += 4
    if rsi_value >= 80: swing -= 8
    if is_canadian_etf(ticker): swing = 50 + (swing - 50) * 0.85
    swing = int(np.clip(round(swing), 0, 100))

    quality = 50
    if 50 <= rsi_value <= 68: quality += 12
    elif rsi_value >= 80: quality -= 18
    if relative_volume >= 1.5: quality += 8
    elif relative_volume >= 1.2: quality += 4
    if ma5 > ma20 > ma50: quality += 10
    vwap = calculate_vwap(ticker)
    if vwap is not None and SESSION == "REGULAR": quality += 10 if current >= vwap else -10
    quality = int(np.clip(round(quality), 0, 100))

    atr_values = calculate_atr(data)
    atr_value = float(atr_values.iloc[-1]) if len(atr_values) and not pd.isna(atr_values.iloc[-1]) else current * 0.02
    support = max(float(low.tail(10).min()), current - 1.5 * atr_value)
    resistance = float(high.tail(10).max())
    if is_canadian_etf(ticker):
        entry_low, entry_high = current - 0.30*atr_value, current + 0.08*atr_value
        stop = min(support - 0.15*atr_value, entry_low - 0.75*atr_value)
    else:
        entry_low, entry_high = current - 0.45*atr_value, current + 0.10*atr_value
        stop = min(support - 0.20*atr_value, entry_low - 0.85*atr_value)
    entry_mid = (entry_low + entry_high) / 2
    risk = max(entry_mid - stop, 0.01)
    target1 = max(resistance, entry_mid + 1.5*risk)
    target2 = max(resistance + atr_value, entry_mid + 2.2*risk)
    rr1, rr2 = (target1-entry_mid)/risk, (target2-entry_mid)/risk

    if rsi_value >= 80:
        action, prediction = "DON'T CHASE", "UP" if day >= 55 else "NEUTRAL"
    elif rsi_value >= 70 and not is_canadian_etf(ticker):
        action, prediction = "WAIT FOR PULLBACK", "UP" if day >= 55 else "NEUTRAL"
    elif rr1 < 1.5:
        action, prediction = "WAIT — POOR RISK/REWARD", "UP" if day >= 55 else "NEUTRAL"
    elif day >= 75 and quality >= 70:
        action, prediction = "BUY SETUP / ENTRY FAVOURABLE", "UP"
    elif day >= 65 or swing >= 70:
        action, prediction = "WATCH FOR ENTRY", "UP"
    elif day <= 40 and swing <= 45:
        action, prediction = "AVOID / SELL REVIEW", "DOWN"
    else:
        action, prediction = "NO CLEAR ENTRY", "NEUTRAL"

    eod = make_eod_forecast(current, previous_close, close, atr_value, rsi_value, market_move, day, quality, vwap)
    result = {
        "ticker": ticker, "name": ALL_NAMES.get(ticker, ticker), "current": float(current), "price_label": price_label,
        "previous_close": previous_close, "day": day, "swing": swing, "quality": quality, "prediction": prediction,
        "action": action, "rsi": float(rsi_value), "relative_volume": relative_volume, "vwap": vwap, "atr": atr_value,
        "entry_low": float(entry_low), "entry_high": float(entry_high), "stop": float(stop), "target1": float(target1),
        "target2": float(target2), "rr1": float(rr1), "rr2": float(rr2),
    }
    result.update(context)
    result.update(eod)
    result["context_score"] = context_alignment(result)
    result["today_rank"] = calculate_today_rank(result)
    result["swing_rank"] = calculate_swing_rank(result)
    return result


# ============================================================
# INSIGHTS
# ============================================================
def build_insights(result):
    items = []
    if result["day"] >= 70: items.append("Short-term momentum is supportive.")
    elif result["day"] <= 45: items.append("Short-term momentum is weak.")
    if result["swing"] >= 75: items.append("The 2–5 day swing setup is strong.")
    if 50 <= result["rsi"] <= 68: items.append("RSI is in a healthy momentum range.")
    elif result["rsi"] >= 75: items.append("RSI is elevated, so chase risk is higher.")
    if SESSION == "REGULAR" and result["vwap"] is not None:
        items.append("Price is above VWAP, supporting the intraday setup." if result["current"] >= result["vwap"] else "Price is below VWAP, weakening the intraday setup.")
    if result["relative_volume"] >= 1.5: items.append("Volume is materially above normal, adding confirmation.")
    elif result["relative_volume"] < 0.8: items.append("Volume confirmation is currently weak.")
    if result["sector_relative_strength"] >= 0.005: items.append(f"{result['sector_name']} is outperforming the broader market.")
    elif result["sector_relative_strength"] <= -0.005: items.append(f"{result['sector_name']} is underperforming the broader market.")
    if result["commodity_move"] is not None:
        if result["commodity_move"] >= 0.01: items.append(f"{result['commodity_name']} is rising and supports this sector.")
        elif result["commodity_move"] <= -0.01: items.append(f"{result['commodity_name']} is falling and is a headwind.")
    if result["event_risk"] == "HIGH": items.append("Major event risk is high because earnings are very close.")
    elif result["event_risk"] == "MEDIUM": items.append("Earnings are approaching, which adds event risk.")
    status = entry_status(result)
    if status == "INSIDE BUY ZONE": items.append("Current price is inside the preferred entry zone.")
    elif status == "ABOVE BUY ZONE — DON'T CHASE": items.append("Price is above the preferred entry zone.")
    if result["eod_predicted_move"] > 0.005: items.append("The EOD model still sees meaningful upside from the current price.")
    elif result["eod_predicted_move"] < -0.005: items.append("The EOD model currently expects downside into the close.")
    else: items.append("The EOD model sees limited remaining same-day movement.")
    return items


# ============================================================
# SESSION STATE
# ============================================================
for key, default in {"analysis_result": None, "scanner_results": [], "my_stock_results": [], "predictions": []}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# SUPABASE
# ============================================================
def get_database():
    if create_client is None:
        return None
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None


DATABASE = get_database()
PERSISTENT_STORAGE = DATABASE is not None


def prediction_trade_date():
    current = now_et()
    if current.weekday() < 5 and current.time() <= time(16, 0):
        return current.date()
    next_date = current.date() + timedelta(days=1)
    while next_date.weekday() >= 5:
        next_date += timedelta(days=1)
    return next_date


def fetch_predictions():
    if PERSISTENT_STORAGE:
        try:
            return DATABASE.table("prediction_tracker").select("*").order("tracked_at", desc=True).execute().data or []
        except Exception as error:
            st.error(f"Could not load tracker: {error}")
            return []
    return list(st.session_state.predictions)


def fetch_snapshots(prediction_id):
    if not PERSISTENT_STORAGE:
        return []
    try:
        return DATABASE.table("forecast_snapshots").select("*").eq("prediction_id", prediction_id).order("snapshot_at", desc=False).execute().data or []
    except Exception:
        return []


def already_tracked(ticker, trade_date):
    return any(row.get("ticker") == ticker and str(row.get("trade_date")) == str(trade_date) for row in fetch_predictions())


def save_snapshot(prediction_id, result, trade_date):
    if not PERSISTENT_STORAGE:
        return False
    row = {
        "prediction_id": prediction_id, "ticker": result["ticker"], "trade_date": str(trade_date), "snapshot_at": now_et().isoformat(),
        "current_price": result["current"], "predicted_close": result["eod_predicted_close"],
        "predicted_range_low": result["eod_range_low"], "predicted_range_high": result["eod_range_high"],
        "confidence": result["eod_confidence"], "predicted_move": result["eod_predicted_move"],
        "day_score": result["day"], "swing_score": result["swing"], "quality_score": result["quality"],
        "rsi": result["rsi"], "relative_volume": result["relative_volume"], "vwap": result["vwap"],
        "market_regime": result["market_regime"], "market_move": result["market_move"], "vix_level": result["vix_level"],
        "vix_move": result["vix_move"], "sector_symbol": result["sector_symbol"], "sector_move": result["sector_move"],
        "sector_relative_strength": result["sector_relative_strength"], "commodity_symbol": result["commodity_symbol"],
        "commodity_move": result["commodity_move"], "earnings_date": str(result["earnings_date"]) if result.get("earnings_date") else None,
        "event_risk": result["event_risk"],
    }
    try:
        DATABASE.table("forecast_snapshots").insert(row).execute()
        return True
    except Exception as error:
        st.error(f"Could not save forecast snapshot: {error}")
        return False


def save_prediction(result):
    result = ensure_event_context(result)
    trade_date = prediction_trade_date()
    if already_tracked(result["ticker"], trade_date):
        return "duplicate"
    row = {
        "ticker": result["ticker"], "tracked_at": now_et().isoformat(), "trade_date": trade_date.isoformat(),
        "prediction": result["prediction"], "action": result["action"], "day_score": result["day"], "swing_score": result["swing"],
        "quality_score": result["quality"], "start_price": result["current"], "entry_low": result["entry_low"],
        "entry_high": result["entry_high"], "stop_price": result["stop"], "target1": result["target1"], "target2": result["target2"],
        "eod_predicted_close": result["eod_predicted_close"], "eod_range_low": result["eod_range_low"],
        "eod_range_high": result["eod_range_high"], "eod_confidence": result["eod_confidence"],
        "eod_predicted_move": result["eod_predicted_move"], "latest_eod_predicted_close": result["eod_predicted_close"],
        "latest_eod_range_low": result["eod_range_low"], "latest_eod_range_high": result["eod_range_high"],
        "latest_eod_confidence": result["eod_confidence"], "latest_eod_predicted_move": result["eod_predicted_move"],
        "latest_forecast_at": now_et().isoformat(), "saved_market_regime": result["market_regime"],
        "saved_vix_level": result["vix_level"], "saved_sector_symbol": result["sector_symbol"],
        "saved_sector_move": result["sector_move"], "saved_sector_relative_strength": result["sector_relative_strength"],
        "saved_commodity_symbol": result["commodity_symbol"], "saved_commodity_move": result["commodity_move"],
        "saved_earnings_date": str(result["earnings_date"]) if result.get("earnings_date") else None,
        "saved_event_risk": result["event_risk"], "close_price": None, "day_high": None, "day_low": None,
        "direction_correct": None, "stop_hit": None, "target1_hit": None, "target2_hit": None,
        "eod_error_abs": None, "eod_error_pct": None, "eod_range_hit": None, "result_status": "OPEN",
    }
    if PERSISTENT_STORAGE:
        try:
            response = DATABASE.table("prediction_tracker").insert(row).execute()
            inserted = response.data or []
            if inserted and inserted[0].get("id") is not None:
                save_snapshot(inserted[0]["id"], result, trade_date)
            return "persistent"
        except Exception as error:
            st.error(f"Database save failed: {error}")
            return "error"
    row["id"] = max([x.get("id", 0) for x in st.session_state.predictions] or [0]) + 1
    st.session_state.predictions.append(row)
    return "temporary"


def update_prediction(row_id, values):
    if PERSISTENT_STORAGE:
        try:
            DATABASE.table("prediction_tracker").update(values).eq("id", row_id).execute()
            return True
        except Exception as error:
            st.error(f"Could not update database: {error}")
            return False
    for row in st.session_state.predictions:
        if row.get("id") == row_id:
            row.update(values)
    return True


def refresh_latest_forecast(row):
    if row.get("result_status") == "CLOSED":
        return False
    latest = analyze(row["ticker"], include_event=True)
    if latest is None:
        return False
    values = {
        "latest_eod_predicted_close": latest["eod_predicted_close"], "latest_eod_range_low": latest["eod_range_low"],
        "latest_eod_range_high": latest["eod_range_high"], "latest_eod_confidence": latest["eod_confidence"],
        "latest_eod_predicted_move": latest["eod_predicted_move"], "latest_forecast_at": now_et().isoformat(),
    }
    ok = update_prediction(row["id"], values)
    if ok:
        save_snapshot(row["id"], latest, row["trade_date"])
    return ok


def remove_prediction(row_id):
    if PERSISTENT_STORAGE:
        try:
            DATABASE.table("forecast_snapshots").delete().eq("prediction_id", row_id).execute()
            DATABASE.table("prediction_tracker").delete().eq("id", row_id).execute()
            return True
        except Exception as error:
            st.error(f"Could not remove prediction: {error}")
            return False
    st.session_state.predictions = [row for row in st.session_state.predictions if row.get("id") != row_id]
    return True


def clear_all_predictions():
    if PERSISTENT_STORAGE:
        try:
            DATABASE.table("forecast_snapshots").delete().neq("id", 0).execute()
            DATABASE.table("prediction_tracker").delete().neq("id", 0).execute()
            return True
        except Exception as error:
            st.error(f"Could not clear predictions: {error}")
            return False
    st.session_state.predictions = []
    return True


def settle_prediction(row):
    if row.get("result_status") == "CLOSED":
        return row
    data = daily_data(row["ticker"], "3mo")
    if data.empty:
        return row
    target_date = pd.to_datetime(row["trade_date"]).date()
    dates = pd.to_datetime(data.index).date
    positions = [i for i, d in enumerate(dates) if d >= target_date]
    if not positions:
        return row
    pos = positions[0]
    actual_date = dates[pos]
    if actual_date == now_et().date() and SESSION in ["PREMARKET", "REGULAR"]:
        return row
    daily_row = data.iloc[pos]
    def scalar(column):
        value = daily_row[column]
        return float(value.iloc[0]) if isinstance(value, pd.Series) else float(value)
    close_price, day_high, day_low = scalar("Close"), scalar("High"), scalar("Low")
    start_price = float(row["start_price"])
    prediction = row["prediction"]
    direction_correct = close_price > start_price if prediction == "UP" else close_price < start_price if prediction == "DOWN" else None
    original_predicted_close = row.get("eod_predicted_close")
    eod_error_abs = abs(close_price - float(original_predicted_close)) if original_predicted_close is not None else None
    eod_error_pct = eod_error_abs / close_price if eod_error_abs is not None else None
    range_low, range_high = row.get("eod_range_low"), row.get("eod_range_high")
    eod_range_hit = float(range_low) <= close_price <= float(range_high) if range_low is not None and range_high is not None else None
    values = {
        "close_price": close_price, "day_high": day_high, "day_low": day_low, "direction_correct": direction_correct,
        "stop_hit": day_low <= float(row["stop_price"]), "target1_hit": day_high >= float(row["target1"]),
        "target2_hit": day_high >= float(row["target2"]), "eod_error_abs": eod_error_abs,
        "eod_error_pct": eod_error_pct, "eod_range_hit": eod_range_hit, "result_status": "CLOSED",
    }
    update_prediction(row["id"], values)
    row.update(values)
    return row


# ============================================================
# DISPLAY HELPERS
# ============================================================
def confidence_label(score):
    return "LOW" if score < 60 else "MODERATE" if score < 70 else "HIGH" if score < 80 else "VERY HIGH"


def colored_change(value, suffix=""):
    color = "#16a34a" if value > 0 else "#dc2626" if value < 0 else "#6b7280"
    return f"<span style='color:{color};font-weight:700;'>{value:+.2f}{suffix}</span>"


def show_market_context(result):
    result = ensure_event_context(result)
    result["context_score"] = context_alignment(result)
    st.subheader("Market Context")
    c1, c2 = st.columns(2)
    c1.metric("Market Regime", result["market_regime"])
    c2.metric("Context Score", f"{result['context_score']:.0f}/100")
    if result["vix_level"] is not None:
        st.write(f"VIX: **{result['vix_level']:.2f}** ({result['vix_move']:+.2%})")
    st.write(f"Broad market: **{result['market_move']:+.2%}**")
    st.write(f"Sector: **{result['sector_name']}**")
    st.write(f"Sector move: **{result['sector_move']:+.2%}**")
    rel = result["sector_relative_strength"]
    word = "OUTPERFORMING" if rel > 0 else "UNDERPERFORMING" if rel < 0 else "IN LINE"
    st.write(f"Sector vs market: **{word} ({rel:+.2%})**")
    if result["commodity_symbol"] is not None:
        st.write(f"{result['commodity_name']}: **{result['commodity_move']:+.2%}**")
    if result["event_risk"] == "HIGH": st.error("Event Risk: HIGH — earnings are very close.")
    elif result["event_risk"] == "MEDIUM": st.warning("Event Risk: MEDIUM — earnings are approaching.")
    else: st.write(f"Event Risk: **{result['event_risk']}**")
    if result.get("earnings_date") is not None:
        st.caption(f"Next earnings date found: {result['earnings_date']}")


def show_eod_forecast(result):
    st.subheader("End-of-Day Forecast")
    c1, c2 = st.columns(2)
    c1.metric("Predicted close", f"${result['eod_predicted_close']:.2f}", f"{result['eod_predicted_move']:+.2%}")
    c2.metric("Model Confidence", f"{result['eod_confidence']}%")
    st.caption(f"Confidence level: {confidence_label(result['eod_confidence'])}")
    st.write(f"Expected direction: **{result['eod_direction']}**")
    st.write(f"Likely closing range: **${result['eod_range_low']:.2f} – ${result['eod_range_high']:.2f}**")


def show_insights(result):
    st.subheader("Prediction Insights")
    c1, c2 = st.columns(2)
    c1.metric("Setup Quality", setup_quality(result))
    c2.metric("Entry Status", entry_status(result))
    st.write(f"Best Today score: **{result['today_rank']:.0f}/100**")
    st.write(f"2–5 Day score: **{result['swing_rank']:.0f}/100**")
    st.write(f"Market Context score: **{result['context_score']:.0f}/100**")
    with st.expander("Why the model sees it this way"):
        for item in build_insights(result):
            st.write(f"• {item}")


def show_trade(result):
    result = ensure_event_context(result)
    result["context_score"] = context_alignment(result)
    result["today_rank"] = calculate_today_rank(result)
    result["swing_rank"] = calculate_swing_rank(result)
    st.subheader(result["action"])
    st.metric("CURRENT PRICE", f"${result['current']:.2f}")
    st.caption(f"Price source: {result['price_label']}")
    show_eod_forecast(result)
    show_market_context(result)
    show_insights(result)
    st.divider()
    st.markdown(
        f"### BUY ZONE — preferred entry area\n**${result['entry_low']:.2f} – ${result['entry_high']:.2f}**\n\n"
        f"### STOP / EXIT — risk level\n**${result['stop']:.2f}**\n\n"
        f"### TARGET 1 — 2–5 day swing objective\n**${result['target1']:.2f}**\n\n"
        f"### TARGET 2 — extended swing objective\n**${result['target2']:.2f}**"
    )
    st.write(f"Day / Swing / Quality: **{result['day']} / {result['swing']} / {result['quality']}**")
    st.write(f"RSI: **{result['rsi']:.0f}**")
    st.write(f"Relative Volume: **{result['relative_volume']:.2f}×**")
    if result["vwap"] is not None:
        st.write(f"VWAP: **${result['vwap']:.2f}**")
    st.write(f"Risk / Reward to T1: **1:{result['rr1']:.1f}**")


def track_button(result, key):
    trade_date = prediction_trade_date()
    if already_tracked(result["ticker"], trade_date):
        st.success(f"Tracked ✓ for {trade_date}")
        return
    if st.button("📌 Track this prediction", key=key, use_container_width=True):
        mode = save_prediction(result)
        if mode == "persistent": st.success("Forecast and Market Context saved permanently.")
        elif mode == "temporary": st.success("Forecast saved for this session.")
        elif mode == "duplicate": st.info("Already tracked.")


# ============================================================
# HOLDINGS / WATCHLIST
# ============================================================
try:
    saved_holdings = st.query_params.get("holdings", "TRP.TO")
    saved_watchlist = st.query_params.get("watchlist", "")
except Exception:
    saved_holdings, saved_watchlist = "TRP.TO", ""

st.subheader("My Holdings")
holdings_text = st.text_input("Stocks / ETFs you own", value=saved_holdings)
st.subheader("⭐ My Watchlist")
watchlist_text = st.text_input("Stocks / ETFs you want to watch", value=saved_watchlist)
holdings = [normalize_ticker(x) for x in holdings_text.split(",") if x.strip()]
watchlist = [normalize_ticker(x) for x in watchlist_text.split(",") if x.strip()]
if st.button("💾 Save My Stocks", use_container_width=True):
    st.query_params["holdings"] = ",".join(holdings)
    st.query_params["watchlist"] = ",".join(watchlist)
    st.success("Saved.")


# ============================================================
# TABS
# ============================================================
scan_tab, my_tab, analyze_tab, tracker_tab = st.tabs(["Scanner", "⭐ My Stocks", "Analyze", "📊 Prediction Tracker"])

with scan_tab:
    market_choice = st.selectbox("Market", ["TSX", "S&P 500", "Nasdaq", "Canadian ETFs", "All Markets"])
    results_to_show = st.selectbox("Number of results to show", [5, 10, 15, 20], index=1)
    st.caption("The app scans the full built-in universe first, then ranks the best setups.")
    if st.button("🔎 Scan Market Now", type="primary", use_container_width=True):
        if market_choice == "TSX": universe = list(TSX.keys())
        elif market_choice == "S&P 500": universe = list(SP500.keys())
        elif market_choice == "Nasdaq": universe = list(NASDAQ.keys())
        elif market_choice == "Canadian ETFs": universe = [f"{x}.TO" for x in CANADIAN_ETFS]
        else: universe = list(dict.fromkeys(list(TSX) + list(SP500) + list(NASDAQ) + [f"{x}.TO" for x in CANADIAN_ETFS]))
        results, total = [], len(universe)
        progress, status = st.progress(0), st.empty()
        for i, ticker in enumerate(universe):
            status.write(f"Scanning {ticker} ({i+1}/{total})...")
            r = analyze(ticker, include_event=False)
            if r is not None: results.append(r)
            progress.progress((i+1)/total)
        progress.empty(); status.empty(); st.session_state.scanner_results = results

    results = st.session_state.scanner_results
    if results:
        st.success(f"Analyzed {len(results)} usable securities.")
        today_results = sorted(results, key=lambda x: x["today_rank"], reverse=True)
        st.subheader("🔥 Best Today")
        st.caption("Ranks the current session using technicals, VWAP, volume, EOD forecast, entry location, risk/reward and Market Context.")
        for rank, result in enumerate(today_results[:results_to_show], start=1):
            with st.expander(f"#{rank} {result['ticker']} — {result['today_rank']:.0f}/100 — {result['action']}"):
                st.write(f"**{result['name']}**"); show_trade(result); track_button(result, f"today_{rank}_{result['ticker']}")
        swing_results = sorted(results, key=lambda x: x["swing_rank"], reverse=True)
        st.subheader("📈 Best 2–5 Day Setups")
        for rank, result in enumerate(swing_results[:results_to_show], start=1):
            with st.expander(f"#{rank} {result['ticker']} — {result['swing_rank']:.0f}/100 — {result['action']}"):
                st.write(f"**{result['name']}**"); show_trade(result); track_button(result, f"swing_{rank}_{result['ticker']}")

with my_tab:
    personal = list(dict.fromkeys(holdings + watchlist))
    if st.button("Refresh My Stocks", use_container_width=True):
        refreshed = []
        for ticker in personal:
            r = analyze(ticker, include_event=True)
            if r: refreshed.append(r)
        st.session_state.my_stock_results = refreshed
    for i, result in enumerate(st.session_state.my_stock_results):
        st.header(result["ticker"])
        st.caption("OWNED" if result["ticker"] in holdings else "WATCHLIST")
        show_trade(result); track_button(result, f"my_track_{i}"); st.divider()

with analyze_tab:
    raw_ticker = st.text_input("Enter ticker", value="CVE")
    ticker = normalize_ticker(raw_ticker)
    if ticker != raw_ticker.strip().upper(): st.caption(f"Using ticker: **{ticker}**")
    if st.button("Analyze", use_container_width=True):
        result = analyze(ticker, include_event=True)
        if result is None:
            st.session_state.analysis_result = None; st.error("No usable market data was found.")
        else:
            st.session_state.analysis_result = result
    result = st.session_state.analysis_result
    if result is not None:
        st.header(result["ticker"]); st.write(result["name"]); show_trade(result); track_button(result, "single_track")

with tracker_tab:
    st.subheader("Prediction Tracker")
    if PERSISTENT_STORAGE:
        st.success("Persistent storage connected.")
    else:
        st.warning("Temporary storage only.")
    rows = fetch_predictions()
    st.metric("Tracked Predictions", len(rows))
    open_rows = [r for r in rows if r.get("result_status") != "CLOSED"]
    if open_rows and st.button("🔄 Refresh Latest Forecasts", type="primary", use_container_width=True):
        refreshed = 0
        for row in open_rows:
            if refresh_latest_forecast(row): refreshed += 1
        st.success(f"Updated {refreshed} latest forecast(s). Original forecasts were not changed.")
        rows = fetch_predictions()
    if st.button("✅ Update End-of-Day Results", use_container_width=True):
        updated = 0
        for row in rows:
            before = row.get("result_status")
            after = settle_prediction(row)
            if before != "CLOSED" and after.get("result_status") == "CLOSED": updated += 1
        st.success(f"Closed {updated} prediction(s).")
        rows = fetch_predictions()
    if rows and st.button("🧹 Clear All Tracked Predictions", use_container_width=True):
        if clear_all_predictions(): st.success("All predictions removed."); st.rerun()

    closed = [r for r in rows if r.get("result_status") == "CLOSED"]
    if closed:
        scored = [r for r in closed if r.get("direction_correct") is not None]
        accuracy = sum(1 for r in scored if r.get("direction_correct") is True) / len(scored) if scored else None
        errors = [float(r["eod_error_pct"]) for r in closed if r.get("eod_error_pct") is not None]
        ranges = [r for r in closed if r.get("eod_range_hit") is not None]
        c1, c2 = st.columns(2)
        c1.metric("Direction accuracy", f"{accuracy:.1%}" if accuracy is not None else "—")
        c2.metric("Avg forecast error", f"{np.mean(errors):.2%}" if errors else "—")
        if len(closed) < 20: st.info(f"Only {len(closed)} completed forecast(s). Treat the statistics as preliminary.")

    if not rows:
        st.info("No tracked predictions yet.")

    for i, row in enumerate(rows):
        icon = "✅" if row.get("direction_correct") is True else "❌" if row.get("direction_correct") is False else "⏳"
        with st.expander(f"{icon} {row['ticker']} — {row['trade_date']} — {row.get('result_status', 'OPEN')}"):
            st.write(f"Start price: **${float(row['start_price']):.2f}**")
            st.write(f"Original signal: **{row['action']}**")
            st.subheader("Original Saved Forecast")
            original_close, original_conf = row.get("eod_predicted_close"), row.get("eod_confidence")
            if original_close is not None: st.write(f"Predicted close: **${float(original_close):.2f}**")
            if original_conf is not None: st.write(f"Confidence: **{int(original_conf)}% ({confidence_label(int(original_conf))})**")
            st.subheader("Saved Market Context")
            st.write(f"Market regime: **{row.get('saved_market_regime') or '—'}**")
            if row.get("saved_vix_level") is not None: st.write(f"VIX: **{float(row['saved_vix_level']):.2f}**")
            if row.get("saved_sector_move") is not None: st.write(f"Sector move: **{float(row['saved_sector_move']):+.2%}**")
            st.write(f"Event risk: **{row.get('saved_event_risk') or '—'}**")
            st.subheader("Latest Forecast")
            latest_close, latest_conf = row.get("latest_eod_predicted_close"), row.get("latest_eod_confidence")
            if latest_close is not None: st.write(f"Latest predicted close: **${float(latest_close):.2f}**")
            if latest_conf is not None: st.write(f"Latest confidence: **{int(latest_conf)}% ({confidence_label(int(latest_conf))})**")
            if original_close is not None and latest_close is not None:
                st.markdown("Change in model forecast: " + colored_change(float(latest_close)-float(original_close)), unsafe_allow_html=True)
            if original_conf is not None and latest_conf is not None:
                st.markdown("Confidence change: " + colored_change(int(latest_conf)-int(original_conf), " pts"), unsafe_allow_html=True)
            if row.get("id") is not None:
                snapshots = fetch_snapshots(row["id"])
                if snapshots:
                    with st.expander(f"Forecast history ({len(snapshots)} snapshots)"):
                        snap_df = pd.DataFrame(snapshots)
                        cols = [c for c in ["snapshot_at", "current_price", "predicted_close", "confidence", "predicted_move", "day_score", "swing_score", "quality_score", "market_regime", "vix_level", "sector_move", "sector_relative_strength", "commodity_move", "event_risk"] if c in snap_df.columns]
                        st.dataframe(snap_df[cols], use_container_width=True, hide_index=True)
            st.divider()
            st.write(f"Buy zone: **${float(row['entry_low']):.2f} – ${float(row['entry_high']):.2f}**")
            st.write(f"Stop: **${float(row['stop_price']):.2f}**")
            st.write(f"Target 1: **${float(row['target1']):.2f}**")
            st.write(f"Target 2: **${float(row['target2']):.2f}**")
            if row.get("result_status") == "CLOSED":
                st.subheader("Actual Result")
                st.write(f"Actual close: **${float(row['close_price']):.2f}**")
                if row.get("eod_error_pct") is not None: st.write(f"Original forecast error: **{float(row['eod_error_pct']):.2%}**")
                if row.get("direction_correct") is True: st.success("Direction prediction: CORRECT")
                elif row.get("direction_correct") is False: st.error("Direction prediction: WRONG")
                if row.get("eod_range_hit") is True: st.success("Actual close landed inside the predicted range.")
                elif row.get("eod_range_hit") is False: st.error("Actual close finished outside the predicted range.")
            if row.get("id") is not None and st.button(f"🗑 Remove {row['ticker']}", key=f"remove_{row['id']}_{i}", use_container_width=True):
                if remove_prediction(row["id"]): st.success(f"{row['ticker']} removed."); st.rerun()


# ============================================================
# GUIDE
# ============================================================
st.divider()
st.subheader("How to Read This App")
with st.expander("Model Confidence — what does the % mean?"):
    st.markdown("""
Model Confidence is a **signal-strength score**, not a guaranteed probability.

- **50–59% — Low**
- **60–69% — Moderate**
- **70–79% — High**
- **80–85% — Very High**

A displayed 75% does **not** mean there is exactly a 75% chance the forecast will happen.
""")
with st.expander("Best Today vs Best 2–5 Day"):
    st.markdown("""
**Best Today** emphasizes Day Score, VWAP, volume, EOD upside, entry location, risk/reward and Market Context.

**Best 2–5 Day** emphasizes Swing Score, trend quality, risk/reward, sector support and Market Context.
""")
with st.expander("Market Context"):
    st.markdown("""
Market Context currently considers broad market direction, VIX, sector direction, sector relative strength, relevant commodity movement, and earnings/event risk.
""")
with st.expander("EOD Forecast vs Targets"):
    st.markdown("""
**EOD Predicted Close** is the model's estimate for the current session close.

**Target 1** is a broader 2–5 day swing objective.

**Target 2** is a more aggressive extended swing objective.
""")
with st.expander("RSI / VWAP / Relative Volume"):
    st.markdown("""
**RSI:** 50–68 is a healthy momentum area; 75+ increases chase risk.

**VWAP:** above VWAP is generally supportive intraday; below VWAP is weaker.

**Relative Volume:** around 1.0× is normal, 1.2×+ is stronger confirmation, 1.5×+ is strong confirmation.
""")

st.divider()
st.caption(f"Page refreshed: {now_et().strftime('%I:%M:%S %p ET')} • Session: {SESSION_LABEL}")
