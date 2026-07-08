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
from data.devaluation_risk import calculate_devaluation_risk, get_risk_label
from data.investment_signals import generate_signals, get_action_emoji
from data.sentiment_scorer import score_news_feed, get_sentiment_emoji
from data.rbm_rates_collector import (
    get_policy_rate_history, get_current_policy_rate, get_rate_environment)

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
        "\U0001f4b9 Investment Signals",
        "\U0001f4b1 Forex Trading",
        "\U0001f3e6 Policy Rate",
        "\U0001f4b3 Interest Rates",
        "\U0001f3e6 Macro Indicators",
        "\U0001f4f0 News & Sentiment",
        "\u26a0\ufe0f Risk Signals",
        "\U0001f514 Alerts & Subscribe",
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("IMF \u00b7 RBM \u00b7 World Bank \u00b7 Live news")


@st.cache_data(ttl=21600)
def load_imf():
    actuals, imf_proj = imf_fetch()
    return actuals, imf_proj

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
    st.markdown("Live data — IMF \u00b7 RBM \u00b7 World Bank \u00b7 Malawi news")
    st.markdown("---")
    imf, imf_proj = load_imf()
    forex = load_forex()
    pr = get_current_policy_rate()
    col1, col2, col3, col4, col5 = st.columns(5)
    inf_val, inf_yr = get_current_value("Inflation Rate (%)", imf)
    with col1:
        st.metric("\U0001f525 Inflation", f"{inf_val}%" if inf_val else "N/A", f"IMF {inf_yr}")
    gdp_val, gdp_yr = get_current_value("GDP Growth (%)", imf)
    with col2:
        st.metric("\U0001f4c8 GDP Growth", f"{gdp_val}%" if gdp_val else "N/A", f"IMF {gdp_yr}")
    debt_val, _ = get_current_value("Government Debt (% GDP)", imf)
    with col3:
        st.metric("\U0001f3e6 Govt Debt", f"{debt_val}%" if debt_val else "N/A", "IMF")
    fx = forex.get("rate")
    with col4:
        st.metric("\U0001f4b1 MWK/USD", f"{fx:,.0f}" if fx else "N/A", "Live")
    with col5:
        env = get_rate_environment()
        st.metric("\U0001f3e6 Policy Rate", f"{pr['rate']}%",
            f"{pr['change']:+.1f}pp {pr['decision']}")
    st.markdown("---")
    inf_df = imf.get("Inflation Rate (%)")
    if inf_df is not None and not inf_df.empty:
        fig = px.area(inf_df, x="year", y="value",
            title="Malawi Inflation — Actuals only (up to 2026)",
            labels={"year": "Year", "value": "Inflation %"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
        fig.update_traces(line_color="#FF4B4B", fillcolor="rgba(255,75,75,0.2)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("\U0001f4f0 Latest economic headlines")
    news_df = load_news()
    if not news_df.empty:
        scored_df, _ = score_news_feed(news_df)
        econ = scored_df[scored_df["is_economic"] == True].head(5)
        for _, row in econ.iterrows():
            emoji = get_sentiment_emoji(row.get("sentiment", "neutral"))
            st.markdown(f"{emoji} **[{row['source']}]** [{row['title']}]({row['link']})")
    else:
        st.warning("News feed not available.")


# ════════════════════════════════════════════════════════════════
# EXCHANGE RATES
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b1 Exchange Rates":
    st.title("Exchange Rates — MWK")
    forex = load_forex()
    wb = load_wb()
    fx_rate = forex.get("rate")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Live rate", f"1 USD = {fx_rate:,.2f} MWK" if fx_rate else "N/A", "Live")
    with col2:
        st.metric("Source", forex.get("source", "N/A"), str(forex.get("timestamp",""))[:25])
    st.markdown("---")
    fx_df = wb.get("Exchange rate MWK per USD")
    if fx_df is not None and not fx_df.empty:
        fig = px.line(fx_df, x="year", y="value",
            title="MWK per USD — Annual average (World Bank)",
            labels={"year": "Year", "value": "MWK per 1 USD"}, markers=True)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        fig.update_traces(line_color="#F4C542", marker_color="#F4C542")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# INFLATION
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4c8 Inflation":
    st.title("Inflation Tracker")
    imf, imf_proj = load_imf()
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
            st.metric("Year", str(latest_yr), "IMF latest actual")
        with col3:
            status = "\U0001f534 Very high" if latest_val > 20 else "\U0001f7e1 Elevated" if latest_val > 10 else "\U0001f7e2 Moderate"
            st.metric("Status", status, "")
        st.markdown("---")
        fig = px.bar(inf_df, x="year", y="value",
            title="Malawi Inflation Rate — Actuals only (up to 2026)",
            labels={"year": "Year", "value": "Inflation %"},
            color="value", color_continuous_scale="RdYlGn_r")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.subheader("Raw data")
        st.dataframe(inf_df.sort_values("year", ascending=False).reset_index(drop=True), use_container_width=True)


# ════════════════════════════════════════════════════════════════
# FORECASTS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f52e Forecasts":
    try:
        from data.lstm_model import train_lstm, forecast_lstm
        LSTM_AVAILABLE = True
    except ImportError:
        LSTM_AVAILABLE = False
    from data.forecaster import forecast_indicator, build_forecast_chart_data
    st.title("Economic Forecasts")
    st.markdown("Our independent forecasts vs IMF projections — starting from 2027.")
    st.markdown("---")
    imf, imf_proj = load_imf()
    indicator = st.selectbox("Select indicator to forecast",
        ["Inflation Rate (%)", "GDP Growth (%)", "Government Debt (% GDP)", "Current Account (% GDP)"])
    steps = st.slider("Years ahead to forecast", 1, 10, 5)
    df = imf.get(indicator)
    if df is None or df.empty:
        st.error("No data available for this indicator.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("\U0001f7e2 Our ARIMA Forecast")
            st.caption("Statistical model trained on actuals only")
            with st.spinner("Running ARIMA..."):
                arima_result = forecast_indicator(df, steps=steps, indicator_name=indicator)
            if arima_result:
                st.metric(f"Forecast {arima_result['years'][0]}", f"{arima_result['forecast'][0]}%",
                    f"{arima_result['forecast'][0] - arima_result['last_actual_value']:+.2f}%")
                st.metric(f"Forecast {arima_result['years'][-1]}", f"{arima_result['forecast'][-1]}%", "")
        with col2:
            st.subheader("\U0001f9e0 Our LSTM Forecast")
            st.caption("Neural network trained on actuals only")
            if not LSTM_AVAILABLE:
                st.info("LSTM runs locally only.")
                lstm_result = None
                mae = None
            else:
                with st.spinner("Training LSTM... (30-60 seconds)"):
                    dataframes = {k: v for k, v in imf.items() if not v.empty and len(v) >= 8}
                    if indicator in dataframes:
                        model, scaler, history, mae = train_lstm(
                            dataframes=dataframes, target_key=indicator, lookback=5, epochs=100)
                        lstm_result = forecast_lstm(model=model, scaler=scaler,
                            dataframes=dataframes, target_key=indicator, steps=steps) if model else None
                    else:
                        lstm_result = None
                        mae = None
                if lstm_result:
                    st.metric(f"Forecast {lstm_result['years'][0]}", f"{lstm_result['forecast'][0]}%",
                        f"{lstm_result['forecast'][0] - lstm_result['last_actual_value']:+.2f}%")
                    st.metric(f"Forecast {lstm_result['years'][-1]}", f"{lstm_result['forecast'][-1]}%", "")
                    if mae: st.caption(f"Model accuracy (MAE): {mae:.4f}")
                else:
                    st.warning("LSTM could not generate forecast.")
                    lstm_result = None
        st.markdown("---")
        st.subheader("Our forecasts vs IMF projections")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["year"], y=df["value"], mode="lines+markers",
            name="Historical actuals", line=dict(color="#aaaaaa", width=2)))
        if arima_result:
            fig.add_trace(go.Scatter(x=arima_result["years"], y=arima_result["forecast"],
                mode="lines+markers", name="Our ARIMA", line=dict(color="#00C49F", width=2, dash="dash")))
        if lstm_result:
            fig.add_trace(go.Scatter(x=lstm_result["years"], y=lstm_result["forecast"],
                mode="lines+markers", name="Our LSTM", line=dict(color="#FF4B4B", width=2, dash="dot")))
        imf_line = imf_proj.get(indicator)
        if imf_line is not None and not imf_line.empty:
            fig.add_trace(go.Scatter(x=imf_line["year"], y=imf_line["value"],
                mode="lines+markers", name="IMF Projection", line=dict(color="#F4C542", width=2, dash="longdash")))
        fig.update_layout(title=f"{indicator} — Our Forecasts vs IMF Projections (from 2027)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", hovermode="x unified", legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        if arima_result:
            st.subheader("Year by year comparison")
            rows = []
            for i, yr in enumerate(arima_result["years"]):
                arima_val = arima_result["forecast"][i]
                lstm_val = lstm_result["forecast"][i] if lstm_result and i < len(lstm_result["forecast"]) else None
                imf_val = None
                if imf_line is not None:
                    imf_row = imf_line[imf_line["year"] == yr]
                    if not imf_row.empty: imf_val = round(float(imf_row.iloc[0]["value"]), 2)
                rows.append({"Year": yr, "Our ARIMA (%)": arima_val, "Our LSTM (%)": lstm_val, "IMF Projection (%)": imf_val})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.caption("Grey = history | Green = our ARIMA | Red = our LSTM | Yellow = IMF.")


# ════════════════════════════════════════════════════════════════
# INVESTMENT SIGNALS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b9 Investment Signals":
    st.title("Investment Signals")
    st.markdown("Rate-aware sector rotation — what to buy, hold or avoid right now.")
    st.markdown("---")
    imf, imf_proj = load_imf()
    forex = load_forex()
    news_df = load_news()
    inf_val, _ = get_current_value("Inflation Rate (%)", imf)
    gdp_val, _ = get_current_value("GDP Growth (%)", imf)
    debt_val, _ = get_current_value("Government Debt (% GDP)", imf)
    ca_val, _ = get_current_value("Current Account (% GDP)", imf)
    fx = forex.get("rate")
    _, sentiment_summary = score_news_feed(news_df)
    neg_pct = sentiment_summary["negative_pct"]
    rate_env = get_rate_environment()
    risk = calculate_devaluation_risk(
        inflation=inf_val, mwk_per_usd=fx,
        gdp_growth=gdp_val, government_debt=debt_val,
        current_account=ca_val, news_negative_pct=neg_pct)
    signals = generate_signals(
        inflation=inf_val, gdp_growth=gdp_val,
        government_debt=debt_val, current_account=ca_val,
        mwk_per_usd=fx, devaluation_score=risk["score"],
        rate_env=rate_env)
    # Rate environment banner
    phase = rate_env["cycle_phase"]
    pr = get_current_policy_rate()
    lending = rate_env["estimated_lending_rate"]
    real_r = round(lending - inf_val, 1) if inf_val else None
    if phase == "EARLY_EASING":
        st.success(f"\U0001f7e2 EARLY EASING — Policy rate cut to {pr['rate']}%. Buy bonds now. Equities expanding. Real lending rate: {real_r}%")
    elif phase == "TIGHTENING":
        st.error(f"\U0001f534 TIGHTENING — Rates rising. Cash and short-duration assets win.")
    elif phase == "PEAK":
        st.warning(f"\U0001f7e0 PEAK RATES — Watch for the pivot. Buy bonds before first cut.")
    else:
        st.info(f"\u26aa RATES ON HOLD — Policy rate {pr['rate']}%. No strong directional signal.")
    st.markdown("---")
    buy_count = sum(1 for s in signals if s["action"] == "BUY")
    hold_count = sum(1 for s in signals if s["action"] == "HOLD")
    avoid_count = sum(1 for s in signals if s["action"] == "AVOID")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("\U0001f7e2 BUY", buy_count)
    with col2: st.metric("\U0001f7e1 HOLD", hold_count)
    with col3: st.metric("\U0001f534 AVOID", avoid_count)
    with col4: st.metric("Devaluation risk", f"{risk['score']}/100", risk["level"])
    st.markdown("---")
    filter_action = st.radio("Filter by action", ["All", "BUY", "HOLD", "AVOID"], horizontal=True)
    filtered = signals if filter_action == "All" else [s for s in signals if s["action"] == filter_action]
    for s in filtered:
        action = s["action"]
        emoji = get_action_emoji(action)
        if action == "BUY":
            st.success(f"{emoji} **{action} — {s['emoji']} {s['asset']}**\n\n{s['reason']}\n\n*Confidence: {s['confidence']}*")
        elif action == "AVOID":
            st.error(f"{emoji} **{action} — {s['emoji']} {s['asset']}**\n\n{s['reason']}\n\n*Confidence: {s['confidence']}*")
        else:
            st.warning(f"{emoji} **{action} — {s['emoji']} {s['asset']}**\n\n{s['reason']}\n\n*Confidence: {s['confidence']}*")
    st.markdown("---")
    st.caption("Signals generated from IMF actuals, RBM rate cycle, live forex and news sentiment. Not financial advice.")

# ================================================================
# FOREX TRADING
# ================================================================
elif page == "\U0001f4b1 Forex Trading":
    from data.forex_collector import fetch_all_rates, get_depreciation_summary

    st.title("Forex Trading Terminal")
    st.markdown("---")

    # ── Live news ticker ─────────────────────────────────────────
    news_df = load_news()
    if not news_df.empty:
        scored_df, _ = score_news_feed(news_df)
        fx_keywords = ["kwacha", "forex", "currency", "dollar", "exchange rate",
            "devaluation", "depreciation", "reserve", "rbm", "import", "export",
            "trade", "rand", "pound", "euro", "inflation", "imf", "fuel price"]
        fx_news = scored_df[scored_df["title"].str.lower().str.contains(
            "|".join(fx_keywords), na=False)].head(15)
        if not fx_news.empty:
            ticker_items = " \u2022\u2022\u2022 ".join(
                [f"{row['title']}" for _, row in fx_news.iterrows()]
            )
            st.markdown("""
                <style>
                .ticker-wrap {
                    width: 100%;
                    background: #0d1117;
                    border-top: 2px solid #F4C542;
                    border-bottom: 2px solid #F4C542;
                    padding: 8px 0;
                    overflow: hidden;
                    margin-bottom: 16px;
                }
                .ticker {
                    display: inline-block;
                    white-space: nowrap;
                    animation: ticker-scroll 60s linear infinite;
                    color: #F4C542;
                    font-size: 14px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                @keyframes ticker-scroll {
                    0%   { transform: translateX(100vw); }
                    100% { transform: translateX(-100%); }
                }
                </style>
            """, unsafe_allow_html=True)
            st.markdown(
                f'<div class="ticker-wrap"><span class="ticker">\U0001f4f0 MARKET NEWS: {ticker_items}</span></div>',
                unsafe_allow_html=True)

    # ── Fetch live rates ─────────────────────────────────────────
    with st.spinner("Fetching live currency rates..."):
        rates = fetch_all_rates()

    if not rates:
        st.error("Could not fetch live rates. Check your connection.")
    else:
        analysis = get_depreciation_summary(rates)
        timestamp = rates.get("_timestamp", "")[:25]

        # ── Rate environment context ──────────────────────────────
        env = get_rate_environment()
        pr = get_current_policy_rate()
        imf, _ = load_imf()
        inf_val, _ = get_current_value("Inflation Rate (%)", imf)
        lending = pr["estimated_lending_rate"]
        real_rate = round(lending - inf_val, 1) if inf_val else None

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("MWK Policy Rate", f"{pr['rate']}%", env["cycle_phase"].replace("_"," "))
        with col2: st.metric("MWK Lending Rate", f"{lending}%", "+11pp over policy")
        with col3: st.metric("Real Rate (MWK)", f"{real_rate}%" if real_rate else "N/A", "Lending minus inflation")
        with col4: st.metric("Updated", timestamp[:16], rates.get("_source",""))

        st.markdown("---")

        # ── Currency performance table ────────────────────────────
        st.subheader("\U0001f4ca Currency Rankings vs MWK")
        st.markdown("Ranked by strength. The more MWK it takes to buy one unit — the stronger that currency.")

        rows = []
        for a in analysis:
            carry = a["carry_spread"]
            carry_str = f"+{carry:.1f}pp MWK advantage" if carry > 0 else f"{carry:.1f}pp foreign advantage"
            rows.append({
                "Currency": f"{a['flag']} {a['code']}",
                "Name": a["name"],
                "MWK per 1 unit": f"{a['mwk_per_unit']:,.2f}",
                "Foreign Rate %": a["country_rate"],
                "Carry Spread": carry_str,
                "Region": a["region"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.markdown("---")

        # ── Visual bar chart ─────────────────────────────────────
        st.subheader("MWK per 1 unit of each currency")
        codes  = [a["code"]          for a in analysis]
        values = [a["mwk_per_unit"]  for a in analysis]
        flags  = [a["flag"]          for a in analysis]
        labels = [f"{f} {c}" for f, c in zip(flags, codes)]

        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=["#FF4B4B" if v > 500 else "#F4C542" if v > 50 else "#00C49F" for v in values],
            text=[f"{v:,.0f}" for v in values],
            textposition="outside"
        ))
        fig.update_layout(
            title="MWK per 1 unit — Higher = stronger foreign currency",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", yaxis_title="MWK", height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── Carry trade analysis ──────────────────────────────────
        st.subheader("\U0001f9e0 Carry Trade Analysis")
        st.markdown(f"MWK lending rate is **{lending}%**. Compare against each country's rate. Wide positive spread = MWK is high-yielding but risky.")

        for a in analysis:
            carry = a["carry_spread"]
            code = a["code"]
            name = a["name"]
            flag = a["flag"]
            c_rate = a["country_rate"]
            mwk = a["mwk_per_unit"]

            if carry > 15:
                verdict = "\U0001f534 MWK massively higher-yielding but devaluation risk dominates. Avoid holding MWK long."
            elif carry > 8:
                verdict = "\U0001f7e0 MWK higher-yielding. But kwacha depreciation may eat the carry. Hedge required."
            elif carry > 0:
                verdict = "\U0001f7e1 Slight MWK yield advantage. Monitor depreciation pace."
            else:
                verdict = "\U0001f7e2 Foreign currency has yield advantage AND likely appreciating vs MWK. Strong hold candidate."

            with st.expander(f"{flag} {code} — {name} | Rate: {c_rate}% | MWK: {mwk:,.2f} | Spread: {carry:+.1f}pp"):
                st.markdown(verdict)
                st.markdown(f"**{code} central bank rate:** {c_rate}%")
                st.markdown(f"**MWK lending rate:** {lending}%")
                st.markdown(f"**Carry spread:** {carry:+.1f}pp (positive = MWK higher yielding)")
                st.markdown(f"**Current rate:** 1 {code} = {mwk:,.2f} MWK")

        st.markdown("---")

        # ── High conviction trade call ─────────────────────────────
        st.subheader("\U0001f3af The Trade — High Conviction Call")

        usd_data = rates.get("USD")
        usd_rate = usd_data["mwk_per_unit"] if usd_data else None

        # Devaluation risk
        news_df2 = load_news()
        _, sent = score_news_feed(news_df2)
        neg_pct = sent["negative_pct"]
        risk = calculate_devaluation_risk(
            inflation=inf_val, mwk_per_usd=usd_rate,
            gdp_growth=None, government_debt=None,
            current_account=None, news_negative_pct=neg_pct)

        dev_score = risk["score"]

        if dev_score >= 65 and inf_val and inf_val > 20:
            st.error("""
## \U0001f534 POSITION: LONG USD / SHORT MWK

**The setup:**
- Devaluation risk score: high
- MWK inflation running above 20% — purchasing power destruction
- RBM in early easing cycle — rate cuts reduce MWK yield advantage
- Current account deficit means more USD going out than coming in

**The trade:**
Convert MWK savings to USD now. Do not wait for the next cut.
Every RBM rate cut narrows the spread. The kwacha will follow the rate.

**Risk:**
RBM intervention could temporarily support MWK.
Strong tobacco season could bring USD inflows.

**Sizing:**
60-70% of liquid savings in USD. Keep 30% in MWK T-bills for yield.
            """)
        elif dev_score >= 45:
            st.warning("""
## \U0001f7e0 POSITION: DIVERSIFY INTO USD AND ZAR

**The setup:**
- Moderate devaluation risk
- Early easing cycle — watch for acceleration in rate cuts

**The trade:**
Hold 40% USD, 20% ZAR (regional liquidity), 40% MWK T-bills.
ZAR gives you regional exposure with better liquidity than other SADC currencies.

**Risk:**
ZAR itself volatile — South Africa political risk.
            """)
        else:
            st.success("""
## \U0001f7e2 POSITION: HOLD MWK T-BILLS — WAIT FOR CLARITY

**The setup:**
- Devaluation risk manageable
- MWK T-bills at 28%+ yield

**The trade:**
Stay in 364-day T-bills. Collect the yield. Reassess after next MPC.
            """)

        st.markdown("---")

        # ── Currency-affecting news ───────────────────────────────
        st.subheader("\U0001f4f0 News affecting these currencies")
        if not news_df.empty:
            if not fx_news.empty:
                for _, row in fx_news.iterrows():
                    emoji = get_sentiment_emoji(row.get("sentiment", "neutral"))
                    st.markdown(f"{emoji} **[{row['source']}]** [{row['title']}]({row['link']})")
                    st.caption(str(row["date"])[:25])
                    st.markdown("---")
            else:
                st.info("No currency-specific headlines right now.")

        st.caption("Rates from open.er-api.com. Carry analysis uses RBM lending rate vs counterpart central bank rates. Not financial advice.")


# ════════════════════════════════════════════════════════════════
# POLICY RATE
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f3e6 Policy Rate":
    st.title("RBM Policy Rate")
    st.markdown("Reserve Bank of Malawi — Monetary Policy Committee decisions and rate cycle.")
    st.markdown("---")
    pr = get_current_policy_rate()
    env = get_rate_environment()
    hist = get_policy_rate_history()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Policy Rate", f"{pr['rate']}%", f"{pr['change']:+.1f}pp — {pr['decision']}")
    with col2:
        st.metric("Lombard Rate", f"{pr['lombard_rate']}%", "Policy + 0.2pp")
    with col3:
        st.metric("Cycle Phase", env["cycle_phase"].replace("_", " "),
            f"{env['streak']} consecutive {env['direction']} decision(s)")
    with col4:
        st.metric("Below Peak", f"{env['below_peak_by']}pp", f"Peak was {env['peak_rate']}%")
    st.markdown("---")
    phase = env["cycle_phase"]
    if phase == "EARLY_EASING":
        st.success("\U0001f7e2 EARLY EASING — RBM has begun cutting rates. Bonds benefit first, then equities. Rate cuts reduce the cost of capital — valuations expand.")
    elif phase == "DEEP_EASING":
        st.success("\U0001f7e2 DEEP EASING — Multiple cuts underway. Strong signal for equities and long-duration bonds.")
    elif phase == "TIGHTENING":
        st.error("\U0001f534 TIGHTENING — RBM is raising rates. Cash and short-duration assets win. Avoid leveraged positions.")
    elif phase == "PEAK":
        st.warning("\U0001f7e0 PEAK — Rates at maximum. Watch for the pivot. Bonds are attractive here.")
    else:
        st.info("\u26aa PLATEAU — Rates on hold. No strong directional signal.")
    st.markdown("---")
    st.subheader("MPC Decision History — 2022 to 2026")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["rate"],
        mode="lines+markers", name="Policy Rate",
        line=dict(color="#F4C542", width=3),
        marker=dict(size=10, color=[
            "#FF4B4B" if c > 0 else "#00C49F" if c < 0 else "#aaaaaa"
            for c in hist["change"]
        ])
    ))
    fig.update_layout(title="RBM Policy Rate — MPC Decisions",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", yaxis_title="Rate (%)", hovermode="x unified", height=400)
    fig.add_hline(y=pr["rate"], line_dash="dash", line_color="white",
        annotation_text=f"Current: {pr['rate']}%", annotation_font_color="white")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("MPC Decision Log")
    display = hist[["date", "rate", "change", "decision", "note"]].copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display["change"] = display["change"].apply(lambda x: f"{x:+.1f}pp" if x != 0 else "Hold")
    display.columns = ["Date", "Rate (%)", "Change", "Decision", "Note"]
    st.dataframe(display.sort_values("Date", ascending=False).reset_index(drop=True), use_container_width=True)
    st.markdown("---")
    st.caption("Source: RBM MPC press statements. Red dots = hikes. Green dots = cuts. Grey = hold.")


# ════════════════════════════════════════════════════════════════
# INTEREST RATES
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b3 Interest Rates":
    st.title("Interest Rate Transmission")
    st.markdown("How the RBM policy rate flows through to lending, bonds and sector performance.")
    st.markdown("---")
    imf, imf_proj = load_imf()
    pr = get_current_policy_rate()
    env = get_rate_environment()
    inf_val, _ = get_current_value("Inflation Rate (%)", imf)
    policy_rate  = pr["rate"]
    lombard      = pr["lombard_rate"]
    lending_rate = pr["estimated_lending_rate"]
    real_rate    = round(lending_rate - inf_val, 1) if inf_val else None
    tbills       = env["tbill_rates"]
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Policy Rate", f"{policy_rate}%", "RBM sets this")
    with col2: st.metric("Lombard Rate", f"{lombard}%", "+0.2pp above policy")
    with col3: st.metric("T-Bill 91-day", f"{tbills['91-day']['rate']}%", "Risk-free benchmark")
    with col4: st.metric("Est. Lending Rate", f"{lending_rate}%", "+11pp spread over policy")
    with col5:
        if real_rate:
            st.metric("Real Lending Rate", f"{real_rate}%", f"Lending minus {inf_val}% inflation")
    st.markdown("---")
    st.subheader("Rate flow diagram")
    rates  = [policy_rate, lombard, tbills["91-day"]["rate"], tbills["182-day"]["rate"], tbills["364-day"]["rate"], lending_rate]
    labels = ["Policy Rate", "Lombard Rate", "T-Bill 91d", "T-Bill 182d", "T-Bill 364d", "Est. Lending Rate"]
    colors = ["#F4C542", "#F4C542", "#00C49F", "#00C49F", "#00C49F", "#FF4B4B"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=rates, marker_color=colors,
        text=[f"{r}%" for r in rates], textposition="outside"))
    if inf_val:
        fig.add_hline(y=inf_val, line_dash="dash", line_color="white",
            annotation_text=f"Inflation: {inf_val}%", annotation_font_color="white")
    fig.update_layout(title="Interest Rate Structure — Malawi (current)",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", yaxis_title="Rate (%)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("What this means for each sector")
    if real_rate:
        st.markdown(f"**Real lending rate: {real_rate}%** (lending {lending_rate}% minus inflation {inf_val}%)")
        st.markdown("---")
    sectors = [
        ("\U0001f4dc Government Bonds", "FAVOURABLE" if env["cycle_phase"] in ["EARLY_EASING","DEEP_EASING"] else "NEUTRAL",
         f"T-bill 364-day at {tbills['364-day']['rate']}%. In easing cycle — lock in high yields before rates fall further. Bond prices rise as rates fall." if env["cycle_phase"] in ["EARLY_EASING","DEEP_EASING"] else f"T-bill yields above inflation only if rate exceeds {inf_val}%."),
        ("\U0001f3e6 Commercial Banks", "FAVOURABLE",
         f"Banks borrow near policy rate ({policy_rate}%) and lend at ~{lending_rate}%. Spread of ~{lending_rate - policy_rate}pp = strong net interest income."),
        ("\U0001f3e0 Real Estate", "NEUTRAL",
         f"Nominal values rising with {inf_val}% inflation. Leveraged buyers pay {lending_rate}% on mortgages. Cash buyers: favourable. Debt buyers: expensive."),
        ("\U0001f33d Agriculture", "FAVOURABLE",
         "Insulated from rate cycle. Returns driven by rainfall, commodity prices and forex earnings. No debt dependency."),
        ("\U0001f3ed Manufacturing", "UNFAVOURABLE",
         f"Capital-intensive sectors pay ~{lending_rate}% to borrow. Real rate of {real_rate}% means borrowing costs exceed returns in most cases. Avoid until lending falls below 25%."),
        ("\U0001f4c8 MSE Equities", "FAVOURABLE" if env["cycle_phase"] == "EARLY_EASING" else "NEUTRAL",
         "Early easing: buy low-debt, cash-rich equities. Rate cuts lower discount rates — valuations expand. Avoid leveraged companies." if env["cycle_phase"] == "EARLY_EASING" else "Mixed. Be selective."),
    ]
    for sector, status, explanation in sectors:
        if status == "FAVOURABLE": st.success(f"\U0001f7e2 **{sector}** — {explanation}")
        elif status == "UNFAVOURABLE": st.error(f"\U0001f534 **{sector}** — {explanation}")
        else: st.info(f"\u26aa **{sector}** — {explanation}")
    st.markdown("---")
    st.caption("Lending rate estimated from policy rate + historical spread. Source: RBM MPC press statements.")


# ════════════════════════════════════════════════════════════════
# MACRO INDICATORS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f3e6 Macro Indicators":
    st.title("Macro Indicators — Malawi")
    imf, imf_proj = load_imf()
    wb = load_wb()
    all_data = {**wb, **imf}
    if not all_data:
        st.error("Could not load data.")
    else:
        indicator = st.selectbox("Select indicator", list(all_data.keys()))
        df = all_data[indicator]
        latest = df.iloc[-1]
        st.metric(indicator, f"{latest['value']:.2f}", f"Latest actual: {int(latest['year'])}")
        fig = px.line(df, x="year", y="value",
            title=f"{indicator} — Malawi (actuals only)",
            labels={"year": "Year", "value": indicator}, markers=True)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
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
        scored_df, summary = score_news_feed(news_df)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total headlines", summary["total"])
        with col2: st.metric("\U0001f7e2 Positive", f"{summary['positive_pct']}%")
        with col3: st.metric("\U0001f534 Negative", f"{summary['negative_pct']}%")
        with col4:
            score = summary["avg_score"]
            mood = "Bearish \U0001f4c9" if score < -0.1 else "Bullish \U0001f4c8" if score > 0.1 else "Neutral \u26aa"
            st.metric("Market mood", mood, f"Score: {score}")
        st.markdown("---")
        fig = go.Figure(go.Bar(
            x=["Positive", "Neutral", "Negative"],
            y=[summary["positive_pct"], summary["neutral_pct"], summary["negative_pct"]],
            marker_color=["#1a472a", "#7d6608", "#641e16"]))
        fig.update_layout(title="News sentiment breakdown (%)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", height=250)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["\U0001f534 Negative", "\U0001f7e2 Positive", "\U0001f4f0 All"])
        with tab1:
            neg = scored_df[scored_df["sentiment"] == "negative"]
            if neg.empty: st.info("No negative headlines right now.")
            else:
                for _, row in neg.iterrows():
                    st.markdown(f"\U0001f534 **[{row['source']}]** [{row['title']}]({row['link']})")
                    st.caption(str(row["date"])[:25])
                    st.markdown("---")
        with tab2:
            pos = scored_df[scored_df["sentiment"] == "positive"]
            if pos.empty: st.info("No positive headlines right now.")
            else:
                for _, row in pos.iterrows():
                    st.markdown(f"\U0001f7e2 **[{row['source']}]** [{row['title']}]({row['link']})")
                    st.caption(str(row["date"])[:25])
                    st.markdown("---")
        with tab3:
            for _, row in scored_df.iterrows():
                emoji = get_sentiment_emoji(row["sentiment"])
                st.markdown(f"{emoji} **[{row['source']}]** [{row['title']}]({row['link']})")
                st.caption(f"{str(row['date'])[:25]} | Score: {row['sentiment_score']}")
                st.markdown("---")


# ════════════════════════════════════════════════════════════════
# RISK SIGNALS
# ════════════════════════════════════════════════════════════════
elif page == "\u26a0\ufe0f Risk Signals":
    st.title("Economic Risk Signals")
    st.markdown("---")
    imf, imf_proj = load_imf()
    forex = load_forex()
    news_df = load_news()
    inf_val, _ = get_current_value("Inflation Rate (%)", imf)
    gdp_val, _ = get_current_value("GDP Growth (%)", imf)
    debt_val, _ = get_current_value("Government Debt (% GDP)", imf)
    ca_val, _ = get_current_value("Current Account (% GDP)", imf)
    fx = forex.get("rate")
    _, sentiment_summary = score_news_feed(news_df)
    neg_pct = sentiment_summary["negative_pct"]
    risk = calculate_devaluation_risk(
        inflation=inf_val, mwk_per_usd=fx,
        gdp_growth=gdp_val, government_debt=debt_val,
        current_account=ca_val, news_negative_pct=neg_pct)
    score = risk["score"]
    level = risk["level"]
    message = risk["message"]
    st.subheader("Kwacha Devaluation Risk Score")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Risk Score", f"{score} / 100", get_risk_label(score))
        if level == "CRITICAL": st.error(f"\U0001f534 {level} — {message}")
        elif level == "HIGH": st.warning(f"\U0001f7e0 {level} — {message}")
        elif level == "MODERATE": st.info(f"\U0001f7e1 {level} — {message}")
        else: st.success(f"\U0001f7e2 {level} — {message}")
    with col2:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=score,
            title={"text": "Devaluation Risk", "font": {"color": "white"}},
            gauge={"axis": {"range": [0,100], "tickcolor": "white"}, "bar": {"color": "white"},
                "steps": [{"range": [0,35], "color": "#1a472a"}, {"range": [35,55], "color": "#7d6608"},
                    {"range": [55,75], "color": "#784212"}, {"range": [75,100], "color": "#641e16"}],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": score}}))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("Individual signals")
    signals = []
    if inf_val:
        if inf_val > 25: signals.append(("\U0001f534 CRITICAL", "Inflation", f"{inf_val}% — Severely above target."))
        elif inf_val > 15: signals.append(("\U0001f7e0 HIGH", "Inflation", f"{inf_val}% — Well above target."))
        else: signals.append(("\U0001f7e1 MODERATE", "Inflation", f"{inf_val}% — Elevated."))
    if gdp_val:
        if gdp_val < 0: signals.append(("\U0001f534 CRITICAL", "GDP Growth", f"{gdp_val}% — Economy contracting."))
        elif gdp_val < 2: signals.append(("\U0001f7e0 HIGH", "GDP Growth", f"{gdp_val}% — Very slow."))
        elif gdp_val < 4: signals.append(("\U0001f7e1 MODERATE", "GDP Growth", f"{gdp_val}% — Below potential."))
        else: signals.append(("\U0001f7e2 LOW", "GDP Growth", f"{gdp_val}% — Healthy."))
    if debt_val:
        if debt_val > 80: signals.append(("\U0001f534 CRITICAL", "Govt Debt", f"{debt_val}% of GDP — Crisis territory."))
        elif debt_val > 60: signals.append(("\U0001f7e0 HIGH", "Govt Debt", f"{debt_val}% of GDP — Above threshold."))
        else: signals.append(("\U0001f7e1 MODERATE", "Govt Debt", f"{debt_val}% of GDP — Watch closely."))
    if fx:
        if fx > 1700: signals.append(("\U0001f534 CRITICAL", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Severe depreciation."))
        elif fx > 1200: signals.append(("\U0001f7e0 HIGH", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Significant weakness."))
        else: signals.append(("\U0001f7e2 LOW", "MWK/USD", f"1 USD = {fx:,.0f} MWK — Relatively stable."))
    if neg_pct > 50: signals.append(("\U0001f7e0 HIGH", "News Sentiment", f"{neg_pct}% negative headlines — Bearish."))
    elif neg_pct > 30: signals.append(("\U0001f7e1 MODERATE", "News Sentiment", f"{neg_pct}% negative — Cautious."))
    else: signals.append(("\U0001f7e2 LOW", "News Sentiment", f"{neg_pct}% negative — Relatively calm."))
    for level, category, message in signals:
        if "CRITICAL" in level: st.error(f"{level} | **{category}** — {message}")
        elif "HIGH" in level: st.warning(f"{level} | **{category}** — {message}")
        elif "MODERATE" in level: st.info(f"{level} | **{category}** — {message}")
        else: st.success(f"{level} | **{category}** — {message}")
    st.markdown("---")
    st.subheader("Component breakdown")
    for name, data in risk["components"].items():
        s = data["score"]
        w = data["weight"]
        st.markdown(f"**{name}** — Score: {s}/100 | Weight: {int(w*100)}% | Contribution: {round(s*w,1)}")
        st.progress(s / 100)
    st.markdown("---")
    st.caption("Score combines inflation, exchange rate, GDP, debt, current account and news sentiment.")


# ════════════════════════════════════════════════════════════════
# ALERTS & SUBSCRIBE
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f514 Alerts & Subscribe":
    from data.alert_scheduler import run_alert_check
    st.title("Alerts & Subscribe")
    st.markdown("Get notified by email when economic thresholds are breached.")
    st.markdown("---")
    imf, imf_proj = load_imf()
    forex = load_forex()
    news_df = load_news()
    inf_val, _ = get_current_value("Inflation Rate (%)", imf)
    gdp_val, _ = get_current_value("GDP Growth (%)", imf)
    debt_val, _ = get_current_value("Government Debt (% GDP)", imf)
    ca_val, _ = get_current_value("Current Account (% GDP)", imf)
    fx = forex.get("rate")
    _, sentiment_summary = score_news_feed(news_df)
    neg_pct = sentiment_summary["negative_pct"]
    risk = calculate_devaluation_risk(
        inflation=inf_val, mwk_per_usd=fx,
        gdp_growth=gdp_val, government_debt=debt_val,
        current_account=ca_val, news_negative_pct=neg_pct)
    st.subheader("Current status")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Devaluation risk", f"{risk['score']}/100", risk["level"])
    with col2: st.metric("Inflation", f"{inf_val}%" if inf_val else "N/A")
    with col3: st.metric("MWK/USD", f"{fx:,.0f}" if fx else "N/A")
    st.markdown("---")
    st.subheader("Alert thresholds")
    thresholds = [
        ("Devaluation Risk Score", 75, risk["score"], "/100"),
        ("Inflation Rate", 30, inf_val, "%"),
        ("MWK/USD Rate", 1800, fx, " MWK"),
        ("Government Debt", 80, debt_val, "% of GDP"),
    ]
    for label, threshold, current, unit in thresholds:
        if current:
            breached = (current >= threshold)
            status = "\U0001f534 BREACHED" if breached else "\U0001f7e2 OK"
            st.markdown(f"**{label}**: Current {current:,.1f}{unit} | Alert at {threshold}{unit} | {status}")
            st.progress(min(current / threshold, 1.0))
    st.markdown("---")
    st.subheader("\U0001f4e7 Subscribe to alerts")
    with st.form("alert_form"):
        email_input = st.text_input("Your email address", placeholder="yourname@gmail.com")
        submitted = st.form_submit_button("Subscribe & Check Now")
        if submitted:
            if not email_input or "@" not in email_input:
                st.error("Please enter a valid email address.")
            else:
                with st.spinner("Checking thresholds..."):
                    result = run_alert_check(
                        risk_score=risk["score"], inflation=inf_val,
                        mwk_per_usd=fx, gdp_growth=gdp_val,
                        government_debt=debt_val, recipient_email=email_input)
                if result["status"] == "sent":
                    st.success(f"\U0001f4e7 Alert sent to {email_input}!")
                elif result["status"] == "ok":
                    st.info(f"\U0001f7e2 No thresholds breached. We will alert {email_input} when conditions change.")
                else:
                    st.warning(result["message"])
    st.markdown("---")
    st.caption("Alerts sent automatically every 6 hours when thresholds are breached.")
