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
        "\U0001f3e6 Macro Indicators",
        "\U0001f4f0 News & Sentiment",
        "\u26a0\ufe0f Risk Signals",
        "\U0001f514 Alerts & Subscribe",
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("IMF · World Bank · RBM · Live news")


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
    st.markdown("Live data — IMF · World Bank · RBM · Malawi news")
    st.markdown("---")
    imf, imf_proj = load_imf()
    forex = load_forex()
    col1, col2, col3, col4 = st.columns(4)
    inf_val, inf_yr = get_current_value("Inflation Rate (%)", imf)
    with col1:
        st.metric("\U0001f525 Inflation", f"{inf_val}%" if inf_val else "N/A", f"IMF {inf_yr}" if inf_yr else "")
    gdp_val, gdp_yr = get_current_value("GDP Growth (%)", imf)
    with col2:
        st.metric("\U0001f4c8 GDP Growth", f"{gdp_val}%" if gdp_val else "N/A", f"IMF {gdp_yr}" if gdp_yr else "")
    debt_val, debt_yr = get_current_value("Government Debt (% GDP)", imf)
    with col3:
        st.metric("\U0001f3e6 Govt Debt", f"{debt_val}%" if debt_val else "N/A", f"IMF {debt_yr}" if debt_yr else "")
    fx = forex.get("rate")
    with col4:
        st.metric("\U0001f4b1 MWK/USD", f"{fx:,.0f}" if fx else "N/A", "Live rate")
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
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("\U0001f7e2 Our ARIMA Forecast")
            st.caption("Statistical model trained on actuals only — independent of IMF")
            with st.spinner("Running ARIMA..."):
                arima_result = forecast_indicator(df, steps=steps, indicator_name=indicator)
            if arima_result:
                st.metric(f"Forecast {arima_result['years'][0]}", f"{arima_result['forecast'][0]}%",
                    f"{arima_result['forecast'][0] - arima_result['last_actual_value']:+.2f}%")
                st.metric(f"Forecast {arima_result['years'][-1]}", f"{arima_result['forecast'][-1]}%", "")
            else:
                st.warning("ARIMA could not generate forecast.")

        with col2:
            st.subheader("\U0001f9e0 Our LSTM Forecast")
            st.caption("Neural network trained on actuals only — independent of IMF")
            if not LSTM_AVAILABLE:
                st.info("LSTM runs locally only. Open app on your laptop to see full comparison.")
                lstm_result = None
                mae = None
            else:
                with st.spinner("Training LSTM... (30-60 seconds)"):
                    dataframes = {k: v for k, v in imf.items() if not v.empty and len(v) >= 8}
                    if indicator in dataframes:
                        model, scaler, history, mae = train_lstm(
                            dataframes=dataframes, target_key=indicator,
                            lookback=5, epochs=100)
                        lstm_result = forecast_lstm(model=model, scaler=scaler,
                            dataframes=dataframes, target_key=indicator, steps=steps) if model else None
                    else:
                        lstm_result = None
                        mae = None
                if lstm_result:
                    st.metric(f"Forecast {lstm_result['years'][0]}", f"{lstm_result['forecast'][0]}%",
                        f"{lstm_result['forecast'][0] - lstm_result['last_actual_value']:+.2f}%")
                    st.metric(f"Forecast {lstm_result['years'][-1]}", f"{lstm_result['forecast'][-1]}%", "")
                    if mae:
                        st.caption(f"Model accuracy (MAE): {mae:.4f}")
                else:
                    st.warning("LSTM could not generate forecast.")
                    lstm_result = None

        st.markdown("---")
        st.subheader("Our forecasts vs IMF projections")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["year"], y=df["value"],
            mode="lines+markers", name="Historical actuals",
            line=dict(color="#aaaaaa", width=2)))
        if arima_result:
            fig.add_trace(go.Scatter(x=arima_result["years"], y=arima_result["forecast"],
                mode="lines+markers", name="Our ARIMA",
                line=dict(color="#00C49F", width=2, dash="dash")))
        if lstm_result:
            fig.add_trace(go.Scatter(x=lstm_result["years"], y=lstm_result["forecast"],
                mode="lines+markers", name="Our LSTM",
                line=dict(color="#FF4B4B", width=2, dash="dot")))
        imf_line = imf_proj.get(indicator)
        if imf_line is not None and not imf_line.empty:
            fig.add_trace(go.Scatter(x=imf_line["year"], y=imf_line["value"],
                mode="lines+markers", name="IMF Projection",
                line=dict(color="#F4C542", width=2, dash="longdash")))
        fig.update_layout(
            title=f"{indicator} — Our Forecasts vs IMF Projections (from 2027)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", hovermode="x unified",
            legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        if arima_result:
            st.subheader("Year by year comparison")
            rows = []
            imf_line = imf_proj.get(indicator)
            for i, yr in enumerate(arima_result["years"]):
                arima_val = arima_result["forecast"][i]
                lstm_val = lstm_result["forecast"][i] if lstm_result and i < len(lstm_result["forecast"]) else None
                imf_val = None
                if imf_line is not None:
                    imf_row = imf_line[imf_line["year"] == yr]
                    if not imf_row.empty:
                        imf_val = round(float(imf_row.iloc[0]["value"]), 2)
                rows.append({"Year": yr, "Our ARIMA (%)": arima_val,
                    "Our LSTM (%)": lstm_val, "IMF Projection (%)": imf_val})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.caption("Grey = history | Green = our ARIMA | Red = our LSTM | Yellow = IMF. All forecasts start from 2027.")


# ════════════════════════════════════════════════════════════════
# INVESTMENT SIGNALS
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f4b9 Investment Signals":
    st.title("Investment Signals")
    st.markdown("What to do with your money based on current Malawi economic conditions.")
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
    signals = generate_signals(
        inflation=inf_val, gdp_growth=gdp_val,
        government_debt=debt_val, current_account=ca_val,
        mwk_per_usd=fx, devaluation_score=risk["score"])
    buy_count = sum(1 for s in signals if s["action"] == "BUY")
    hold_count = sum(1 for s in signals if s["action"] == "HOLD")
    avoid_count = sum(1 for s in signals if s["action"] == "AVOID")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("\U0001f7e2 BUY signals", buy_count)
    with col2: st.metric("\U0001f7e1 HOLD signals", hold_count)
    with col3: st.metric("\U0001f534 AVOID signals", avoid_count)
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
    st.caption("Signals generated from IMF actuals, live forex and news sentiment. Not financial advice.")


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
        label = get_risk_label(score)
        st.metric("Risk Score", f"{score} / 100", label)
        if level == "CRITICAL": st.error(f"\U0001f534 {level} — {message}")
        elif level == "HIGH": st.warning(f"\U0001f7e0 {level} — {message}")
        elif level == "MODERATE": st.info(f"\U0001f7e1 {level} — {message}")
        else: st.success(f"\U0001f7e2 {level} — {message}")
    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            title={"text": "Devaluation Risk", "font": {"color": "white"}},
            gauge={"axis": {"range": [0, 100], "tickcolor": "white"},
                "bar": {"color": "white"},
                "steps": [
                    {"range": [0, 35], "color": "#1a472a"},
                    {"range": [35, 55], "color": "#7d6608"},
                    {"range": [55, 75], "color": "#784212"},
                    {"range": [75, 100], "color": "#641e16"}],
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
    elif neg_pct > 30: signals.append(("\U0001f7e1 MODERATE", "News Sentiment", f"{neg_pct}% negative headlines — Cautious."))
    else: signals.append(("\U0001f7e2 LOW", "News Sentiment", f"{neg_pct}% negative headlines — Calm."))
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
        contribution = round(s * w, 1)
        label = get_risk_label(s)
        st.markdown(f"**{name}** — Score: {s}/100 | Weight: {int(w*100)}% | Contribution: {contribution}")
        st.progress(s / 100)
    st.markdown("---")
    st.caption("Score combines inflation, exchange rate, GDP, debt, current account and live news sentiment.")


# ════════════════════════════════════════════════════════════════
# ALERTS & SUBSCRIBE
# ════════════════════════════════════════════════════════════════
elif page == "\U0001f514 Alerts & Subscribe":
    from data.sentiment_scorer import score_news_feed
    from data.devaluation_risk import calculate_devaluation_risk, get_risk_label
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
    st.markdown("Enter your email to receive alerts when thresholds are breached.")
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
