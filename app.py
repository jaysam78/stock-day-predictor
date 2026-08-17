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

st.set_page_config(page_title="Live Market Trader", page_icon="📈", layout="centered")
st.title("Live Market Trader")
st.caption("Scanner • trade plan • holdings/watchlist • prediction scorecard")
st.warning("Model scores and trade levels are research signals, not guaranteed outcomes or personalized investment advice.")

ET = ZoneInfo("America/Toronto")
def now_et(): return datetime.now(ET)
def session_mode():
    n = now_et()
    if n.weekday() >= 5: return "WEEKEND", "Market closed"
    if n.time() < time(9,30): return "PREMARKET", "Premarket"
    if n.time() <= time(16,0): return "REGULAR", "Live"
    return "AFTERHOURS", "After-hours"
SESSION, SESSION_LABEL = session_mode()

CANADIAN_ETFS = {
    "XEQT":"iShares Core Equity ETF Portfolio","XGRO":"iShares Core Growth ETF Portfolio",
    "XBAL":"iShares Core Balanced ETF Portfolio","VEQT":"Vanguard All-Equity ETF Portfolio",
    "VGRO":"Vanguard Growth ETF Portfolio","VBAL":"Vanguard Balanced ETF Portfolio",
    "VFV":"Vanguard S&P 500 Index ETF","XQQ":"iShares NASDAQ 100 Index ETF",
    "VCN":"Vanguard FTSE Canada All Cap Index ETF","XIU":"iShares S&P/TSX 60 Index ETF",
    "ZAG":"BMO Aggregate Bond Index ETF","VAB":"Vanguard Canadian Aggregate Bond Index ETF"
}
TSX = {"RY.TO":"Royal Bank","TD.TO":"TD Bank","BMO.TO":"Bank of Montreal","BNS.TO":"Scotiabank","CM.TO":"CIBC","NA.TO":"National Bank","MFC.TO":"Manulife","SLF.TO":"Sun Life","CNQ.TO":"Canadian Natural","SU.TO":"Suncor","CVE.TO":"Cenovus","IMO.TO":"Imperial Oil","TRP.TO":"TC Energy","ENB.TO":"Enbridge","SHOP.TO":"Shopify","CSU.TO":"Constellation Software","OTEX.TO":"OpenText","CNR.TO":"CN Rail","CP.TO":"CPKC","ABX.TO":"Barrick Mining","AEM.TO":"Agnico Eagle","WPM.TO":"Wheaton Precious Metals","NTR.TO":"Nutrien","TECK-B.TO":"Teck Resources","FTS.TO":"Fortis","EMA.TO":"Emera","BCE.TO":"BCE","T.TO":"TELUS","ATD.TO":"Couche-Tard","L.TO":"Loblaw"}
SP500 = {"AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","META":"Meta","GOOGL":"Alphabet","AVGO":"Broadcom","JPM":"JPMorgan","BAC":"Bank of America","GS":"Goldman Sachs","V":"Visa","MA":"Mastercard","XOM":"Exxon Mobil","CVX":"Chevron","LLY":"Eli Lilly","WMT":"Walmart","COST":"Costco","HD":"Home Depot","NFLX":"Netflix","AMD":"AMD","CRM":"Salesforce","ORCL":"Oracle","DIS":"Disney","UBER":"Uber","PLTR":"Palantir"}
NASDAQ = {"AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","META":"Meta","GOOGL":"Alphabet","AVGO":"Broadcom","TSLA":"Tesla","COST":"Costco","NFLX":"Netflix","AMD":"AMD","ADBE":"Adobe","INTC":"Intel","QCOM":"Qualcomm","AMAT":"Applied Materials","MU":"Micron","PANW":"Palo Alto Networks","CRWD":"CrowdStrike","CSCO":"Cisco","MRVL":"Marvell","LRCX":"Lam Research","KLAC":"KLA","MSTR":"Strategy","ARM":"Arm Holdings"}
ALL_NAMES = {}; ALL_NAMES.update(TSX); ALL_NAMES.update(SP500); ALL_NAMES.update(NASDAQ)
for t,n in CANADIAN_ETFS.items(): ALL_NAMES[t+".TO"] = n

def normalize_ticker(raw):
    t = raw.strip().upper()
    if not t: return ""
    if t.endswith(".TO"): return t
    if t in CANADIAN_ETFS or t+".TO" in TSX: return t+".TO"
    return t

