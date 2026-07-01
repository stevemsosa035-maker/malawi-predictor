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
CUTOFF_YEAR = datetime.now().year
IMF_PROJECTION_START = CUTOFF_YEAR + 1



def fetch_indicator(code, name):
    """
    Fetch a single IMF indicator for Malawi.
    Splits data into two clean sets:
        - actuals: historical data up to current year
        - imf_projections: IMF forecast from next year onwards
    Our models only train on actuals.
    IMF projections are stored separately for comparison.
    """
    try:
        url = f"{BASE_URL}/data/{code}/MWI"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
        values = raw.get("values", {}).get(code, {}).get("MWI", {})

        if not values:
            return None, None

        rows = []
        for year_str, val in values.items():
            try:
                rows.append({"year": int(year_str), "value": float(val)})
            except:
                continue

        if not rows:
            return None, None

        df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

        # Split at cutoff year
        actuals = df[df["year"] <= CUTOFF_YEAR].copy()
        imf_proj = df[df["year"] > CUTOFF_YEAR].copy()

        if actuals.empty:
            return None, None

        latest_yr = int(actuals.iloc[-1]["year"])
        print(f"OK: {name} — {len(actuals)} years of actuals (up to {latest_yr}), {len(imf_proj)} IMF projection years")

        return actuals, imf_proj if not imf_proj.empty else None

    except Exception as e:
        print(f"FAILED: {name} — {e}")
        return None, None

def get_current_value(indicator_name, actuals):
    """Get the most recent actual value for an indicator."""
    df = actuals.get(indicator_name)
    if df is None or df.empty:
        return None, None
    latest = df.iloc[-1]
    return round(float(latest["value"]), 2), int(latest["year"])

def fetch_all():
    """
    Fetch all IMF indicators for Malawi.
    Returns two dicts:
        actuals: {name: DataFrame} - historical only, for our models
        imf_projections: {name: DataFrame} - IMF forecasts, for comparison
    """
    actuals = {}
    imf_projections = {}

    for code, name in INDICATORS.items():
        actual_df, proj_df = fetch_indicator(code, name)
        if actual_df is not None:
            actuals[name] = actual_df
        if proj_df is not None:
            imf_projections[name] = proj_df

    return actuals, imf_projections



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
    print(f"Fetching IMF data — actuals cut off at {CUTOFF_YEAR}...")
    print("")
    actuals, imf_proj = fetch_all()
    print("")
    print(f"Actuals loaded: {len(actuals)} indicators")
    print(f"IMF projections loaded: {len(imf_proj)} indicators")
    print("")
    for name, df in actuals.items():
        val, yr = get_current_value(name, actuals)
        if val:
            print(f"  {name}: {val} ({yr})")
    if imf_proj:
        print("")
        print("IMF projections (for comparison only):")
        for name, df in imf_proj.items():
            print(f"  {name}: {list(df['year'])} -> {list(df['value'].round(2))}")

