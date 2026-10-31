"""Feature 6: monthly sales / revenue forecasting (trend + seasonality)."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


def _features(index, t0):
    t = np.arange(t0, t0 + len(index))
    m = index.month.values
    return np.column_stack([t, np.sin(2 * np.pi * m / 12), np.cos(2 * np.pi * m / 12)])


def forecast_series(df, date_col, value_col, periods=6):
    s = df.set_index(date_col)[value_col].resample("MS").sum()
    if len(s) < 6:
        raise ValueError("Need at least 6 months of data to forecast.")
    X, y = _features(s.index, 0), s.values

    metrics = {}
    if len(s) >= 9:  # hold out last 3 months to check accuracy
        pred = LinearRegression().fit(X[:-3], y[:-3]).predict(X[-3:])
        metrics["MAE"] = round(float(mean_absolute_error(y[-3:], pred)), 2)
        metrics["MAPE %"] = round(float(np.mean(np.abs((y[-3:] - pred) / np.where(y[-3:] == 0, 1, y[-3:]))) * 100), 2)

    model = LinearRegression().fit(X, y)
    future_idx = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    future = np.maximum(model.predict(_features(future_idx, len(s))), 0)

    history = s.reset_index()
    history.columns = ["month", "actual"]
    fc = pd.DataFrame({"month": future_idx, "forecast": future.round(2)})
    return history, fc, metrics