def is_canadian_etf(t): return t.replace(".TO","") in CANADIAN_ETFS

def market_index(t):
    if t.endswith(".TO"): return "^GSPTSE"
    if t in NASDAQ: return "^IXIC"
    return "^GSPC"

@st.cache_data(ttl=600)
def daily_data(ticker, period="1y"):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=60)
def intraday_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="5m", auto_adjust=False, prepost=True, progress=False, threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception: return pd.DataFrame()

def s(df,col):
    if df is None or df.empty or col not in df.columns: return pd.Series(dtype=float)
    x=df[col]
    if isinstance(x,pd.DataFrame): x=x.iloc[:,0]
    return pd.to_numeric(x,errors="coerce")

def rsi(c,n=14):
    d=c.diff(); g=d.clip(lower=0).rolling(n).mean(); l=(-d.clip(upper=0)).rolling(n).mean(); rs=g/l.replace(0,np.nan)
    return 100-100/(1+rs)

def atr(df,n=14):
    h,l,c=s(df,"High"),s(df,"Low"),s(df,"Close"); pc=c.shift(1)
    tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

def latest_move(t):
    d=daily_data(t,"1mo"); c=s(d,"Close").dropna()
    return float(c.iloc[-1]/c.iloc[-2]-1) if len(c)>=2 else 0.0

def price_info(t):
    intra=intraday_data(t); d=daily_data(t,"1mo"); dc=s(d,"Close").dropna(); prev=float(dc.iloc[-1]) if len(dc) else None
    if not intra.empty:
        ic=s(intra,"Close").dropna()
        if len(ic):
            label="Premarket" if SESSION=="PREMARKET" else "Live / latest available" if SESSION=="REGULAR" else "After-hours" if SESSION=="AFTERHOURS" else "Latest available"
            return float(ic.iloc[-1]),label,prev
    return prev,"Previous Close",prev

def calc_vwap(t):
    d=intraday_data(t)
    if d.empty: return None
    h,l,c,v=s(d,"High"),s(d,"Low"),s(d,"Close"),s(d,"Volume")
    cv=v.cumsum()
    if len(c)==0 or len(cv)==0 or cv.iloc[-1]<=0: return None
    return float((((h+l+c)/3*v).cumsum()/cv).iloc[-1])

