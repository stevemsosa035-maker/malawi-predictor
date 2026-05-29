"""
IMF data collector for Malawi.
Uses the IMF JSON API — completely free, no key needed.
Updates monthly. More current than World Bank.
"""

import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

# IMF indicator codes for Malawi
INDICATORS = {
    "PCPIPCH":  "Inflation Rate (%)",
    "NGDP_RPCH": "GDP Growth (%)",
    "GGR_NGDP":  "Government Revenue (% GDP)",
    "GGXWDG_NGDP": "Government Debt (% GDP)",
    "BCA_NGDPD":  "Current Account (% GDP)",
    "LUR":       "Unemployment Rate (%)",
}

COUNTRY = "MWI"


def fetch_indicator(code, name):
    """
    Fetch a single indicator from IMF for Malawi.
    Returns DataFrame with columns: year, value.
    """
    url = f"{BASE_URL}/PCPIPCH/{COUNTRY}"
    url = f"{BASE_URL}/{code}/{COUNTRY}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code} for {name}")
            return None

        data = resp.json()
        values = data.get("values", {})
        country_data = values.get(code, {}).get(COUNTRY, {})

        if not country_data:
            print(f"No data returned for {name}")
            return None

        records = []
        for year_str, value in country_data.items():
            try:
                records.append({
                    "year": int(year_str),
                    "value": float(value)
                })
            except:
                continue

        df = pd.DataFrame(records)
        df = df.sort_values("year").reset_index(drop=True)
        print(f"OK: {name} — {len(df)} years of data")
        return df

    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None


def fetch_all():
    """
    Fetch all IMF indicators for Malawi.
    Returns dict of indicator name -> DataFrame.
    """
    results = {}
    for code, name in INDICATORS.items():
        df = fetch_indicator(code, name)
        if df is not None and not df.empty:
            results[name] = df
    return results


def get_current_value(name, data):
    """
    Get the most recent value for an indicator.
    Looks for current year first, then falls back.
    """
    df = data.get(name)
    if df is None or df.empty:
        return None, None

    current_year = datetime.now().year

    # Try current year first
    row = df[df["year"] == current_year]
    if not row.empty:
        return round(float(row.iloc[0]["value"]), 2), current_year

    # Try last year
    row = df[df["year"] == current_year - 1]
    if not row.empty:
        return round(float(row.iloc[0]["value"]), 2), current_year - 1

    # Fall back to latest available
    latest = df.iloc[-1]
    return round(float(latest["value"]), 2), int(latest["year"])


if __name__ == "__main__":
    print("Fetching Malawi data from IMF...")
    print("")
    data = fetch_all()
    print("")
    print(f"Fetched {len(data)} indicators.")
    print("")
    print("Current values:")
    for name in data:
        value, year = get_current_value(name, data)
        if value is not None:
            print(f"  {name}: {value} ({year})")
