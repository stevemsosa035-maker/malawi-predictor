"""
Email alert system for Malawi Economic Predictor.
Sends alerts when economic thresholds are breached.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL    = os.getenv("ALERT_SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("ALERT_SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("ALERT_RECIPIENT_EMAIL")

# Thresholds that trigger alerts
THRESHOLDS = {
    "devaluation_risk":  {"trigger": 75, "label": "Devaluation Risk"},
    "inflation":         {"trigger": 30, "label": "Inflation Rate"},
    "mwk_per_usd":       {"trigger": 1800, "label": "MWK/USD Exchange Rate"},
    "gdp_growth":        {"trigger": 0, "label": "GDP Growth"},
    "government_debt":   {"trigger": 80, "label": "Government Debt"},
}


def send_email(subject, body_html):
    """
    Send an HTML email alert.
    Returns True if sent successfully.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = RECIPIENT_EMAIL

        part = MIMEText(body_html, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

        print(f"Alert sent to {RECIPIENT_EMAIL}")
        return True

    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False


def build_alert_email(triggered_alerts, risk_score, indicators):
    """
    Build a clean HTML email with all triggered alerts.
    """
    now = datetime.now().strftime("%d %B %Y, %H:%M")

    rows = ""
    for alert in triggered_alerts:
        color = "#641e16" if alert["severity"] == "CRITICAL" else "#784212"
        rows += f"""
        <tr>
            <td style="padding:10px; background:{color}; color:white; border-radius:4px;">
                <strong>{alert["label"]}</strong><br>
                {alert["message"]}
            </td>
        </tr>
        <tr><td style="height:8px;"></td></tr>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif; background:#1a1a2e; color:white; padding:20px;">
        <h2 style="color:#FF4B4B;">🇲🇼 Malawi Economic Predictor — Alert</h2>
        <p style="color:#aaa;">{now}</p>
        <hr style="border-color:#444;">
        <h3>Devaluation Risk Score: {risk_score} / 100</h3>
        <h3>The following thresholds have been breached:</h3>
        <table width="100%" cellpadding="0" cellspacing="0">
        {rows}
        </table>
        <hr style="border-color:#444; margin-top:20px;">
        <h3>Current indicators:</h3>
        <ul>
            <li>Inflation: {indicators.get("inflation", "N/A")}%</li>
            <li>MWK/USD: {indicators.get("mwk_per_usd", "N/A"):,.0f} if isinstance(indicators.get("mwk_per_usd"), float) else indicators.get("mwk_per_usd", "N/A")</li>
            <li>GDP Growth: {indicators.get("gdp_growth", "N/A")}%</li>
            <li>Govt Debt: {indicators.get("government_debt", "N/A")}% of GDP</li>
        </ul>
        <p style="color:#aaa; font-size:12px;">
            View full analysis at malawi-predictor.streamlit.app<br>
            This is an automated alert from Malawi Economic Predictor.
        </p>
    </body></html>
    """
    return html


def check_and_send_alerts(
    risk_score=None,
    inflation=None,
    mwk_per_usd=None,
    gdp_growth=None,
    government_debt=None,
):
    """
    Check all thresholds and send an alert email
    if any are breached.
    Returns list of triggered alerts.
    """
    triggered = []

    if risk_score and risk_score >= THRESHOLDS["devaluation_risk"]["trigger"]:
        triggered.append({
            "label": "Devaluation Risk Score",
            "message": f"Score is {risk_score}/100 — above the critical threshold of {THRESHOLDS['devaluation_risk']['trigger']}.",
            "severity": "CRITICAL"
        })

    if inflation and inflation >= THRESHOLDS["inflation"]["trigger"]:
        triggered.append({
            "label": "Inflation Rate",
            "message": f"Inflation at {inflation}% — above the alert threshold of {THRESHOLDS['inflation']['trigger']}%.",
            "severity": "CRITICAL"
        })

    if mwk_per_usd and mwk_per_usd >= THRESHOLDS["mwk_per_usd"]["trigger"]:
        triggered.append({
            "label": "MWK/USD Exchange Rate",
            "message": f"Rate at {mwk_per_usd:,.0f} MWK per USD — above alert threshold of {THRESHOLDS['mwk_per_usd']['trigger']:,.0f}.",
            "severity": "CRITICAL"
        })

    if gdp_growth is not None and gdp_growth <= THRESHOLDS["gdp_growth"]["trigger"]:
        triggered.append({
            "label": "GDP Growth",
            "message": f"GDP growth at {gdp_growth}% — economy is contracting or stagnant.",
            "severity": "HIGH"
        })

    if government_debt and government_debt >= THRESHOLDS["government_debt"]["trigger"]:
        triggered.append({
            "label": "Government Debt",
            "message": f"Debt at {government_debt}% of GDP — above the {THRESHOLDS['government_debt']['trigger']}% danger threshold.",
            "severity": "HIGH"
        })

    if triggered:
        indicators = {
            "inflation": inflation,
            "mwk_per_usd": mwk_per_usd,
            "gdp_growth": gdp_growth,
            "government_debt": government_debt,
        }
        subject = f"🚨 Malawi Economic Alert — {len(triggered)} threshold(s) breached"
        body = build_alert_email(triggered, risk_score, indicators)
        send_email(subject, body)
    else:
        print("No thresholds breached. No alert sent.")

    return triggered


if __name__ == "__main__":
    print("Testing alert system...")
    print("")

    import sys, os as _os
    sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from data.imf_collector import fetch_all, get_current_value
    from data.forex_collector import fetch_latest_rate
    from data.news_collector import fetch_all_news
    from data.sentiment_scorer import score_news_feed
    from data.devaluation_risk import calculate_devaluation_risk

    imf   = fetch_all()
    forex = fetch_latest_rate()
    news  = fetch_all_news()
    _, sentiment = score_news_feed(news)

    inflation, _ = get_current_value("Inflation Rate (%)", imf)
    gdp, _       = get_current_value("GDP Growth (%)", imf)
    debt, _      = get_current_value("Government Debt (% GDP)", imf)
    ca, _        = get_current_value("Current Account (% GDP)", imf)
    fx           = forex.get("rate")

    risk = calculate_devaluation_risk(
        inflation=inflation, mwk_per_usd=fx,
        gdp_growth=gdp, government_debt=debt,
        current_account=ca,
        news_negative_pct=sentiment["negative_pct"]
    )

    print(f"Risk score: {risk['score']}")
    print(f"Inflation: {inflation}%")
    print(f"MWK/USD: {fx}")
    print("")
    print("Checking thresholds and sending alert if needed...")
    print("")

    triggered = check_and_send_alerts(
        risk_score=risk["score"],
        inflation=inflation,
        mwk_per_usd=fx,
        gdp_growth=gdp,
        government_debt=debt,
    )

    if triggered:
        print(f"Alert sent for {len(triggered)} breached threshold(s).")
    else:
        print("All indicators within safe limits.")