def analyze(raw):
    t=normalize_ticker(raw); d=daily_data(t)
    if d.empty: return None
    c,v,h,l=s(d,"Close"),s(d,"Volume"),s(d,"High"),s(d,"Low")
    if len(c)<70: return None
    current,label,prev=price_info(t)
    if current is None: return None
    ret1,ret3,ret5,ret20=c.pct_change(1).iloc[-1],c.pct_change(3).iloc[-1],c.pct_change(5).iloc[-1],c.pct_change(20).iloc[-1]
    ma5,ma20,ma50=c.rolling(5).mean().iloc[-1],c.rolling(20).mean().iloc[-1],c.rolling(50).mean().iloc[-1]
    rv=rsi(c).iloc[-1]
    av=v.rolling(20).mean().iloc[-1]; rel=float(v.iloc[-1]/av) if av and not pd.isna(av) else 1.0
    mkt=latest_move(market_index(t))
    sector="XIU.TO" if t.endswith(".TO") else "SPY"; sec=latest_move(sector)
    day=50+11*np.tanh(ret1/.015)+8*np.tanh(ret3/.025)+7*np.tanh(mkt/.012)+8*np.tanh(sec/.015)+8*np.tanh(((ma5/ma20)-1)/.025)
    if rel>=1.5: day+=5
    elif rel>=1.2: day+=3
    if 55<=rv<=68: day+=4
    if rv>=80: day-=8
    elif rv>=73: day-=4
    if is_canadian_etf(t): day=50+(day-50)*.8
    day=int(max(0,min(100,round(day))))
    swing=50+8*np.tanh(ret3/.025)+11*np.tanh(ret5/.04)+10*np.tanh(ret20/.09)+8*np.tanh(((ma5/ma20)-1)/.03)+8*np.tanh(((ma20/ma50)-1)/.05)+6*np.tanh(sec/.015)
    if 50<=rv<=68: swing+=4
    if rv>=80: swing-=8
    if is_canadian_etf(t): swing=50+(swing-50)*.85
    swing=int(max(0,min(100,round(swing))))
    quality=50+(12 if 50<=rv<=68 else -18 if rv>=80 else 0)+(8 if rel>=1.5 else 4 if rel>=1.2 else 0)+(10 if ma5>ma20>ma50 else 0)
    vwap=calc_vwap(t)
    if vwap is not None and SESSION=="REGULAR": quality += 10 if current>=vwap else -10
    quality=int(max(0,min(100,round(quality))))
    a=atr(d); avtr=float(a.iloc[-1]) if len(a) and not pd.isna(a.iloc[-1]) else current*.02
    support=max(float(l.tail(10).min()),current-1.5*avtr); resistance=float(h.tail(10).max())
    if is_canadian_etf(t): entry_low=current-.30*avtr; entry_high=current+.08*avtr; stop=min(support-.15*avtr,entry_low-.75*avtr)
    else: entry_low=current-.45*avtr; entry_high=current+.10*avtr; stop=min(support-.20*avtr,entry_low-.85*avtr)
    entry_mid=(entry_low+entry_high)/2; risk=max(entry_mid-stop,.01)
    t1=max(resistance,entry_mid+1.5*risk); t2=max(resistance+avtr,entry_mid+2.2*risk)
    rr1=(t1-entry_mid)/risk; rr2=(t2-entry_mid)/risk
    if rv>=80: action="DON'T CHASE"; pred="UP" if day>=55 else "NEUTRAL"
    elif rv>=70 and not is_canadian_etf(t): action="WAIT FOR PULLBACK"; pred="UP" if day>=55 else "NEUTRAL"
    elif rr1<1.5: action="WAIT — POOR RISK/REWARD"; pred="UP" if day>=55 else "NEUTRAL"
    elif day>=75 and quality>=70: action="BUY SETUP / ENTRY FAVOURABLE"; pred="UP"
    elif day>=65 or swing>=70: action="WATCH FOR ENTRY"; pred="UP"
    elif day<=40 and swing<=45: action="AVOID / SELL REVIEW"; pred="DOWN"
    else: action="NO CLEAR ENTRY"; pred="NEUTRAL"
    return dict(ticker=t,name=ALL_NAMES.get(t,t),current=float(current),price_label=label,previous_close=prev,day=day,swing=swing,quality=quality,prediction=pred,action=action,rsi=float(rv),rel_volume=rel,vwap=vwap,entry_low=float(entry_low),entry_high=float(entry_high),stop=float(stop),target1=float(t1),target2=float(t2),rr1=float(rr1),rr2=float(rr2),rank=day*.45+swing*.25+quality*.30)

# Persistent storage: Supabase if configured, otherwise temporary session memory.
def get_db():
    if create_client is None: return None
    try: return create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"])
    except Exception: return None
DB=get_db(); PERSISTENT=DB is not None
if "predictions" not in st.session_state: st.session_state.predictions=[]

def save_prediction(r):
    row={"ticker":r["ticker"],"tracked_at":now_et().isoformat(),"trade_date":now_et().date().isoformat(),"prediction":r["prediction"],"action":r["action"],"day_score":r["day"],"swing_score":r["swing"],"quality_score":r["quality"],"start_price":r["current"],"entry_low":r["entry_low"],"entry_high":r["entry_high"],"stop_price":r["stop"],"target1":r["target1"],"target2":r["target2"],"close_price":None,"day_high":None,"day_low":None,"direction_correct":None,"stop_hit":None,"target1_hit":None,"target2_hit":None,"result_status":"OPEN"}
    if PERSISTENT:
        DB.table("prediction_tracker").insert(row).execute(); return "persistent"
    row["id"]=max([x.get("id",0) for x in st.session_state.predictions] or [0])+1; st.session_state.predictions.append(row); return "temporary"

def fetch_rows():
    if PERSISTENT:
        try: return DB.table("prediction_tracker").select("*").order("tracked_at",desc=True).execute().data or []
        except Exception: return []
    return list(st.session_state.predictions)

def update_row(row_id,vals):
    if PERSISTENT:
        DB.table("prediction_tracker").update(vals).eq("id",row_id).execute(); return
    for row in st.session_state.predictions:
        if row.get("id")==row_id: row.update(vals)

