import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from modules.market.data import (
    get_ticker_info,
    get_price_history,
    add_moving_averages,
    detect_golden_death_cross,
    format_large_number,
)
from modules.market.charts import build_price_chart

from modules.market.data import (
    get_ticker_info,
    get_price_history,
    add_moving_averages,
    detect_golden_death_cross,
    format_large_number,
    search_tickers,
)

st.set_page_config(
    page_title="FinTerminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Terminal CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* dark terminal background */
    .stApp { background-color: #0e1117; }
    section[data-testid="stSidebar"] { background-color: #090c10; }

    /* metric cards */
    .fin-card {
        background: #161b22;
        border: 0.5px solid #30363d;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .fin-label {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .fin-value {
        font-size: 20px;
        font-weight: 600;
        color: #e6edf3;
    }
    .fin-value.up { color: #00aa44; }
    .fin-value.down { color: #cc0000; }

    /* signal banner */
    .signal-banner {
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
    }

    /* ticker header */
    .ticker-header {
        font-size: 28px;
        font-weight: 700;
        color: #e6edf3;
        letter-spacing: 0.05em;
    }
    .ticker-name {
        font-size: 14px;
        color: #8b949e;
        margin-bottom: 16px;
    }

    /* hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 FinTerminal")
    st.caption("Market Intelligence Platform")
    st.divider()

    st.markdown("### Search")
    
    search_query = st.text_input(
        "Search by name or ticker",
        placeholder="e.g. Apple, Tesla, MSFT",
    )

    ticker = ""

    if search_query:
        if len(search_query) <= 5 and search_query.isupper():
            # looks like a direct ticker entry
            ticker = search_query.strip()
        else:
            # search by name
            with st.spinner("Searching..."):
                results = search_tickers(search_query)
            
            if results:
                options = {
                    f"{r['symbol']} — {r['name']} ({r['exchange']})": r["symbol"]
                    for r in results
                    if r["type"] in ["EQUITY", "ETF", ""]
                }
                if options:
                    selected = st.selectbox("Select company", list(options.keys()))
                    ticker = options[selected]
                else:
                    st.warning("No equity results found.")
            else:
                st.warning("No results found. Try a different name.")

    period = st.radio(
        "Time Period",
        ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"],
        index=3,
        horizontal=True,
    )

    show_ma20 = st.checkbox("MA 20", value=True)
    show_ma50 = st.checkbox("MA 50", value=True)
    show_ma200 = st.checkbox("MA 200", value=True)

    st.divider()
    st.caption("Data: Yahoo Finance (15-min delay)")
    st.caption("For educational purposes only.")


# ── Main content ─────────────────────────────────────────────────────────────
if not ticker:
    st.info("Enter a ticker symbol in the sidebar to get started.")
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    info = get_ticker_info(ticker)
    df = get_price_history(ticker, period)
    df = add_moving_averages(df)

    # remove MAs based on checkbox
    if not show_ma20 and "MA20" in df.columns:
        df = df.drop(columns=["MA20"])
    if not show_ma50 and "MA50" in df.columns:
        df = df.drop(columns=["MA50"])
    if not show_ma200 and "MA200" in df.columns:
        df = df.drop(columns=["MA200"])

if "error" in info:
    st.error(f"Could not find ticker: {ticker}. Please check the symbol and try again.")
    st.stop()

if df.empty:
    st.error("No price data available for this ticker.")
    st.stop()

# ── Ticker header ─────────────────────────────────────────────────────────
current = info.get("current_price") or (df["Close"].iloc[-1] if not df.empty else None)
prev_close = info.get("previous_close") or (df["Close"].iloc[-2] if len(df) > 1 else None)

if current and prev_close:
    change = current - prev_close
    change_pct = (change / prev_close) * 100
    is_up = change >= 0
    change_str = f"{'▲' if is_up else '▼'} {abs(change):.2f} ({abs(change_pct):.2f}%)"
    change_class = "up" if is_up else "down"
else:
    change_str = "N/A"
    change_class = ""

current_str = f"${current:.2f}" if current else "N/A"

st.markdown(f"""
<div class="ticker-header">{ticker} &nbsp;
    <span style="font-size:20px" class="fin-value {change_class}">{current_str}</span>
    &nbsp;<span style="font-size:16px" class="fin-value {change_class}">{change_str}</span>
</div>
<div class="ticker-name">{info.get('name', '')} · {info.get('exchange', '')} · {info.get('currency', 'USD')}</div>
""", unsafe_allow_html=True)

# ── Signal banner ──────────────────────────────────────────────────────────
signal = detect_golden_death_cross(df)
if signal:
    st.markdown(f"""
    <div class="signal-banner" style="background:{signal['color']}22; border: 1px solid {signal['color']};">
        {signal['icon']} <strong>{signal['signal']}</strong> — {signal['description']}
    </div>
    """, unsafe_allow_html=True)

# ── Price chart ────────────────────────────────────────────────────────────
fig = build_price_chart(df, ticker, period)
st.plotly_chart(fig, width="stretch")

# ── KPI cards ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Key Statistics")

c1, c2, c3, c4, c5, c6 = st.columns(6)

def metric_card(label, value, cls=""):
    return f"""
    <div class="fin-card">
        <div class="fin-label">{label}</div>
        <div class="fin-value {cls}">{value}</div>
    </div>"""

with c1:
    st.markdown(metric_card("Market Cap", format_large_number(info.get("market_cap"))), unsafe_allow_html=True)
with c2:
    pe = info.get("pe_ratio")
    st.markdown(metric_card("P/E Ratio", f"{pe:.2f}" if pe else "N/A"), unsafe_allow_html=True)
with c3:
    eps = info.get("eps")
    st.markdown(metric_card("EPS (TTM)", f"${eps:.2f}" if eps else "N/A"), unsafe_allow_html=True)
with c4:
    dy = info.get("dividend_yield")
    st.markdown(metric_card("Dividend Yield", f"{dy*100:.2f}%" if dy else "N/A"), unsafe_allow_html=True)
with c5:
    st.markdown(metric_card("52W High", f"${info.get('week_52_high', 'N/A')}"), unsafe_allow_html=True)
with c6:
    st.markdown(metric_card("52W Low", f"${info.get('week_52_low', 'N/A')}"), unsafe_allow_html=True)

# ── Company description ────────────────────────────────────────────────────
st.divider()
with st.expander("About " + info.get("name", ticker)):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<p style='color:#8b949e; font-size:13px'>{info.get('description', 'N/A')}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Sector", info.get("sector", "N/A")), unsafe_allow_html=True)
        st.markdown(metric_card("Industry", info.get("industry", "N/A")), unsafe_allow_html=True)
        avg_vol = info.get("avg_volume")
        st.markdown(metric_card("Avg Volume", f"{avg_vol:,}" if avg_vol else "N/A"), unsafe_allow_html=True)