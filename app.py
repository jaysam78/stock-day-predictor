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
    "Market scanner • EOD forecast • Market Context • "
    "2–5 day setups • prediction tracker"
)

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
# TSX UNIVERSE
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
    "GWO.TO": "Great-West Lifeco",
    "POW.TO": "Power Corporation",
    "IFC.TO": "Intact Financial",
    "FFH.TO": "Fairfax Financial",
    "BAM.TO": "Brookfield Asset Management",
    "BN.TO": "Brookfield Corporation",

    "CNQ.TO": "Canadian Natural Resources",
    "SU.TO": "Suncor",
    "CVE.TO": "Cenovus",
    "IMO.TO": "Imperial Oil",
    "MEG.TO": "MEG Energy",
    "ARX.TO": "ARC Resources",
    "TOU.TO": "Tourmaline Oil",
    "WCP.TO": "Whitecap Resources",
    "PEY.TO": "Peyto Exploration",
    "ENB.TO": "Enbridge",
    "TRP.TO": "TC Energy",
    "PPL.TO": "Pembina Pipeline",
    "KEY.TO": "Keyera",

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

    "SHOP.TO": "Shopify",
    "CSU.TO": "Constellation Software",
    "OTEX.TO": "OpenText",
    "KXS.TO": "Kinaxis",
    "DSG.TO": "Descartes Systems",
    "DCBO.TO": "Docebo",
    "CLS.TO": "Celestica",

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

    "ATD.TO": "Couche-Tard",
    "L.TO": "Loblaw",
    "MRU.TO": "Metro",
    "DOL.TO": "Dollarama",
    "CTC-A.TO": "Canadian Tire",
    "QSR.TO": "Restaurant Brands",
    "MG.TO": "Magna International",
    "GIL.TO": "Gildan Activewear",
    "WN.TO": "George Weston",
    "ATZ.TO": "Aritzia",

    "FTS.TO": "Fortis",
    "EMA.TO": "Emera",
    "AQN.TO": "Algonquin Power",
    "CPX.TO": "Capital Power",
    "CU.TO": "Canadian Utilities",
    "NPI.TO": "Northland Power",
    "BEPC.TO": "Brookfield Renewable",

    "BCE.TO": "BCE",
    "T.TO": "TELUS",
    "RCI-B.TO": "Rogers Communications",
    "QBR-B.TO": "Quebecor",

    "CAR-UN.TO": "Canadian Apartment REIT",
    "REI-UN.TO": "RioCan REIT",
    "SRU-UN.TO": "SmartCentres REIT",
    "DIR-UN.TO": "Dream Industrial REIT",
    "GRT-UN.TO": "Granite REIT",
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
# SECTOR GROUPS
# ============================================================

CANADA_FINANCIALS = {
    "RY.TO", "TD.TO", "BMO.TO", "BNS.TO", "CM.TO", "NA.TO",
    "MFC.TO", "SLF.TO", "GWO.TO", "POW.TO", "IFC.TO",
    "FFH.TO", "BAM.TO", "BN.TO",
}

CANADA_ENERGY = {
    "CNQ.TO", "SU.TO", "CVE.TO", "IMO.TO", "MEG.TO",
    "ARX.TO", "TOU.TO", "WCP.TO", "PEY.TO",
    "ENB.TO", "TRP.TO", "PPL.TO", "KEY.TO",
}

CANADA_GOLD = {
    "AEM.TO", "ABX.TO", "WPM.TO", "K.TO",
    "FNV.TO", "LUG.TO", "AGI.TO",
}

CANADA_METALS = {
    "TECK-B.TO", "FM.TO", "HBM.TO", "IVN.TO",
    "ERO.TO", "LUN.TO",
}

CANADA_TECH = {
    "SHOP.TO", "CSU.TO", "OTEX.TO", "KXS.TO",
    "DSG.TO", "DCBO.TO", "CLS.TO",
}

CANADA_UTILITIES = {
    "FTS.TO", "EMA.TO", "AQN.TO", "CPX.TO",
    "CU.TO", "NPI.TO", "BEPC.TO",
}

CANADA_REAL_ESTATE = {
    "CAR-UN.TO", "REI-UN.TO", "SRU-UN.TO",
    "DIR-UN.TO", "GRT-UN.TO",
}

CANADA_CONSUMER = {
    "ATD.TO", "L.TO", "MRU.TO", "DOL.TO", "CTC-A.TO",
    "QSR.TO", "MG.TO", "GIL.TO", "WN.TO", "ATZ.TO",
}

CANADA_INDUSTRIAL = {
    "CNR.TO", "CP.TO", "WSP.TO", "TFII.TO",
    "CAE.TO", "ATS.TO", "TIH.TO", "STN.TO",
    "GFL.TO", "CCL-B.TO",
}

US_TECH = {
    "AAPL", "MSFT", "NVDA", "META", "GOOGL", "AVGO",
    "AMD", "CRM", "ORCL", "ADBE", "INTC", "QCOM",
    "AMAT", "MU", "PANW", "CRWD", "CSCO", "MRVL",
    "LRCX", "KLAC", "SMCI", "APP", "FTNT",
    "DDOG", "ZS", "MDB", "SNPS", "CDNS", "NOW",
    "IBM", "INTU",
}

US_ENERGY = {
    "XOM", "CVX",
}

US_FINANCIALS = {
    "JPM", "BAC", "GS", "V", "MA", "PYPL",
}

US_HEALTHCARE = {
    "LLY", "UNH", "ABBV", "MRK", "PFE",
}

US_INDUSTRIALS = {
    "GE", "CAT", "DE", "BA",
}

US_CONSUMER = {
    "AMZN", "TSLA", "WMT", "COST", "HD",
    "NFLX", "DIS", "ABNB", "BKNG", "MELI",
    "KO", "PEP",
}


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


def sector_context_for_ticker(ticker):
    if ticker in CANADA_FINANCIALS:
        return "Canadian Financials", "XFN.TO"

    if ticker in CANADA_ENERGY:
        return "Canadian Energy", "XEG.TO"

    if ticker in CANADA_GOLD:
        return "Gold Miners", "XGD.TO"

    if ticker in CANADA_METALS:
        return "Materials / Metals", "XMA.TO"

    if ticker in CANADA_TECH:
        return "Canadian Technology", "XIT.TO"

    if ticker in CANADA_UTILITIES:
        return "Canadian Utilities", "XUT.TO"

    if ticker in CANADA_REAL_ESTATE:
        return "Canadian Real Estate", "XRE.TO"

    if ticker in CANADA_CONSUMER:
        return "Canadian Consumer", "XST.TO"

    if ticker in CANADA_INDUSTRIAL:
        return "Canadian Industrials", "XGI.TO"

    if ticker in US_TECH:
        return "U.S. Technology", "XLK"

    if ticker in US_ENERGY:
        return "U.S. Energy", "XLE"

    if ticker in US_FINANCIALS:
        return "U.S. Financials", "XLF"

    if ticker in US_HEALTHCARE:
        return "U.S. Healthcare", "XLV"

    if ticker in US_INDUSTRIALS:
        return "U.S. Industrials", "XLI"

    if ticker in US_CONSUMER:
        return "U.S. Consumer", "XLY"

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


def pct_distance(current, level):
    if current is None or level is None or current == 0:
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
def daily_data(ticker, period="
