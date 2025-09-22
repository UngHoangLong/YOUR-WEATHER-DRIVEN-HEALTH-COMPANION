import pandas as pd
from datetime import datetime, timedelta
from .period import assign_period_uv


def parse_uv_forecast_df(data):
    """Trích xuất forecast thành DataFrame với uvi, time (VN), year, month, day, hour"""
    records = []

    if not data or "forecast" not in data:
        return pd.DataFrame(records)

    for entry in data["forecast"]:
        utc_time = datetime.strptime(entry["time"], "%Y-%m-%dT%H:%M:%SZ")
        vn_time = utc_time + timedelta(hours=7)  # UTC+7
        records.append({
            "uvi": entry["uvi"],
            "time": vn_time,
            "year": vn_time.year,
            "month": vn_time.month,
            "day": vn_time.day,
            "hour": vn_time.hour
        })

    return pd.DataFrame(records)

def aggregate_uv_by_period(response):
    """
    Nhận DataFrame từ parse_uv_forecast_df, 
    gán period theo assign_period_uv, 
    gom uvi lấy max, loại bỏ time và hour.
    """
    df = parse_uv_forecast_df(response)
    if df.empty:
        return df

    df = df.copy()
    df["period"] = df["hour"].apply(assign_period_uv)

    grouped = df.groupby(["year", "month", "day", "period"], as_index=False).agg({
        "uvi": "max"
    })

    # Bỏ cột time và hour nếu còn
    grouped = grouped.drop(columns=[c for c in ["time", "hour"] if c in grouped.columns])

    return grouped



    return pd.DataFrame(records)