def settle(row):
    if row.get("result_status")=="CLOSED": return row
    d=daily_data(row["ticker"],"1mo")
    if d.empty: return row
    dates=pd.to_datetime(d.index).date; target=pd.to_datetime(row["trade_date"]).date(); mask=np.array([x==target for x in dates])
    if not mask.any(): return row
    z=d.loc[mask].iloc[-1]
    def val(k):
        x=z[k]; return float(x.iloc[0]) if isinstance(x,pd.Series) else float(x)
    close,high,low=val("Close"),val("High"),val("Low"); start=float(row["start_price"]); pred=row["prediction"]
    correct=(close>start) if pred=="UP" else (close<start) if pred=="DOWN" else None
    vals={"close_price":close,"day_high":high,"day_low":low,"direction_correct":correct,"stop_hit":low<=float(row["stop_price"]),"target1_hit":high>=float(row["target1"]),"target2_hit":high>=float(row["target2"]),"result_status":"CLOSED"}
    update_row(row["id"],vals); row.update(vals); return row

def show_trade(r,key):
    st.subheader(r["action"]); st.metric("CURRENT PRICE",f"${r['current']:.2f}"); st.caption(f"Price source: {r['price_label']}")
    st.markdown(f"### BUY ZONE\n**${r['entry_low']:.2f} – ${r['entry_high']:.2f}**\n\n### STOP / EXIT\n**${r['stop']:.2f}**\n\n### SELL TARGET 1\n**${r['target1']:.2f}**\n\n### SELL TARGET 2\n**${r['target2']:.2f}**")
    st.write(f"Day / Swing / Quality: **{r['day']} / {r['swing']} / {r['quality']}**")
    st.write(f"Risk/Reward T1: **1:{r['rr1']:.1f}**")
    if st.button("📌 Track this prediction today",key=key,use_container_width=True):
        mode=save_prediction(r); st.success("Prediction saved permanently." if mode=="persistent" else "Saved for this session. Connect Supabase for permanent history.")

try: saved_holdings=st.query_params.get("holdings","TRP.TO"); saved_watchlist=st.query_params.get("watchlist","")
except Exception: saved_holdings="TRP.TO"; saved_watchlist=""
st.subheader("My Holdings"); htxt=st.text_input("Stocks / ETFs you own",value=saved_holdings)
st.subheader("⭐ My Watchlist"); wtxt=st.text_input("Stocks / ETFs you want to watch",value=saved_watchlist)
holdings=[normalize_ticker(x) for x in htxt.split(",") if x.strip()]; watchlist=[normalize_ticker(x) for x in wtxt.split(",") if x.strip()]
if st.button("💾 Save My Stocks",use_container_width=True):
    st.query_params["holdings"]=",".join(holdings); st.query_params["watchlist"]=",".join(watchlist); st.success("Saved.")

scan_tab,my_tab,an_tab,track_tab=st.tabs(["Market Scanner","⭐ My Stocks","Analyze","📊 Prediction Tracker"])
with scan_tab:
    market=st.selectbox("Market",["TSX","S&P 500","Nasdaq-100","Canadian ETFs","All Markets"]); count=st.selectbox("Number to scan",[10,20,30,50],index=1)
    if st.button("🔎 Scan Now",type="primary",use_container_width=True):
        if market=="TSX": universe=list(TSX)
        elif market=="S&P 500": universe=list(SP500)
        elif market=="Nasdaq-100": universe=list(NASDAQ)
        elif market=="Canadian ETFs": universe=[x+".TO" for x in CANADIAN_ETFS]
        else: universe=list(dict.fromkeys(list(TSX)+list(SP500)+list(NASDAQ)+[x+".TO" for x in CANADIAN_ETFS]))
        universe=universe[:count]
        for t in holdings+watchlist:
            if t not in universe: universe.insert(0,t)
        results=[]; p=st.progress(0); status=st.empty()
        for i,t in enumerate(universe):
            status.write(f"Analyzing {t}..."); r=analyze(t)
            if r: results.append(r)
            p.progress((i+1)/len(universe))
        p.empty(); status.empty(); results=sorted(results,key=lambda x:x["rank"],reverse=True)
        if not results: st.error("No usable results.")
        else:
            st.subheader("🏆 Best Current Setup"); st.header(results[0]["ticker"]); st.write(results[0]["name"]); show_trade(results[0],"track_best")
            st.divider(); st.subheader("Top Opportunities")
            for i,r in enumerate(results[:10]):
                with st.expander(f"{r['ticker']} — {r['action']}"): show_trade(r,f"scan_{i}_{r['ticker']}")
