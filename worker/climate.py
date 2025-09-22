import pandas as pd
from datetime import datetime
from .period import assign_period

def majority_or_median(series):
    """Trả về giá trị xuất hiện >=2 lần, nếu không có thì lấy median. Nếu rỗng thì None."""
    if series is None or series.empty:
        return None
    counts = series.value_counts()
    if counts.empty:
        return None
    if counts.iloc[0] >= 2:
        return counts.index[0]
    else:
        try:
            return int(series.median())
        except Exception:
            return None


def process_air_pollution_grouped(data):
    """Chuyển list thành DataFrame, thêm year/month/day/hour_group và nhóm lại theo 8 khung 3h"""
    if not data or "list" not in data or not data["list"]:
        return pd.DataFrame()
    
    df = pd.json_normalize(data["list"])

    # Nếu thiếu cột dt → return rỗng
    if "dt" not in df or df["dt"].empty:
        return pd.DataFrame()
    
    # Đổi dt -> datetime
    try:
        df["dt_txt"] = pd.to_datetime(df["dt"].apply(lambda x: datetime.utcfromtimestamp(x)))
    except Exception:
        return pd.DataFrame()

    df["year"] = df["dt_txt"].dt.year
    df["month"] = df["dt_txt"].dt.month
    df["day"] = df["dt_txt"].dt.day
    df["hour"] = df["dt_txt"].dt.hour
    
    # Nhóm khung 3h
    df["hour"] = (df["hour"] // 3) * 3
    
    # Gom nhóm (chỉ lấy cột có tồn tại trong df)
    agg_dict = {
        "main.aqi": majority_or_median,
        "components.co": "mean",
        "components.no": "mean",
        "components.no2": "mean",
        "components.o3": "mean",
        "components.so2": "mean",
        "components.pm2_5": "mean",
        "components.pm10": "mean",
        "components.nh3": "mean"
    }
    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

    if not agg_dict:
        return pd.DataFrame()

    grouped = df.groupby(["year", "month", "day", "hour"]).agg(agg_dict).reset_index()
    
    if grouped.empty:
        return pd.DataFrame()

    # Tạo lại dt_txt đại diện (nửa đầu khung giờ)
    grouped["dt_txt"] = pd.to_datetime(dict(
        year=grouped.year,
        month=grouped.month,
        day=grouped.day,
        hour=grouped.hour
    ))
    
    # Đổi tên cột (chỉ rename cột có tồn tại)
    rename_map = {
        "main.aqi": "aqi",
        "components.co": "co",
        "components.no": "no",
        "components.no2": "no2",
        "components.o3": "o3",
        "components.so2": "so2",
        "components.pm2_5": "pm2_5",
        "components.pm10": "pm10",
        "components.nh3": "nh3"
    }
    grouped = grouped.rename(columns={k: v for k, v in rename_map.items() if k in grouped.columns})
    
    # Sắp xếp lại cột
    cols = ["dt_txt", "year", "month", "day", "hour"] + [v for v in rename_map.values() if v in grouped.columns]
    grouped = grouped[cols]
    return grouped


def process_air_pollution_by_period(response):
    df = process_air_pollution_grouped(response)
    if df.empty:
        return df

    # Gán period
    if "hour" not in df:
        return pd.DataFrame()
    df["period"] = df["hour"].apply(assign_period)

    # Gom nhóm lại
    agg_dict = {col: "mean" for col in df.columns if col not in ["year", "month", "day", "period", "hour", "dt_txt"]}
    if "AQI" in df.columns:
        agg_dict["AQI"] = "max"  # AQI lấy max

    grouped = df.groupby(["year", "month", "day", "period"], as_index=False).agg(agg_dict)

    if grouped.empty:
        return grouped

    # Giữ cột theo thứ tự
    cols = ["year", "month", "day", "period"] + [c for c in grouped.columns if c not in ["year", "month", "day", "period"]]
    grouped = grouped[cols]

    return grouped
