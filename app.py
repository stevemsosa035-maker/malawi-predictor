import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.worldbank_collector import fetch_all
from data.forex_collector import fetch_latest_rate
from data.news_collector import fetch_all_news

st.set_page_config(
    page_title="Malawi Economic Predictor",
    page_icon="\U0001f1f2\U0001f1fc",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar ─────────────────────────────────────────────────────
st.sidebar.title("\U0001f1f2\U0001f1fc Malawi Predictor")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    [
        "\U0001f4ca Dashboard",
        "\U0001f4b1 Exchange Rates",
        "\U0001f4c8 Inflation",
        "\U0001f3e6 Macro Indicators",
        "\U0001f4f0 News & Sentiment",
        "\u26a0\ufe0f Risk Signals",
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("Data refreshes every 6 hours")

# ── Cached data loaders ─────────────────────────────────────────
@st.cache_data(ttl=21600)
def load_macro():
    return fetch_all(start_year=2000)

@st.cache_data(ttl=3600)
def load_forex():
    return fetch_latest_rate()

@st.cache_data(ttl=3600)
def load_news():
    return fetch_all_news()

# ── Helper ──────────────────────────────────────────────────────
def get_latest(data, key):
    df = data.get(key)
    if df is not None and not df.empty:
        row = df.iloc[-1]
        return round(float(row["value"]), 2), int(row["year"])
    return None, None


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════
if page == "\U0001f4ca Dashboard":
    st.title("Malawi Economic Predictor")
    st.markdown("Live data — World Bank · RBM · Malawi news sources")
    st.markdown("---")

    macro = load_macro()
    forex = load_forex()

    col1, col2, col3, col4 = st.columns(4)

    inflation, yr1 = get_latest(macro, "Inflation CPI percent")
    with col1:
        st.metric("\U0001f525 Inflation (CPI)",
                  f"{inflation}%" if inflation else "N/A",
                  f"{yr1}" if yr1 else "")

    gdp, yr2 = get_latest(macro, "GDP growth percent")
    with col2:
        st.metric("\U0001f4c8 GDP Growth",
                  f"{gdp}%" if gdp else "N/A",
                  f"{yr2}" if yr2 else "")

    rate, yr3 = get_latest(macro, "Lending interest rate percent")
    with col3:
        st.metric("\U0001f3e6 Lending Rate",
                  f"{rate}%" if rate else "N/A",
                  f"{yr3}" if yr3 else "")

    with col4:
        fx = forex.get("rate")
        st.metric("\U0001f4b1 MWK / USD",
                  f"{fx:,.0f}" if fx else "N/A",
                  "Live rate")

    st.markdown("---")

    # Mini inflation chart on dashboard
    inf_df = macro.get("Inflation CPI percent")
    if inf_df is not None and not inf_df.empty:
        fig = px.area(
            inf_df, x="year", y="value",
            title="Inflation trend (2000 to present)",
            labels={"year": "Year", "value": "Inflation %"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            height=300,
        )
        fig.update_traces(line_color="#FF4B4B", fillcolor="rgba(255,75,75,0.2)")
        st.plotly_chart(fig, use_container_width=True)

    # Latest news on dashboard
    st.markdown("---")
    st.subheader("\U0001f4f0 Latest economic headlines")
    news_df = load_news()
    if not news_df.empty:
        econ = news_df[news_df["is_economic"] == True].head(5)
        if econ.empty:
            st.info("No economic headlines right now.")
        else:
            for _, row in econ.iterrows():
                st.markdown(f"**[{row['source']}]** [{row['title']}]({row['link']})")
    else:
        st.warning("News feed not available.")


# ════════════════════════════════════════════════════════════════
# EXCHANGE RATES
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b1 Exchange Rates":
    st.title("Exchange Rates — MWK")

    forex = load_forex()
    macro = load_macro()

    fx_rate = forex.get("rate")
    fx_time = forex.get("timestamp")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Live rate", f"1 USD = {fx_rate:,.2f} MWK" if fx_rate else "N/A", "Updated just now")
    with col2:
        st.metric("Source", forex.get("source", "N/A"), fx_time or "")

    st.markdown("---")

    # Historical annual exchange rate from World Bank
    fx_df = macro.get("Exchange rate MWK per USD")
    if fx_df is not None and not fx_df.empty:
        fig = px.line(
            fx_df, x="year", y="value",
            title="MWK per USD — Annual average (World Bank)",
            labels={"year": "Year", "value": "MWK per 1 USD"},
            markers=True,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
        )
        fig.update_traces(line_color="#F4C542", marker_color="#F4C542")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Note: Annual averages from World Bank. Live rate above from open.er-api.com.")
    else:
        st.warning("Historical exchange rate data not available.")


# ════════════════════════════════════════════════════════════════
# INFLATION
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4c8 Inflation":
    st.title("Inflation Tracker")

    macro = load_macro()
    inf_df = macro.get("Inflation CPI percent")

    if inf_df is not None and not inf_df.empty:
        latest_val = inf_df.iloc[-1]["value"]
        latest_yr  = int(inf_df.iloc[-1]["year"])
        prev_val   = inf_df.iloc[-2]["value"] if len(inf_df) > 1 else latest_val
        delta      = round(latest_val - prev_val, 2)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current inflation", f"{latest_val:.1f}%", f"{delta:+.1f}% vs prior year")
        with col2:
            st.metric("Year", str(latest_yr), "Latest available")
        with col3:
            status = "\U0001f534 Very high" if latest_val > 20 else "\U0001f7e1 Elevated" if latest_val > 10 else "\U0001f7e2 Moderate"
            st.metric("Status", status, "")

        st.markdown("---")

        fig = px.bar(
            inf_df, x="year", y="value",
            title="Malawi Inflation Rate (CPI) — Annual %",
            labels={"year": "Year", "value": "Inflation %"},
            color="value",
            color_continuous_scale="RdYlGn_r",
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Raw data")
        st.dataframe(inf_df.sort_values("year", ascending=False).reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Inflation data not available.")


# ════════════════════════════════════════════════════════════════
# MACRO INDICATORS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f3e6 Macro Indicators":
    st.title("Macro Indicators — Malawi")

    macro = load_macro()

    if not macro:
        st.error("Could not load data.")
    else:
        indicator = st.selectbox("Select indicator", list(macro.keys()))
        df = macro[indicator]

        latest = df.iloc[-1]
        st.metric(indicator, f"{latest['value']:.2f}", f"Latest: {int(latest['year'])}")

        fig = px.line(
            df, x="year", y="value",
            title=f"{indicator} — Malawi",
            labels={"year": "Year", "value": indicator},
            markers=True,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
        )
        fig.update_traces(line_color="#00C49F", marker_color="#00C49F")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Raw data")
        st.dataframe(df.sort_values("year", ascending=False).reset_index(drop=True), use_container_width=True)


# ════════════════════════════════════════════════════════════════
# NEWS & SENTIMENT
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4f0 News & Sentiment":
    st.title("News & Sentiment")

    news_df = load_news()

    if news_df.empty:
        st.warning("No news available. Check internet connection.")
    else:
        total   = len(news_df)
        economic = int(news_df["is_economic"].sum())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total headlines", total)
        with col2:
            st.metric("Economic headlines", economic)
        with col3:
            pct = round((economic / total) * 100) if total > 0 else 0
            st.metric("Economic focus", f"{pct}%")

        st.markdown("---")

        tab1, tab2 = st.tabs(["\U0001f4ca Economic news only", "\U0001f4f0 All headlines"])

        with tab1:
            econ = news_df[news_df["is_economic"] == True].reset_index(drop=True)
            if econ.empty:
                st.info("No economic headlines right now.")
            else:
                for _, row in econ.iterrows():
                    st.markdown(f"**[{row['source']}]** [{row['title']}]({row['link']})")
                    st.caption(str(row["date"])[:25])
                    st.markdown("---")

        with tab2:
            for _, row in news_df.iterrows():
                tag = "\U0001f4b0 Economic" if row["is_economic"] else "\u26aa General"
                st.markdown(f"{tag} **[{row['source']}]** [{row['title']}]({row['link']})")
                st.caption(str(row["date"])[:25])
                st.markdown("---")


# ════════════════════════════════════════════════════════════════
# RISK SIGNALS
# ════════════════════════════════════════════════════════════════
elif page == "\u26a0\ufe0f Risk Signals":
    st.title("Economic Risk Signals")
    st.markdown("Automated signals based on current economic conditions.")
    st.markdown("---")

    macro = load_macro()
    forex = load_forex()

    signals = []

    inflation, _ = get_latest(macro, "Inflation CPI percent")
    if inflation:
        if inflation > 25:
            signals.append(("\U0001f534 CRITICAL", "Inflation", f"{inflation}% — Severely above target. High cost of living risk."))
        elif inflation > 15:
            signals.append(("\U0001f7e0 HIGH", "Inflation", f"{inflation}% — Well above target. Monitor closely."))
        elif inflation > 8:
            signals.append(("\U0001f7e1 MODERATE", "Inflation", f"{inflation}% — Elevated but not critical."))
        else:
            signals.append(("\U0001f7e2 LOW", "Inflation", f"{inflation}% — Under control."))

    gdp, _ = get_latest(macro, "GDP growth percent")
    if gdp:
        if gdp < 0:
            signals.append(("\U0001f534 CRITICAL", "GDP Growth", f"{gdp}% — Economy is contracting."))
        elif gdp < 2:
            signals.append(("\U0001f7e0 HIGH", "GDP Growth", f"{gdp}% — Very slow growth. Recession risk."))
        elif gdp < 4:
            signals.append(("\U0001f7e1 MODERATE", "GDP Growth", f"{gdp}% — Below potential."))
        else:
            signals.append(("\U0001f7e2 LOW", "GDP Growth", f"{gdp}% — Healthy growth."))

    debt, _ = get_latest(macro, "Government debt percent of GDP")
    if debt:
        if debt > 80:
            signals.append(("\U0001f534 CRITICAL", "Government Debt", f"{debt}% of GDP — Debt crisis territory."))
        elif debt > 60:
            signals.append(("\U0001f7e0 HIGH", "Government Debt", f"{debt}% of GDP — Above sustainability threshold."))
        elif debt > 40:
            signals.append(("\U0001f7e1 MODERATE", "Government Debt", f"{debt}% of GDP — Watch closely."))
        else:
            signals.append(("\U0001f7e2 LOW", "Government Debt", f"{debt}% of GDP — Manageable."))

    fx = forex.get("rate")
    if fx:
        if fx > 1700:
            signals.append(("\U0001f534 CRITICAL", "Exchange Rate", f"1 USD = {fx:,.0f} MWK — Severe depreciation."))
        elif fx > 1200:
            signals.append(("\U0001f7e0 HIGH", "Exchange Rate", f"1 USD = {fx:,.0f} MWK — Significant weakness."))
        else:
            signals.append(("\U0001f7e2 LOW", "Exchange Rate", f"1 USD = {fx:,.0f} MWK — Relatively stable."))

    if not signals:
        st.info("No signals generated yet.")
    else:
        for level, category, message in signals:
            if "CRITICAL" in level:
                st.error(f"{level} | **{category}** — {message}")
            elif "HIGH" in level:
                st.warning(f"{level} | **{category}** — {message}")
            elif "MODERATE" in level:
                st.info(f"{level} | **{category}** — {message}")
            else:
                st.success(f"{level} | **{category}** — {message}")

    st.markdown("---")
    st.caption("Risk signals are based on threshold rules. Prediction models coming in Phase 2.")
