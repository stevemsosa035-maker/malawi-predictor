"""
Forex collector — updated to pull all major currency pairs against MWK.
"""

import requests
import pandas as pd
from datetime import datetime

PRIMARY_URL = "https://open.er-api.com/v6/latest/MWK"
BACKUP_URL  = "https://api.exchangerate-api.com/v4/latest/MWK"

# Currencies to track against MWK
# Format: code -> {name, flag, country_rate (central bank rate %), region}
TRACKED_CURRENCIES = {
    "USD": {"name": "US Dollar",          "flag": "\U0001f1fa\U0001f1f8", "country_rate": 5.25,  "region": "Global reserve"},
    "GBP": {"name": "British Pound",       "flag": "\U0001f1ec\U0001f1e7", "country_rate": 5.00,  "region": "Europe"},
    "EUR": {"name": "Euro",                "flag": "\U0001f1ea\U0001f1fa", "country_rate": 3.75,  "region": "Europe"},
    "ZAR": {"name": "South African Rand",  "flag": "\U0001f1ff\U0001f1e6", "country_rate": 8.25,  "region": "SADC"},
    "CNY": {"name": "Chinese Yuan",        "flag": "\U0001f1e8\U0001f1f3", "country_rate": 3.45,  "region": "Asia"},
    "KES": {"name": "Kenyan Shilling",     "flag": "\U0001f1f0\U0001f1ea", "country_rate": 12.50, "region": "East Africa"},
    "TZS": {"name": "Tanzanian Shilling",  "flag": "\U0001f1f9\U0001f1ff", "country_rate": 6.00,  "region": "East Africa"},
    "ZMW": {"name": "Zambian Kwacha",      "flag": "\U0001f1ff\U0001f1f2", "country_rate": 13.50, "region": "SADC"},
    "BWP": {"name": "Botswana Pula",       "flag": "\U0001f1e7\U0001f1fc", "country_rate": 2.40,  "region": "SADC"},
    "MZN": {"name": "Mozambican Metical",  "flag": "\U0001f1f2\U0001f1ff", "country_rate": 14.25, "region": "SADC"},
}

MWK_POLICY_RATE = 24.0
MWK_LENDING_RATE = 35.0


def fetch_all_rates():
    """
    Fetch all MWK rates against tracked currencies.
    Returns dict of currency -> MWK per 1 unit of that currency.
    """
    try:
        resp = requests.get(PRIMARY_URL, timeout=15)
        data = resp.json()
        if data.get("result") == "success":
            rates_vs_mwk = data.get("rates", {})
            # rates_vs_mwk[USD] = how many USD per 1 MWK
            # We want MWK per 1 USD, so invert
            result = {}
            for code, info in TRACKED_CURRENCIES.items():
                if code in rates_vs_mwk and rates_vs_mwk[code] > 0:
                    mwk_per_unit = round(1 / rates_vs_mwk[code], 4)
                    result[code] = {
                        "mwk_per_unit": mwk_per_unit,
                        "name": info["name"],
                        "flag": info["flag"],
                        "country_rate": info["country_rate"],
                        "region": info["region"],
                    }
            result["_timestamp"] = data.get("time_last_update_utc", str(datetime.now()))
            result["_source"] = "open.er-api.com"
            print(f"OK: {len(result)-2} currency pairs fetched")
            return result
    except Exception as e:
        print(f"Primary forex API failed: {e}")
    return {}


def fetch_latest_rate():
    """Original single USD/MWK rate — kept for backward compatibility."""
    try:
        resp = requests.get(PRIMARY_URL, timeout=15)
        data = resp.json()
        if data.get("result") == "success":
            rates = data.get("rates", {})
            usd_rate = rates.get("USD")
            if usd_rate and usd_rate > 0:
                mwk_per_usd = round(1 / usd_rate, 4)
                print(f"Live rate: 1 USD = {mwk_per_usd} MWK")
                return {
                    "rate": mwk_per_usd,
                    "timestamp": data.get("time_last_update_utc"),
                    "source": "open.er-api.com"
                }
    except Exception as e:
        print(f"Forex fetch failed: {e}")
    return {"rate": None, "timestamp": None, "source": "failed"}


def get_depreciation_summary(rates):
    """
    Calculate carry trade metrics for each currency pair.
    Returns ranked list from most to least attractive.
    """
    if not rates:
        return []

    analysis = []
    for code, data in rates.items():
        if code.startswith("_"):
            continue
        mwk = data["mwk_per_unit"]
        country_rate = data["country_rate"]
        # Carry spread = MWK lending rate minus foreign rate
        # Positive = you earn more holding MWK deposits than foreign
        # Negative = foreign currency deposits earn more
        carry_spread = MWK_LENDING_RATE - country_rate
        # If carry_spread is positive, MWK is high yielding
        # But MWK is depreciating — so net carry depends on depreciation pace
        analysis.append({
            "code": code,
            "name": data["name"],
            "flag": data["flag"],
            "region": data["region"],
            "mwk_per_unit": mwk,
            "country_rate": country_rate,
            "carry_spread": round(carry_spread, 2),
        })

    # Sort by MWK per unit descending (strongest foreign currency first)
    analysis.sort(key=lambda x: x["mwk_per_unit"], reverse=True)
    return analysis


if __name__ == "__main__":
    print("Testing multi-currency forex collector...")
    print("")
    rates = fetch_all_rates()
    if rates:
        analysis = get_depreciation_summary(rates)
        print(f"Updated: {rates['_timestamp']}")
        print("")
        print("Currency rankings vs MWK (strongest first):")
        for i, a in enumerate(analysis, 1):
            print(f"  {i}. {a['flag']} {a['code']} — {a['mwk_per_unit']:,.2f} MWK | {a['name']} | Carry spread: {a['carry_spread']:+.1f}pp")
