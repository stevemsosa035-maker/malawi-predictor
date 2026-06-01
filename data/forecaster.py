
"""
ARIMA forecasting engine for Malawi Economic Predictor.
Fixed version — works with IMF data structure.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA


def forecast_indicator(df, steps=5, indicator_name=""):
    try:
        df = df.dropna().sort_values("year").reset_index(drop=True)

        if len(df) < 4:
            print(f"Not enough data for {indicator_name}")
            return None

        series = list(df["value"].values)
        last_year = int(df["year"].iloc[-1])
        last_value = float(df["value"].iloc[-1])

        try:
            model = ARIMA(series, order=(1, 1, 1))
            fitted = model.fit()
        except Exception:
            model = ARIMA(series, order=(1, 1, 0))
            fitted = model.fit()

        forecast_values = fitted.forecast(steps=steps)
        forecast_years = list(range(last_year + 1, last_year + steps + 1))

        fc_list = [round(float(v), 2) for v in forecast_values]
        lower = [round(float(v) * 0.85, 2) for v in fc_list]
        upper = [round(float(v) * 1.15, 2) for v in fc_list]

        print(f"Forecast OK: {indicator_name}")
        for yr, val in zip(forecast_years, fc_list):
            print(f"  {yr}: {val}")

        return {
            "forecast": fc_list,
            "years": forecast_years,
            "lower": lower,
            "upper": upper,
            "last_actual_year": last_year,
            "last_actual_value": last_value,
        }

    except Exception as e:
        print(f"Forecast failed for {indicator_name}: {e}")
        return None


def build_forecast_chart_data(df, forecast_result):
    if forecast_result is None:
        return df, None

    hist = df[["year", "value"]].copy()
    hist["type"] = "Actual"

    fc = pd.DataFrame({
        "year": forecast_result["years"],
        "value": forecast_result["forecast"],
        "type": "Forecast"
    })

    combined = pd.concat([hist, fc], ignore_index=True)
    return combined, fc


if __name__ == "__main__":
    print("Testing forecaster...")
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.imf_collector import fetch_all
    data = fetch_all()
    for name, df in data.items():
        print(f"")
        result = forecast_indicator(df, steps=5, indicator_name=name)
