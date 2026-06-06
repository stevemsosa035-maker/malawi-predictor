import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.worldbank_collector import fetch_all as wb_fetch
from data.imf_collector import fetch_all as imf_fetch, get_current_value
from data.forex_collector import fetch_latest_rate
from data.news_collector import fetch_all_news
from data.forecaster import forecast_indicator, build_forecast_chart_data

st.set_page_config(
    page_title="Malawi Economic Predictor",
    page_icon="\U0001f1f2\U0001f1fc",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("\U0001f1f2\U0001f1fc Malawi Predictor")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    [
        "\U0001f4ca Dashboard",
        "\U0001f4b1 Exchange Rates",
        "\U0001f4c8 Inflation",
        "\U0001f52e Forecasts",
        "\U0001f3e6 Macro Indicators",
        "\U0001f4f0 News & Sentiment",
        "\u26a0\ufe0f Risk Signals",
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("IMF · World Bank · RBM · Live news")

@st.cache_data(ttl=21600)
def load_imf():
    return imf_fetch()

@st.cache_data(ttl=21600)
def load_wb():
    return wb_fetch(start_year=2000)

@st.cache_data(ttl=3600)
def load_forex():
    return fetch_latest_rate()

@st.cache_data(ttl=3600)
def load_news():
    return fetch_all_news()


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════
if page == "\U0001f4ca Dashboard":
    st.title("Malawi Economic Predictor")
    st.markdown("Live data — IMF · World Bank · RBM · Malawi news")
    st.markdown("---")

    imf = load_imf()
    forex = load_forex()

    col1, col2, col3, col4 = st.columns(4)

    inf_val, inf_yr = get_current_value("Inflation Rate (%)", imf)
    with col1:
        st.metric("\U0001f525 Inflation",
                  f"{inf_val}%" if inf_val else "N/A",
                  f"IMF {inf_yr}" if inf_yr else "")

    gdp_val, gdp_yr = get_current_value("GDP Growth (%)", imf)
    with col2:
        st.metric("\U0001f4c8 GDP Growth",
                  f"{gdp_val}%" if gdp_val else "N/A",
                  f"IMF {gdp_yr}" if gdp_yr else "")

    debt_val, debt_yr = get_current_value("Government Debt (% GDP)", imf)
    with col3:
        st.metric("\U0001f3e6 Govt Debt",
                  f"{debt_val}%" if debt_val else "N/A",
                  f"IMF {debt_yr}" if debt_yr else "")

    fx = forex.get("rate")
    with col4:
        st.metric("\U0001f4b1 MWK/USD",
                  f"{fx:,.0f}" if fx else "N/A",
                  "Live rate")

    st.markdown("---")

    # Inflation chart from IMF
    inf_df = imf.get("Inflation Rate (%)")
    if inf_df is not None and not inf_df.empty:
        fig = px.area(
            inf_df, x="year", y="value",
            title="Malawi Inflation (IMF data — 2026)",
            labels={"year": "Year", "value": "Inflation %"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", height=300,
        )
        fig.update_traces(line_color="#FF4B4B", fillcolor="rgba(255,75,75,0.2)")
        st.plotly_chart(fig, use_container_width=True)

    # Latest news
    st.markdown("---")
    st.subheader("\U0001f4f0 Latest economic headlines")
    news_df = load_news()
    if not news_df.empty:
        econ = news_df[news_df["is_economic"] == True].head(5)
        for _, row in econ.iterrows():
            st.markdown(f"**[{row['source']}]** [{row['title']}]({row['link']})")
    else:
        st.warning("News feed not available.")


# ════════════════════════════════════════════════════════════════
# FORECASTS — NEW PAGE
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f52e Forecasts":
    st.title("Economic Forecasts")
    st.markdown("ARIMA model predicting future values based on historical trends.")
    st.markdown("---")

    imf = load_imf()

    indicator = st.selectbox(
        "Select indicator to forecast",
        ["Inflation Rate (%)", "GDP Growth (%)",
         "Government Debt (% GDP)", "Current Account (% GDP)"]
    )

    steps = st.slider("Years ahead to forecast", 1, 10, 5)

    df = imf.get(indicator)

    if df is None or df.empty:
        st.error("No data available for this indicator.")
    else:
        with st.spinner("Running ARIMA forecast model..."):
            result = forecast_indicator(df, steps=steps, indicator_name=indicator)

        if result is None:
            st.error("Could not generate forecast. Not enough historical data.")
        else:
            combined, fc = build_forecast_chart_data(df, result)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Last actual",
                          f"{result['last_actual_value']}%",
                          f"{result['last_actual_year']}")
            with col2:
                next_yr = result["years"][0]
                next_val = result["forecast"][0]
                delta = round(next_val - result["last_actual_value"], 2)
                st.metric(f"Forecast {next_yr}",
                          f"{next_val}%",
                          f"{delta:+.2f}%")
            with col3:
                last_fc = result["forecast"][-1]
                last_yr = result["years"][-1]
                st.metric(f"Forecast {last_yr}",
                          f"{last_fc}%", "")

            # Combined chart
            fig = go.Figure()

            actual = combined[combined["type"] == "Actual"]
            forecast = combined[combined["type"] == "Forecast"]

            fig.add_trace(go.Scatter(
                x=actual["year"], y=actual["value"],
                mode="lines+markers",
                name="Actual",
                line=dict(color="#00C49F", width=2),
            ))

            fig.add_trace(go.Scatter(
                x=forecast["year"], y=forecast["value"],
                mode="lines+markers",
                name="Forecast",
                line=dict(color="#FF4B4B", width=2, dash="dash"),
            ))

            fig.add_trace(go.Scatter(
                x=result["years"] + result["years"][::-1],
                y=result["upper"] + result["lower"][::-1],
                fill="toself",
                fillcolor="rgba(255,75,75,0.1)",
                line=dict(color="rgba(255,75,75,0)"),
                name="Confidence range",
            ))

            fig.update_layout(
                title=f"{indicator} — Historical + {steps}-year Forecast",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("Forecast table")
            fc_table = pd.DataFrame({
                "Year": result["years"],
                "Forecast (%)": result["forecast"],
                "Lower bound (%)": result["lower"],
                "Upper bound (%)": result["upper"],
            })
            st.dataframe(fc_table, use_container_width=True)
            st.caption("Forecast based on ARIMA(1,1,1) model. Confidence range shown at 80%.")


# ════════════════════════════════════════════════════════════════
# EXCHANGE RATES
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b1 Exchange Rates":
    st.title("Exchange Rates — MWK")
    forex = load_forex()
    wb = load_wb()
    fx_rate = forex.get("rate")
    fx_time = forex.get("timestamp")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Live rate", f"1 USD = {fx_rate:,.2f} MWK" if fx_rate else "N/A", "Live")
    with col2:
        st.metric("Source", forex.get("source", "N/A"), str(fx_time or "")[:25])
    st.markdown("---")
    fx_df = wb.get("Exchange rate MWK per USD")
    if fx_df is not None and not fx_df.empty:
        fig = px.line(fx_df, x="year", y="value",
            title="MWK per USD — Annual average (World Bank)",
            labels={"year": "Year", "value": "MWK per 1 USD"}, markers=True)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        fig.update_traces(line_color="#F4C542", marker_color="#F4C542")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# INFLATION
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4c8 Inflation":
    st.title("Inflation Tracker")
    imf = load_imf()
    inf_df = imf.get("Inflation Rate (%)")
    if inf_df is not None and not inf_df.empty:
        latest_val = inf_df.iloc[-1]["value"]
        latest_yr = int(inf_df.iloc[-1]["year"])
        prev_val = inf_df.iloc[-2]["value"] if len(inf_df) > 1 else latest_val
        delta = round(latest_val - prev_val, 2)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current inflation", f"{latest_val:.1f}%", f"{delta:+.1f}% vs prior year")
        with col2:
            st.metric("Year", str(latest_yr), "IMF latest")
        with col3:
            status = "\U0001f534 Very high" if latest_val > 20 else "\U0001f7e1 Elevated" if latest_val > 10 else "\U0001f7e2 Moderate"
            st.metric("Status", status, "")
        st.markdown("---")
        fig = px.bar(inf_df, x="year", y="value",
            title="Malawi Inflation Rate (CPI) — IMF Annual %",
            labels={"year": "Year", "value": "Inflation %"},
            color="value", color_continuous_scale="RdYlGn_r")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.subheader("Raw data")
        st.dataframe(inf_df.sort_values("year", ascending=False).reset_index(drop=True), use_container_width=True)


# ════════════════════════════════════════════════════════════════
# MACRO INDICATORS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f3e6 Macro Indicators":
    st.title("Macro Indicators — Malawi")
    imf = load_imf()
    wb = load_wb()
    all_data = {**wb, **imf}
    if not all_data:
        st.error("Could not load data.")
    else:
        indicator = st.selectbox("Select indicator", list(all_data.keys()))
        df = all_data[indicator]
        latest = df.iloc[-1]
        st.metric(indicator, f"{latest['value']:.2f}", f"Latest: {int(latest['year'])}")
        fig = px.line(df, x="year", y="value",
            title=f"{indicator} — Malawi",
            labels={"year": "Year", "value": indicator}, markers=True)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        fig.update_traces(line_color="#00C49F", marker_color="#00C49F")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.sort_values("year", ascending=False).reset_index(drop=True), use_container_width=True)


# ════════════════════════════════════════════════════════════════
# NEWS & SENTIMENT
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4f0 News & Sentiment":
    st.title("News & Sentiment")
    news_df = load_news()
    if news_df.empty:
        st.warning("No news available.")
    else:
        total = len(news_df)
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
        tab1, tab2 = st.tabs(["\U0001f4ca Economic only", "\U0001f4f0 All headlines"])
        with tab1:
            econ = news_df[news_df["is_economic"] == True].reset_index(drop=True)
            for _, row in econ.iterrows():
                st.markdown(f"**[{row['source']}]** [{row['title']}]({row['link']})")
                st.caption(str(row["date"])[:25])
                st.markdown("---")
        with tab2:
            for _, row in news_df.iterrows():
                tag = "\U0001f4b0" if row["is_economic"] else "\u26aa"
                st.markdown(f"{tag} **[{row['source']}]** [{row['title']}]({row['link']})")
                st.caption(str(row["date"])[:25])
                st.markdown("---")


# ════════════════════════════════════════════════════════════════
# RISK SIGNALS
# ════════════════════════════════════════════════════════════════
elif page == "\u26a0\ufe0f Risk Signals":
    from data.devaluation_risk import calculate_devaluation_risk, get_risk_label
    import plotly.graph_objects as go

    st.title("Economic Risk Signals")
    st.markdown("---")

    imf = load_imf()
    forex = load_forex()

    inf_val, _  = get_current_value("Inflation Rate (%)", imf)
    gdp_val, _  = get_current_value("GDP Growth (%)", imf)
    debt_val, _ = get_current_value("Government Debt (% GDP)", imf)
    ca_val, _   = get_current_value("Current Account (% GDP)", imf)
    fx          = forex.get("rate")

    risk = calculate_devaluation_risk(
        inflation=inf_val,
        mwk_per_usd=fx,
        gdp_growth=gdp_val,
        government_debt=debt_val,
        current_account=ca_val,
    )

    score = risk["score"]
    level = risk["level"]
    message = risk["message"]

    # ── Gauge ───────────────────────────────────────────────────
    st.subheader("Kwacha Devaluation Risk Score")

    col1, col2 = st.columns([1, 2])

    with col1:
        label = get_risk_label(score)
        st.metric("Risk Score", f"{score} / 100", label)
        if level == "CRITICAL":
            st.error(f"\U0001f534 {level} — {message}")
        elif level == "HIGH":
            st.warning(f"\U0001f7e0 {level} — {message}")
        elif level == "MODERATE":
            st.info(f"\U0001f7e1 {level} — {message}")
        else:
            st.success(f"\U0001f7e2 {level} — {message}")

    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Devaluation Risk", "font": {"color": "white"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "white"},
                "bar": {"color": "white"},
                "steps": [
                    {"range": [0, 35],  "color": "#1a472a"},
                    {"range": [35, 55], "color": "#7d6608"},
                    {"range": [55, 75], "color": "#784212"},
                    {"range": [75, 100],"color": "#641e16"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": score
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Individual signals ───────────────────────────────────────
    st.markdown("---")
    st.subheader("Individual signals")
    signals = []
    if inf_val:
        if inf_val > 25:
            signals.append(("\U0001f534 CRITICAL", "Inflation", f"{inf_val}% — Severely above target."))
        elif inf_val > 15:
            signals.append(("\U0001f7e0 HIGH", "Inflation", f"{inf_val}% — Well above target."))
        else:
            signals.append(("\U0001f7e1 MODERATE", "Inflation", f"{inf_val}% — Elevated."))
    if gdp_val:
        if gdp_val < 0:
            signals.append(("\U0001f534 CRITICAL", "GDP Growth", f"{gdp_val}% — Economy contracting."))
        elif gdp_val < 2:
            signals.append(("\U0001f7e0 HIGH", "GDP Growth", f"{gdp_val}% — Very slow. Recession risk."))
        elif gdp_val < 4:
            signals.append(("\U0001f7e1 MODERATE", "GDP Growth", f"{gdp_val}% — Below potential."))
        else:
            signals.append(("\U0001f7e2 LOW", "GDP Growth", f"{gdp_val}% — Healthy."))
    if debt_val:
        if debt_val > 80:
            signals.append(("\U0001f534 CRITICAL", "Govt Debt", f"{debt_val}% of GDP — Crisis territory."))
        elif debt_val > 60:
            signals.append(("\U0001f7e0 HIGH", "Govt Debt", f"{debt_val}% of GDP — Above threshold."))
        else:
            signals.append(("\U0001f7e1 MODERATE", "Govt Debt", f"{debt_val}% of GDP — Watch closely."))
    if fx:
        if fx > 1700:
            signals.append(("\U0001f534 CRITICAL", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Severe depreciation."))
        elif fx > 1200:
            signals.append(("\U0001f7e0 HIGH", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Significant weakness."))
        else:
            signals.append(("\U0001f7e2 LOW", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Relatively stable."))
    for level, category, message in signals:
        if "CRITICAL" in level:
            st.error(f"{level} | **{category}** — {message}")
        elif "HIGH" in level:
            st.warning(f"{level} | **{category}** — {message}")
        elif "MODERATE" in level:
            st.info(f"{level} | **{category}** — {message}")
        else:
            st.success(f"{level} | **{category}** — {message}")

    # ── Component breakdown ──────────────────────────────────────
    st.markdown("---")
    st.subheader("Component breakdown")
    for name, data in risk["components"].items():
        s = data["score"]
        w = data["weight"]
        contribution = round(s * w, 1)
        label = get_risk_label(s)
        st.markdown(f"**{name}** — Score: {s}/100 | Weight: {int(w*100)}% | Contribution: {contribution}")
        st.progress(s / 100)

    st.markdown("---")
    st.caption("Score combines inflation, exchange rate, GDP, debt, current account and news sentiment.")
