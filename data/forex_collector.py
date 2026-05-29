"""
Forex collector for Malawi Kwacha (MWK).
Pulls live and historical MWK/USD exchange rates.
Uses free APIs — no key needed.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta


def fetch_latest_rate():
    """
    Get the current MWK/USD exchange rate.
    Returns a dict with rate and timestamp.
    """
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("result") == "success":
            rate = data["rates"].get("MWK")
            timestamp = data.get("time_last_update_utc", "Unknown")
            print(f"Live rate: 1 USD = {rate} MWK")
            print(f"Updated: {timestamp}")
            return {
                "rate": rate,
                "timestamp": timestamp,
                "source": "open.er-api.com"
            }
        else:
            print("API returned error — trying backup...")
            return fetch_backup_rate()

    except Exception as e:
        print(f"Primary API failed: {e}")
        return fetch_backup_rate()


def fetch_backup_rate():
    """
    Backup API in case primary fails.
    """
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        rate = data["rates"].get("MWK")
        print(f"Backup rate: 1 USD = {rate} MWK")
        return {
            "rate": rate,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "exchangerate-api.com"
        }
    except Exception as e:
        print(f"Backup API also failed: {e}")
        return {"rate": None, "timestamp": None, "source": "failed"}


def fetch_historical_rates(days=90):
    """
    Build a DataFrame of recent MWK/USD rates.
    Note: Free APIs give limited history.
    We combine with World Bank annual data for longer history.
    """
    try:
        records = []
        today = datetime.today()

        for i in range(days, 0, -5):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            url = f"https://open.er-api.com/v6/history/USD/{date.year}/{date.month}/{date.day}"

            try:
                resp = requests.get(url, timeout=8)
                d = resp.json()
                if d.get("result") == "success":
                    rate = d["rates"].get("MWK")
                    if rate:
                        records.append({"date": date_str, "rate": rate})
            except:
                continue

        if records:
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            print(f"Got {len(df)} historical rate records")
            return df
        else:
            print("No historical records retrieved")
            return pd.DataFrame(columns=["date", "rate"])

    except Exception as e:
        print(f"Historical fetch failed: {e}")
        return pd.DataFrame(columns=["date", "rate"])


def get_depreciation_summary(df):
    """
    Calculate how much MWK has lost value over different periods.
    Higher number = more depreciation = more risk.
    """
    if df is None or df.empty or len(df) < 2:
        return {}

    latest = df.iloc[-1]["rate"]
    summary = {}

    periods = {"30 days": 6, "60 days": 12, "90 days": 18}
    for label, steps_back in periods.items():
        if len(df) > steps_back:
            old_rate = df.iloc[-(steps_back)]["rate"]
            change_pct = ((latest - old_rate) / old_rate) * 100
            summary[label] = round(change_pct, 2)

    return summary


if __name__ == "__main__":
    print("Testing Forex collector...")
    print("")

    result = fetch_latest_rate()
    print(f"Result: {result}")
    print("")

    print("Fetching recent history (this may take a moment)...")
    df = fetch_historical_rates(days=30)

    if not df.empty:
        print("")
        summary = get_depreciation_summary(df)
        print("Depreciation summary:")
        for period, change in summary.items():
            direction = "weaker" if change > 0 else "stronger"
            print(f"  {period}: MWK {direction} by {abs(change)}%")
