import os
from datetime import datetime, time
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title='Stock Day Predictor', page_icon='📈', layout='centered', initial_sidebar_state='collapsed')
st.markdown('''<style>.block-container{padding-top:1.1rem;max-width:780px}.bigprob{font-size:3.1rem;font-weight:800;line-height:1}div[data-testid="stMetric"]{background:rgba(128,128,128,.08);padding:12px;border-radius:14px}</style>''', unsafe_allow_html=True)
st.title('Stock Day Predictor')
st.caption("Probability a stock finishes above the previous regular-session close.")

@st.cache_data(ttl=900)
def daily(ticker, period='5y'):
    x=yf.download(ticker,period=period,interval='1d',auto_adjust=True,progress=False,threads=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    return x.dropna().copy()

@st.cache_data(ttl=120)
def intraday(ticker):
    x=yf.download(ticker,period='5d',interval='5m',auto_adjust=False,prepost=True,progress=False,threads=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    return x.dropna().copy()

def ser(df,col):
    x=df[col]
    if isinstance(x,pd.DataFrame): x=x.iloc[:,0]
    return pd.to_numeric(x,errors='coerce')

def rsi(c,n=14):
    d=c.diff(); up=d.clip(lower=0).rolling(n).mean(); dn=(-d.clip(upper=0)).rolling(n).mean(); rs=up/dn.replace(0,np.nan)
    return 100-100/(1+rs)

def features(stock,spy,qqq,sector,vix,tnx):
    c,o,h,l,v=[ser(stock,k) for k in ['Close','Open','High','Low','Volume']]
    f=pd.DataFrame(index=stock.index)
    f['ret1']=c.pct_change(); f['ret3']=c.pct_change(3); f['ret5']=c.pct_change(5); f['ret20']=c.pct_change(20)
    f['range']=(h-l)/c; f['gap']=o/c.shift(1)-1
    f['ma5_20']=c.rolling(5).mean()/c.rolling(20).mean()-1
    f['ma20_50']=c.rolling(20).mean()/c.rolling(50).mean()-1
    f['vol20']=c.pct_change().rolling(20).std(); f['volume_z']=(v-v.rolling(20).mean())/v.rolling(20).std(); f['rsi']=rsi(c)/100
    for name,df in [('spy',spy),('qqq',qqq),('sector',sector),('vix',vix),('tnx',tnx)]:
        mc=ser(df,'Close').reindex(f.index).ffill(); f[name+'1']=mc.pct_change(); f[name+'5']=mc.pct_change(5)
    f['target_next_up']=(c.shift(-1)>c).astype(float); f.iloc[-1,f.columns.get_loc('target_next_up')]=np.nan
    return f.replace([np.inf,-np.inf],np.nan)

def train_model(f):
    cols=[c for c in f.columns if c!='target_next_up']; clean=f.dropna(subset=cols+['target_next_up'])
    split=max(int(len(clean)*.8),100); tr,te=clean.iloc[:split],clean.iloc[split:]
    model=Pipeline([('scale',StandardScaler()),('clf',LogisticRegression(C=.45,max_iter=3000))])
    model.fit(tr[cols],tr['target_next_up'].astype(int)); probs=model.predict_proba(te[cols])[:,1]
    acc=accuracy_score(te['target_next_up'].astype(int),(probs>=.5).astype(int)); brier=brier_score_loss(te['target_next_up'].astype(int),probs)
    model.fit(clean[cols],clean['target_next_up'].astype(int)); latest=f.dropna(subset=cols).iloc[[-1]][cols]
    return float(model.predict_proba(latest)[0,1]),acc,brier

def live_return(ticker,d):
    try:
        x=intraday(ticker); lp=float(ser(x,'Close').dropna().iloc[-1]); pc=float(ser(d,'Close').dropna().iloc[-1]); return lp/pc-1,lp,pc
    except Exception: return None,None,None

POS={'beat','beats','surge','surges','growth','record','upgrade','upgraded','strong','bullish','profit','rally','gain','gains','higher','positive','approval','approved','contract','partnership','outperform'}
NEG={'miss','misses','drop','drops','fall','falls','downgrade','downgraded','weak','bearish','loss','lawsuit','probe','investigation','recall','cuts','lower','negative','warning','fraud','delay','underperform'}

@st.cache_data(ttl=300)
def yahoo_sentiment(ticker):
    try:
        news=yf.Ticker(ticker).news or []; vals=[]; titles=[]
        for item in news[:20]:
            content=item.get('content',item); title=content.get('title') or item.get('title') or ''
            if not title: continue
            words=set(''.join(ch.lower() if ch.isalnum() else ' ' for ch in title).split())
            vals.append(float(np.clip((len(words&POS)-len(words&NEG))/max(3,len(words)**.5),-1,1))); titles.append(title)
        return (float(np.mean(vals)) if vals else 0.0),titles[:5]
    except Exception: return 0.0,[]

@st.cache_data(ttl=300)
def alpha_sentiment(ticker,key):
    if not key: return None,[]
    try:
        r=requests.get('https://www.alphavantage.co/query',params={'function':'NEWS_SENTIMENT','tickers':ticker,'sort':'LATEST','limit':50,'apikey':key},timeout=12); data=r.json(); vals=[]; titles=[]
        for item in data.get('feed',[]):
            for ts in item.get('ticker_sentiment',[]):
                if ts.get('ticker','').upper()==ticker.upper(): vals.append(float(ts.get('ticker_sentiment_score',0))); titles.append(item.get('title','')); break
        return (float(np.mean(vals)) if vals else None),titles[:5]
    except Exception: return None,[]

def session_label():
    now=datetime.now(ZoneInfo('America/New_York'))
    if now.weekday()>=5: return 'Weekend — forecast is for the next trading session'
    if now.time()<time(9,30): return 'Pre-market forecast'
    if now.time()<=time(16): return 'Live intraday forecast'
    return 'After-hours — forecast is for the next trading session'

sector_defaults={'NVDA':'SMH','AMD':'SMH','AVGO':'SMH','AAPL':'XLK','MSFT':'XLK','META':'XLC','AMZN':'XLY','TSLA':'XLY','JPM':'XLF','XOM':'XLE','TRP.TO':'XEG.TO','CNQ.TO':'XEG.TO'}
ticker=st.text_input('Stock / ETF ticker','NVDA').upper().strip()
sector=st.text_input('Sector ETF',sector_defaults.get(ticker,'XLK')).upper().strip()
c1,c2=st.columns(2)
with c1: period=st.selectbox('History',['2y','5y','10y'],index=1)
with c2: threshold=st.selectbox('Strong-signal cutoff',[.55,.60,.65,.70],index=1,format_func=lambda x:f'{x:.0%}')
try: av_key=st.secrets.get('ALPHA_VANTAGE_API_KEY','')
except Exception: av_key=os.getenv('ALPHA_VANTAGE_API_KEY','')

if st.button('Analyze now',type='primary',use_container_width=True):
    with st.spinner('Reading market conditions and training the probability model...'):
        try:
            stock=daily(ticker,period); spy=daily('SPY',period); qqq=daily('QQQ',period); sec=daily(sector,period); vix=daily('^VIX',period); tnx=daily('^TNX',period)
            if len(stock)<180: st.error('Not enough price history for this ticker.'); st.stop()
            base,acc,brier=train_model(features(stock,spy,qqq,sec,vix,tnx))
            stock_live,lp,pc=live_return(ticker,stock); spy_live,_,_=live_return('SPY',spy); qqq_live,_,_=live_return('QQQ',qqq); sec_live,_,_=live_return(sector,sec); vix_live,_,_=live_return('^VIX',vix); tnx_live,_,_=live_return('^TNX',tnx)
            a_sent,a_titles=alpha_sentiment(ticker,av_key); y_sent,y_titles=yahoo_sentiment(ticker); news=a_sent if a_sent is not None else y_sent; headlines=a_titles if a_sent is not None else y_titles; source='Alpha Vantage' if a_sent is not None else 'headline heuristic'
            adj=0.0; rows=[]
            def add(name,raw,weight,pos=True,scale=.012):
                nonlocal_dummy=0
                if raw is None or not np.isfinite(raw): return 0
                z=np.tanh(raw/scale); z=z if pos else -z; impact=weight*z; rows.append((name,raw,impact)); return impact
            adj+=add('Stock live vs prev close',stock_live,.16); adj+=add('S&P 500 live',spy_live,.05); adj+=add('Nasdaq live',qqq_live,.07); adj+=add('Sector live',sec_live,.08); adj+=add('VIX move',vix_live,.05,False); adj+=add('10Y yield move',tnx_live,.025,False,.01)
            if news is not None and np.isfinite(news):
                scale=.35 if a_sent is not None else .60; impact=.055*np.tanh(news/scale); adj+=impact; rows.append(('News sentiment',news,impact))
            p=float(np.clip(base+adj,.05,.95)); down=1-p
            st.caption(session_label()); st.markdown(f'<div class="bigprob">{p:.0%} UP</div>',unsafe_allow_html=True)
            call='LIKELY GREEN' if p>=threshold else ('LIKELY RED' if down>=threshold else 'NO STRONG EDGE'); st.subheader(f'{ticker}: {call}')
            m1,m2,m3=st.columns(3); m1.metric('Model baseline',f'{base:.0%}'); m2.metric('Backtest accuracy',f'{acc:.1%}'); m3.metric('Brier score',f'{brier:.3f}')
            if lp and pc: st.metric('Latest vs previous close',f'{stock_live:+.2%}',f'${lp:,.2f}')
            st.subheader('What is moving the forecast')
            out=[]
            for name,raw,impact in sorted(rows,key=lambda z:abs(z[2]),reverse=True):
                reading=f'{raw:+.3f}' if 'sentiment' in name.lower() else f'{raw:+.2%}'
                effect='Bullish' if impact>.002 else ('Bearish' if impact<-.002 else 'Neutral')
                out.append({'Signal':name,'Current reading':reading,'Effect':effect,'Probability impact':f'{impact:+.1%}'})
            st.dataframe(pd.DataFrame(out),hide_index=True,use_container_width=True)
            if headlines:
                st.subheader('Recent headlines'); st.caption('Sentiment source: '+source)
                for h in headlines[:5]: st.write('•',h)
            st.subheader('How much should you trust it?')
            st.write(f'The held-out historical test was **{acc:.1%} accurate**. Judge the model over many predictions, not one day. A probability near 50% means the app sees little edge.')
            with st.expander('Method & limitations'):
                st.markdown('''The historical model uses a time-ordered split and predicts the **next** regular-session direction from information already known. The live overlay adds current/premarket stock, market, sector, VIX, yield, and headline signals. The overlay is bounded so one extreme signal cannot dominate. This is a research tool, not a guaranteed trade signal. Free/public feeds may be delayed or incomplete, and backtests do not guarantee future performance.''')
        except Exception as e:
            st.error("I couldn't complete this analysis for that ticker."); st.code(str(e))

st.divider(); st.caption('iPhone: open the deployed URL in Safari → Share → Add to Home Screen.')
