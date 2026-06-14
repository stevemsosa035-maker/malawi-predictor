"""
Alert scheduler for Malawi Economic Predictor.
Runs threshold checks and sends alerts automatically.
Called from the Streamlit dashboard.
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

LAST_ALERT_FILE = "data/last_alert.json"
ALERT_COOLDOWN_HOURS = 6


def get_last_alert_time():
    """
    Read when the last alert was sent.
    Prevents spamming alerts every page load.
    """
    try:
        with open(LAST_ALERT_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_sent"])
    except:
        return None


def save_last_alert_time():
    """Save the current time as the last alert time."""
    with open(LAST_ALERT_FILE, "w") as f:
        json.dump({"last_sent": datetime.now().isoformat()}, f)


def should_send_alert():
    """
    Check if enough time has passed since last alert.
    Returns True if we should check and potentially send.
    """
    last = get_last_alert_time()
    if last is None:
        return True
    hours_since = (datetime.now() - last).total_seconds() / 3600
    return hours_since >= ALERT_COOLDOWN_HOURS


def run_alert_check(
    risk_score=None,
    inflation=None,
    mwk_per_usd=None,
    gdp_growth=None,
    government_debt=None,
    recipient_email=None,
):
    """
    Main function called from Streamlit.
    Checks thresholds and sends alert if needed.
    Returns dict with status and triggered alerts.
    """
    from data.alerts import check_and_send_alerts, THRESHOLDS

    if not should_send_alert():
        last = get_last_alert_time()
        hours_since = round((datetime.now() - last).total_seconds() / 3600, 1)
        return {
            "status": "cooldown",
            "message": f"Last alert sent {hours_since}h ago. Next check in {ALERT_COOLDOWN_HOURS - hours_since:.1f}h.",
            "triggered": []
        }

    # Override recipient if custom email provided
    if recipient_email:
        import data.alerts as alerts_module
        original = alerts_module.RECIPIENT_EMAIL
        alerts_module.RECIPIENT_EMAIL = recipient_email

    triggered = check_and_send_alerts(
        risk_score=risk_score,
        inflation=inflation,
        mwk_per_usd=mwk_per_usd,
        gdp_growth=gdp_growth,
        government_debt=government_debt,
    )

    if recipient_email:
        alerts_module.RECIPIENT_EMAIL = original

    if triggered:
        save_last_alert_time()
        return {
            "status": "sent",
            "message": f"Alert sent — {len(triggered)} threshold(s) breached.",
            "triggered": triggered
        }
    else:
        save_last_alert_time()
        return {
            "status": "ok",
            "message": "All indicators within safe limits. No alert sent.",
            "triggered": []
        }