with my_tab:
    personal=list(dict.fromkeys(holdings+watchlist))
    if st.button("Refresh My Stocks",use_container_width=True):
        for i,t in enumerate(personal):
            r=analyze(t)
            if r: st.header(t); st.caption("OWNED" if t in holdings else "WATCHLIST"); show_trade(r,f"my_{i}_{t}"); st.divider()
with an_tab:
    raw=st.text_input("Enter ticker",value="XEQT"); t=normalize_ticker(raw)
    if t!=raw.strip().upper(): st.caption(f"Using ticker: **{t}**")
    if st.button("Analyze",use_container_width=True):
        r=analyze(t)
        if not r: st.error("No usable market data was found.")
        else: st.header(r["ticker"]); st.write(r["name"]); show_trade(r,f"single_{r['ticker']}")
with track_tab:
    st.subheader("Prediction Tracker")
    st.success("Persistent storage connected." ) if PERSISTENT else st.warning("Temporary storage only. Connect Supabase for permanent multi-day history.")
    if st.button("🔄 Update results",use_container_width=True):
        n=0
        for row in fetch_rows():
            before=row.get("result_status"); after=settle(row)
            if before!="CLOSED" and after.get("result_status")=="CLOSED": n+=1
        st.success(f"Updated {n} prediction(s).")
    rows=fetch_rows(); settled=[]
    for row in rows:
        td=pd.to_datetime(row["trade_date"]).date()
        if row.get("result_status")!="CLOSED" and (td<now_et().date() or (td==now_et().date() and SESSION=="AFTERHOURS")): row=settle(row)
        settled.append(row)
    rows=settled
    closed=[x for x in rows if x.get("result_status")=="CLOSED"]
    if closed:
        scored=[x for x in closed if x.get("direction_correct") is not None]; correct=sum(1 for x in scored if x.get("direction_correct") is True); acc=correct/len(scored) if scored else None
        a,b,c,d=st.columns(4); a.metric("Closed",len(closed)); b.metric("Accuracy",f"{acc:.1%}" if acc is not None else "—"); c.metric("T1 hit",sum(bool(x.get("target1_hit")) for x in closed)); d.metric("Stop hit",sum(bool(x.get("stop_hit")) for x in closed))
    if not rows: st.info("No tracked predictions yet.")
    for row in rows:
        icon="✅" if row.get("direction_correct") is True else "❌" if row.get("direction_correct") is False else ""
        with st.expander(f"{icon} {row['ticker']} — {row['prediction']} — {row['trade_date']} — {row.get('result_status','OPEN')}"):
            st.write(f"Start price: **${float(row['start_price']):.2f}**"); st.write(f"Scores D/S/Q: **{row['day_score']} / {row['swing_score']} / {row['quality_score']}**"); st.write(f"Buy zone: **${float(row['entry_low']):.2f} – ${float(row['entry_high']):.2f}**"); st.write(f"Stop: **${float(row['stop_price']):.2f}**"); st.write(f"Targets: **${float(row['target1']):.2f} / ${float(row['target2']):.2f}**")
            if row.get("result_status")=="CLOSED":
                ch=float(row["close_price"])/float(row["start_price"])-1; st.write(f"Close: **${float(row['close_price']):.2f}** ({ch:+.2%} from tracked price)"); st.write(f"High / Low: **${float(row['day_high']):.2f} / ${float(row['day_low']):.2f}**"); st.write(f"Target 1 hit: **{'YES' if row.get('target1_hit') else 'NO'}**"); st.write(f"Target 2 hit: **{'YES' if row.get('target2_hit') else 'NO'}**"); st.write(f"Stop hit: **{'YES' if row.get('stop_hit') else 'NO'}**")
    if closed:
        df=pd.DataFrame(closed); st.download_button("Download closed predictions CSV",df.to_csv(index=False),"prediction_tracker.csv","text/csv",use_container_width=True)

with st.expander("How the Prediction Tracker works"):
    st.markdown("Track a stock when the app makes a call. After the session, Update results compares the tracked price with that day's close and records whether direction, targets, and stop were hit. Daily OHLC cannot determine which happened first if both a target and stop were touched; that can be improved later with intraday event-order tracking.")
st.divider(); st.caption(f"Page refreshed: {now_et().strftime('%I:%M:%S %p ET')} • Session: {SESSION_LABEL}")
