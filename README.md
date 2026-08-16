# Stock Day Predictor — Mobile V2

Mobile-first Streamlit app estimating whether a stock/ETF will finish above the previous regular-session close.

## Includes
- No-lookahead historical model: features from one day predict the next trading day.
- Live/premarket overlay from public 5-minute market data when available.
- SPY, QQQ, sector ETF, VIX, and 10-year Treasury signals.
- Current stock move versus prior close.
- Recent headline sentiment.
- Held-out accuracy and Brier score.
- iPhone-friendly layout.

## Local run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for iPhone
1. Put `app.py`, `requirements.txt`, and `.streamlit/config.toml` into a GitHub repository.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Create an app from that repository and set `app.py` as the entrypoint.
4. Open the generated `streamlit.app` URL on your iPhone.
5. In Safari: Share → Add to Home Screen.

Optional: add `ALPHA_VANTAGE_API_KEY` in Streamlit Secrets for improved news sentiment.

This is a research tool, not a guaranteed trading signal. Free/public feeds may be delayed or incomplete.
