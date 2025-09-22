import uuid
from core.postgresql_client import get_db
from core.redis_client import get_redis_data
from dotenv import load_dotenv
import os
import asyncio
import json
from .queries import GET_FULL_DATA_QUERY
from datetime import datetime
from zoneinfo import ZoneInfo
load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
QUEUE_PASSIVE_SUGGESTION = os.getenv("QUEUE_PASSIVE_SUGGESTION", "queue_passive_suggestion")
# để test
VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

async def get_data_for_json(day: int, month: int, year: int):
    """
    Retrieves weather, climate, and UV data, and structures it into a JSON-like format,
    grouped by user and city.
    """
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch(GET_FULL_DATA_QUERY, day, month, year)
    
    grouped_data = {}
    for row in rows:
        user_id = row['user_id']
        city_id = row['city_id']
        key = (user_id, city_id)
        
        # Initialize the user-city entry if it doesn't exist
        if key not in grouped_data:
            grouped_data[key] = {
                "user_id": user_id,
                "city_id": city_id,
                "disease_name": row['disease_name'],
                "describe_disease": row['describe_disease'],
                "daily_data": []
            }
        
        # Append the weather, climate, and UV data for the specific period
        grouped_data[key]["daily_data"].append({
            "period": row['period'],
            "report_time":{
                "report_day": row['report_day'],
                "report_month": row['report_month'],
                "report_year": row['report_year'],
            },
            "weather_details": {
                "temp": row['temp'],
                "feels_like": row['feels_like'],
                "humidity": row['humidity'],
                "pop": row['pop'],
                "wind_speed": row['wind_speed'],
                "wind_gust": row['wind_gust'],
                "visibility": row['visibility'],
                "clouds_all": row['clouds_all'],
                "weather_main": row['weather_main'],
                "weather_description": row['weather_description']
            },
            "climate_details": {
                "aqi": row['aqi'],
                "co": row['co'],
                "no": row['no'],
                "no2": row['no2'],
                "o3": row['o3'],
                "so2": row['so2'],
                "pm2_5": row['pm2_5'],
                "pm10": row['pm10'],
                "nh3": row['nh3']
            },
            "uvi_details": {
                "uvi": row['uvi']
            }
        })
    
    # Define a custom order for periods
    period_order = {
        'Early Morning': 1,
        'Morning': 2,
        'Noon': 3,
        'Afternoon': 4,
        'Evening': 5
    }

    # Convert the dictionary values to a list and sort the daily_data
    # based on the custom period order
    final_data_list = list(grouped_data.values())
    for item in final_data_list:
        item["daily_data"].sort(key=lambda x: period_order.get(x['period'], 99))
    
    return final_data_list

async def clear_old_data_in_suggestion_table(): # hàm xoá dữ liệu trước khi thực hiện push_job lặp lịch
    """
    Xoá toàn bộ dữ liệu trong các bảng suggestion
    """
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE TABLE suggestion RESTART IDENTITY CASCADE;")
            print("[Postgres] Cleared data from suggestion")

async def push_job_passive_suggestion(day: int, month: int, year: int):
    """
    Pushes individual user-city data as separate jobs to Redis Queue.
    """
    await clear_old_data_in_suggestion_table()
    redis_data = await get_redis_data()
    list_dic_data = await get_data_for_json(day, month, year)

    # Push each user-city dictionary as a separate job
    for user_city_data in list_dic_data:
        # Use a unique job ID for each job
        job_id = str(uuid.uuid4())
        # Convert the dictionary to a JSON string for storage in Redis
        job_data_json = json.dumps(user_city_data)
        
        await redis_data.lpush(QUEUE_PASSIVE_SUGGESTION, job_data_json)
        
        print(f"[Redis] Pushed job {job_id} for user {user_city_data['user_id']} to queue '{QUEUE_PASSIVE_SUGGESTION}'")

# này chỉ để test cho scheduler
if __name__ == "__main__":
    now = datetime.now(VIETNAM_TIMEZONE)
    day_now = now.day
    month_now = now.month
    year_now = now.year
    asyncio.run(push_job_passive_suggestion(day_now, month_now, year_now ))

# python -m scheduler.scheduler_suggestion