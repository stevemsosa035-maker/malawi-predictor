"""
World Bank data collector for Malawi.
Pulls real economic data - no API key needed.
"""

import wbgapi as wb
import pandas as pd
from datetime import datetime

COUNTRY = "MWI"

INDICATORS = {
    "FP.CPI.TOTL.ZG":       "Inflation CPI percent",
    "NY.GDP.MKTP.KD.ZG":    "GDP growth percent",
    "BN.CAB.XOKA.GD.ZS":    "Current account percent of GDP",
    "GC.DOD.TOTL.GD.ZS":    "Government debt percent of GDP",
    "PA.NUS.FCRF":           "Exchange rate MWK per USD",
    "FR.INR.LEND":           "Lending interest rate percent",
    "NE.EXP.GNFS.ZS":       "Exports percent of GDP",
    "NE.IMP.GNFS.ZS":       "Imports percent of GDP",
}


def fetch_all(start_year=2000):
    results = {}
    current_year = datetime.now().year

    for code, name in INDICATORS.items():
        try:
            raw = wb.data.DataFrame(
                code,
                economy=COUNTRY,
                time=range(start_year, current_year + 1),
                numericTimeKeys=True,
                labels=False,
            )
            if raw.empty:
                print(f"No data: {name}")
                continue

            df = raw.T.reset_index()
            df.columns = ["year", "value"]
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna().sort_values("year").reset_index(drop=True)
            results[name] = df
            print(f"OK: {name} — {len(df)} rows")

        except Exception as e:
            print(f"FAILED: {name} — {e}")

    return results


def fetch_single(indicator_code, start_year=2000):
    name = INDICATORS.get(indicator_code, indicator_code)
    current_year = datetime.now().year
    try:
        raw = wb.data.DataFrame(
            indicator_code,
            economy=COUNTRY,
            time=range(start_year, current_year + 1),
            numericTimeKeys=True,
            labels=False,
        )
        df = raw.T.reset_index()
        df.columns = ["year", "value"]
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().sort_values("year").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame(columns=["year", "value"])


if __name__ == "__main__":
    print("Fetching Malawi data from World Bank...")
    data = fetch_all(start_year=2005)
    print(f"\nDone. Got {len(data)} indicators.")
    for name, df in data.items():
        latest = df.iloc[-1]
        print(f"  {name}: {latest["value"]:.2f} ({int(latest["year"])})")
