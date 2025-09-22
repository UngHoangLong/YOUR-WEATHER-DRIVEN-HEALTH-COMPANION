import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
# Lấy biến môi trường (cấu hình Redis cho queue và cache)
REDIS_DATA_HOST = os.getenv("REDIS_DATA_HOST", "localhost")
REDIS_DATA_PORT = int(os.getenv("REDIS_QUEUE_PORT", 6379))


# Biến toàn cục để giữ kết nối (chỉ khởi tạo một lần)
redis_data = None
redis_cache_conn = None
redis_history_conn = None

# kết nối đến db0 chứa các messeage queue
async def get_redis_data():
    """
    Kết nối đến Redis QUEUE (dùng để chứa jobs).
    """
    global redis_data
    if redis_data is None:
        redis_data = await redis.from_url(
            f"redis://{REDIS_DATA_HOST}:{REDIS_DATA_PORT}",
            decode_responses=True,  # dữ liệu trả về là string thay vì bytes
            socket_connect_timeout=30,  # timeout khi connect
            socket_timeout=30           # timeout khi đọc/ghi
        )
    return redis_data


async def get_redis_cache_conn(): # dùng để kết nối đến redis lưu dữ liệu tạm thời
    """
    Kết nối đến Redis DB 1 (dùng để lưu tạm kết quả).
    """
    global redis_cache_conn
    if redis_cache_conn is None:
        redis_cache_conn = await redis.from_url(
            f"redis://{REDIS_DATA_HOST}:{REDIS_DATA_PORT}/1",
            decode_responses=True,
            socket_connect_timeout=30,  # timeout khi connect
            socket_timeout=30           # timeout khi đọc/ghi
        )
    return redis_cache_conn

# --- Redis DB 2 ---
async def get_redis_history_conn():
    global redis_history_conn
    if redis_history_conn is None:
        redis_history_conn = await redis.from_url(
            f"redis://{REDIS_DATA_HOST}:{REDIS_DATA_PORT}/2",
            decode_responses=True,
            socket_connect_timeout=30,  # timeout khi connect
            socket_timeout=30           # timeout khi đọc/ghi
        )
    return redis_history_conn