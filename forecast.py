"""Helpers for the saved CatBoost daily sales model."""
from __future__ import annotations

import datetime
from pathlib import Path

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "Business Sales.joblib"
REFERENCE_START_DATE = datetime.date(2025, 7, 1)

QUIET_BELOW = 17975.62
PEAK_ABOVE = 36475.40
TYPICAL_DAY = 32153.71


def load_assets():
    artifacts = joblib.load(MODEL_PATH)
    return artifacts["model"], list(artifacts["features"])


def build_input_df(
    selected_date: datetime.date,
    lag_1d: float,
    lag_7d: float,
    lag_14d: float,
    lag_30d: float,
    rolling_mean_7d: float,
    rolling_mean_30d: float,
    features: list[str],
) -> pd.DataFrame:
    weekday = selected_date.weekday()
    row = {
        "time_index": max(0, (selected_date - REFERENCE_START_DATE).days),
        "Month": selected_date.month,
        "Day": selected_date.day,
        "DayOfWeek": weekday,
        "IsWeekend": 1 if weekday >= 5 else 0,
        "is_q4": 1 if selected_date.month in (10, 11, 12) else 0,
        "is_month_start": 1 if selected_date.day <= 3 else 0,
        "is_month_end": 1 if selected_date.day >= 28 else 0,
        "lag_1d": float(lag_1d),
        "lag_7d": float(lag_7d),
        "lag_14d": float(lag_14d),
        "lag_30d": float(lag_30d),
        "rolling_mean_7d": float(rolling_mean_7d),
        "rolling_mean_30d": float(rolling_mean_30d),
    }
    return pd.DataFrame([[row[f] for f in features]], columns=features)


def predict_sales(model, input_df: pd.DataFrame) -> float:
    return max(0.0, float(model.predict(input_df)[0]))


def demand_band(prediction: float) -> str:
    if prediction < QUIET_BELOW:
        return "Quiet Day"
    if prediction <= PEAK_ABOVE:
        return "Steady Day"
    return "Peak Day"


def band_class(band: str) -> str:
    return {
        "quiet day": "quiet",
        "steady day": "steady",
        "peak day": "peak",
    }.get(str(band).lower(), "steady")
