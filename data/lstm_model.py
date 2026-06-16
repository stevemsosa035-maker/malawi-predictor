"""
LSTM model for Malawi Economic Predictor.
Learns patterns across multiple indicators simultaneously.
More powerful than ARIMA — sees relationships between indicators.
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

MODEL_DIR = "data/models"
os.makedirs(MODEL_DIR, exist_ok=True)


def prepare_data(dataframes, target_key, lookback=5):
    """
    Prepare multi-indicator data for LSTM training.

    Args:
        dataframes: dict of {name: DataFrame with year/value columns}
        target_key: which indicator we are forecasting
        lookback: how many years to look back

    Returns:
        X: input sequences
        y: target values
        scaler: fitted scaler for inverse transform
        years: year index
    """
    # Align all dataframes on year
    merged = None
    for name, df in dataframes.items():
        df_clean = df[["year", "value"]].dropna().copy()
        df_clean.columns = ["year", name]
        if merged is None:
            merged = df_clean
        else:
            merged = merged.merge(df_clean, on="year", how="inner")

    if merged is None or len(merged) < lookback + 2:
        return None, None, None, None

    merged = merged.sort_values("year").reset_index(drop=True)
    years = merged["year"].values
    feature_cols = [c for c in merged.columns if c != "year"]

    # Scale all features to 0-1
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(merged[feature_cols].values)

    # Build sequences
    target_idx = feature_cols.index(target_key)
    X, y = [], []

    for i in range(lookback, len(scaled)):
        X.append(scaled[i - lookback:i])
        y.append(scaled[i, target_idx])

    X = np.array(X)
    y = np.array(y)
    return X, y, scaler, years[lookback:]


def build_model(input_shape):
    """Build the LSTM neural network."""
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def train_lstm(
    dataframes,
    target_key,
    lookback=5,
    epochs=100,
    verbose=0
):
    """
    Train LSTM model on Malawi economic data.

    Returns:
        model: trained Keras model
        scaler: fitted MinMaxScaler
        history: training history
        mae: mean absolute error on training data
    """
    print(f"Preparing data for LSTM — target: {target_key}")
    X, y, scaler, years = prepare_data(dataframes, target_key, lookback)

    if X is None:
        print("Not enough data to train LSTM.")
        return None, None, None, None

    print(f"Training on {len(X)} sequences with {X.shape[2]} features")

    model = build_model((X.shape[1], X.shape[2]))

    early_stop = EarlyStopping(
        monitor="loss",
        patience=10,
        restore_best_weights=True
    )

    history = model.fit(
        X, y,
        epochs=epochs,
        batch_size=4,
        callbacks=[early_stop],
        verbose=verbose
    )

    # Calculate MAE on training data
    predictions = model.predict(X, verbose=0)
    mae = float(mean_absolute_error(y, predictions))
    print(f"Training MAE: {mae:.4f}")

    return model, scaler, history, mae


def forecast_lstm(
    model,
    scaler,
    dataframes,
    target_key,
    steps=5,
    lookback=5
):
    """
    Generate future forecasts using trained LSTM.

    Returns:
        dict with forecast values, years, and last actual value
    """
    try:
        # Rebuild merged dataset
        merged = None
        for name, df in dataframes.items():
            df_clean = df[["year", "value"]].dropna().copy()
            df_clean.columns = ["year", name]
            if merged is None:
                merged = df_clean
            else:
                merged = merged.merge(df_clean, on="year", how="inner")

        merged = merged.sort_values("year").reset_index(drop=True)
        feature_cols = [c for c in merged.columns if c != "year"]
        last_year = int(merged["year"].iloc[-1])

        target_df = dataframes.get(target_key)
        last_actual = float(target_df.iloc[-1]["value"]) if target_df is not None else None

        scaled = scaler.transform(merged[feature_cols].values)
        sequence = scaled[-lookback:].copy()

        forecasts = []
        for _ in range(steps):
            inp = sequence.reshape(1, lookback, len(feature_cols))
            pred_scaled = model.predict(inp, verbose=0)[0][0]

            # Build a dummy full-feature row for inverse scaling
            dummy = sequence[-1].copy()
            target_idx = feature_cols.index(target_key)
            dummy[target_idx] = pred_scaled

            # Inverse scale just the target
            dummy_2d = dummy.reshape(1, -1)
            inv = scaler.inverse_transform(dummy_2d)
            forecast_value = float(inv[0][target_idx])
            forecasts.append(round(forecast_value, 2))

            # Roll sequence forward
            sequence = np.vstack([sequence[1:], dummy])

        forecast_years = list(range(last_year + 1, last_year + steps + 1))

        return {
            "forecast": forecasts,
            "years": forecast_years,
            "last_actual_year": last_year,
            "last_actual_value": last_actual,
            "model_type": "LSTM"
        }

    except Exception as e:
        print(f"LSTM forecast error: {e}")
        return None


if __name__ == "__main__":
    print("Testing LSTM model...")
    print("")

    import sys, os as _os
    sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from data.imf_collector import fetch_all

    print("Fetching IMF data...")
    imf = fetch_all()

    # Use all available IMF indicators as features
    dataframes = {}
    for name, df in imf.items():
        if not df.empty and len(df) >= 10:
            dataframes[name] = df
            print(f"  Using: {name} ({len(df)} years)")

    if not dataframes:
        print("No data available.")
    else:
        target = "Inflation Rate (%)"
        if target not in dataframes:
            target = list(dataframes.keys())[0]

        print(f"")
        print(f"Training LSTM to forecast: {target}")
        print("This may take 30-60 seconds...")
        print("")

        model, scaler, history, mae = train_lstm(
            dataframes=dataframes,
            target_key=target,
            lookback=5,
            epochs=100,
        )

        if model:
            print("")
            print(f"Model trained. MAE: {mae:.4f}")
            print("")
            print("Forecasting next 5 years...")

            result = forecast_lstm(
                model=model,
                scaler=scaler,
                dataframes=dataframes,
                target_key=target,
                steps=5
            )

            if result:
                print(f"Last actual: {result['last_actual_value']}% ({result['last_actual_year']})")
                print("LSTM Forecast:")
                for yr, val in zip(result["years"], result["forecast"]):
                    print(f"  {yr}: {val}%")

