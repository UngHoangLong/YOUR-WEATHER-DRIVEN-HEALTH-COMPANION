import pandas as pd
from datetime import datetime
from .period import assign_period

def clean_weather_data(response):
    """
    Nhận vào JSON gốc từ OpenWeather API,
    trả về DataFrame rút gọn chỉ còn trường cần thiết,
    đồng thời tách dt_txt thành day, month, year, hour.
    """
    if not response or "list" not in response or not response["list"]:
        return pd.DataFrame()  # Nếu API trả về rỗng thì return DataFrame rỗng
    city_id = response.get("city", {}).get("id")

    result = []
    for item in response.get("list", []):
        entry = {
            "city_id": city_id,
            "dt_txt": item.get("dt_txt"),
            "temp": item.get("main", {}).get("temp"),
            "feels_like": item.get("main", {}).get("feels_like"),
            "humidity": item.get("main", {}).get("humidity"),
            "weather_main": item.get("weather", [{}])[0].get("main"),
            "weather_description": item.get("weather", [{}])[0].get("description"),
            "weather_icon": item.get("weather", [{}])[0].get("icon"),
            "pop": item.get("pop"),
            "rain_3h": item.get("rain", {}).get("3h", 0),
            "wind_speed": item.get("wind", {}).get("speed"),
            "wind_gust": item.get("wind", {}).get("gust"),
            "visibility": item.get("visibility"),
            "clouds_all": item.get("clouds", {}).get("all"),
        }
        result.append(entry)

    # Chuyển thành DataFrame
    df = pd.DataFrame(result)

    # Parse datetime
    df["dt_txt"] = pd.to_datetime(df["dt_txt"], errors="coerce")

    # Tách thành day, month, year, hour
    df["year"] = df["dt_txt"].dt.year
    df["month"] = df["dt_txt"].dt.month
    df["day"] = df["dt_txt"].dt.day
    df["hour"] = df["dt_txt"].dt.hour

    return df


def aggregate_weather_by_period(response):
    df = clean_weather_data(response)
    df["period"] = df["hour"].apply(assign_period)

    # Xác định numeric và categorical
    numeric_cols = df.select_dtypes(include=["float64", "int64", "int32"]).columns.tolist()
    object_cols = df.select_dtypes(include=["object"]).columns.tolist()

    exclude = ["city_id", "year", "month", "day", "hour", "period"]
    numeric_cols = [c for c in numeric_cols if c not in exclude]

    agg_funcs = {}
    for col in numeric_cols:
        agg_funcs[col] = "mean"
    for col in object_cols:
        agg_funcs[col] = lambda x: x.mode().iloc[0] if not x.mode().empty else None

    grouped = (
        df.groupby(["city_id", "year", "month", "day", "period"], as_index=False)
          .agg(agg_funcs)
    )

    # Bỏ cột dt_txt và hour nếu còn sót
    grouped = grouped.drop(columns=[c for c in ["hour", "dt_txt"] if c in grouped.columns])

    return grouped

