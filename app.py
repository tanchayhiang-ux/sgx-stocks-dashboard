import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz
import json
import os

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="SGX Stocks Dashboard",
    page_icon="📈",
    layout="wide"
)

# ==================================================
# AUTO REFRESH
# ==================================================

st.markdown(
"""
<meta http-equiv="refresh" content="30">
""",
unsafe_allow_html=True
)

# ==================================================
# DEFAULT STOCKS
# ==================================================

DEFAULT_STOCKS = {
    "D05.SI": "DBS",
    "O39.SI": "OCBC",
    "U11.SI": "UOB",
    "BN4.SI": "Keppel",
    "9CI.SI": "CapitaLand Investment",
    "C38U.SI": "CapitaLand Integrated Commercial Trust",
    "G07.SI": "Great Eastern",
    "U10.SI": "UOB Kay Hian",
    "Z74.SI": "Singtel"
}

WATCHLIST_FILE = "watchlist.json"

# ==================================================
# WATCHLIST FUNCTIONS
# ==================================================

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_STOCKS

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f)

watchlist = load_watchlist()

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("⭐ Watchlist")

new_symbol = st.sidebar.text_input(
    "Add SGX Symbol",
    placeholder="e.g. A17U.SI"
)

new_name = st.sidebar.text_input(
    "Stock Name",
    placeholder="e.g. Ascendas REIT"
)

if st.sidebar.button("Add Stock"):
    if new_symbol:
        watchlist[new_symbol.upper()] = new_name
        save_watchlist(watchlist)
        st.rerun()

remove_stock = st.sidebar.selectbox(
    "Remove Stock",
    [""] + list(watchlist.keys())
)

if st.sidebar.button("Remove"):
    if remove_stock:
        del watchlist[remove_stock]
        save_watchlist(watchlist)
        st.rerun()

# ==================================================
# MARKET STATUS
# ==================================================

sg_time = datetime.now(
    pytz.timezone("Asia/Singapore")
)

market_open = (
    sg_time.weekday() < 5
    and 9 <= sg_time.hour < 17
)

status = "🟢 SGX OPEN" if market_open else "🔴 SGX CLOSED"

st.title("📈 SGX Stock Dashboard")

st.subheader(status)

# ==================================================
# PORTFOLIO CALCULATOR
# ==================================================

st.sidebar.markdown("---")
st.sidebar.header("💰 Portfolio Calculator")

portfolio_shares = {}

for symbol, name in watchlist.items():
    portfolio_shares[symbol] = st.sidebar.number_input(
        f"{name}",
        min_value=0,
        value=0
    )

# ==================================================
# STOCK CARDS
# ==================================================

portfolio_value = 0

for symbol, name in watchlist.items():

    try:

        stock = yf.Ticker(symbol)

        info = stock.info

        hist = stock.history(period="2d")

        current = info.get("currentPrice")

        previous = info.get("previousClose")

        change = current - previous

        pct = change / previous * 100

        color = "green" if change >= 0 else "red"

        market_cap = info.get("marketCap")

        pe = info.get("trailingPE")

        dividend = info.get("dividendYield")

        high52 = info.get("fiftyTwoWeekHigh")

        low52 = info.get("fiftyTwoWeekLow")

        shares = portfolio_shares[symbol]

        stock_value = shares * current

        portfolio_value += stock_value

        st.markdown(
        f"""
        <div style="
        border-radius:15px;
        padding:20px;
        margin-bottom:15px;
        border:1px solid #444;
        ">
        <h3>{name} ({symbol})</h3>

        <h2>S${current:.2f}</h2>

        <h4 style='color:{color};'>
        {change:+.2f}
        ({pct:+.2f}%)
        </h4>

        <b>Dividend Yield:</b> {dividend*100 if dividend else 0:.2f}%<br>

        <b>PE Ratio:</b> {pe}<br>

        <b>Market Cap:</b>
        {market_cap:,.0f}<br>

        <b>52W High:</b> {high52}<br>

        <b>52W Low:</b> {low52}<br>

        <b>Your Holdings:</b> {shares}<br>

        <b>Value:</b> S${stock_value:,.2f}
        </div>
        """,
        unsafe_allow_html=True
        )

        # ======================================
        # CHART
        # ======================================

        chart_data = stock.history(
            period="6mo"
        )

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=chart_data.index,
                    open=chart_data["Open"],
                    high=chart_data["High"],
                    low=chart_data["Low"],
                    close=chart_data["Close"]
                )
            ]
        )

        fig.update_layout(
            height=400,
            title=f"{name} Candlestick Chart"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ======================================
        # DIVIDEND HISTORY
        # ======================================

        dividends = stock.dividends.tail(20)

        if not dividends.empty:

            st.write("### Dividend History")

            div_df = dividends.reset_index()

            div_df.columns = [
                "Date",
                "Dividend"
            ]

            st.dataframe(
                div_df,
                use_container_width=True
            )

    except:
        st.warning(
            f"Unable to retrieve {symbol}"
        )

# ==================================================
# PORTFOLIO SUMMARY
# ==================================================

st.markdown("---")

st.header("💰 Portfolio Summary")

st.metric(
    "Current Portfolio Value",
    f"S${portfolio_value:,.2f}"
)

# ==================================================
# REIT DASHBOARD
# ==================================================

st.markdown("---")

st.header("🏢 SGX REIT Dashboard")

REITS = [
    "A17U.SI",
    "C38U.SI",
    "M44U.SI",
    "ME8U.SI"
]

reit_rows = []

for r in REITS:

    try:

        s = yf.Ticker(r)

        info = s.info

        reit_rows.append(
            {
                "Symbol": r,
                "Price": info.get(
                    "currentPrice"
                ),
                "Yield %":
                round(
                    (info.get(
                        "dividendYield",0
                    )*100),
                    2
                )
            }
        )

    except:
        pass

st.dataframe(
    pd.DataFrame(reit_rows),
    use_container_width=True
)
