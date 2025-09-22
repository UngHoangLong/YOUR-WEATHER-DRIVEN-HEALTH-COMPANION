import os
import asyncpg
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')

# Đọc thông tin PostgreSQL từ env
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB   = os.getenv("POSTGRES_DB", "health_twin")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Biến toàn cục giữ connection pool
db_pool = None


async def init_db():
    """
    Khởi tạo connection pool đến PostgreSQL.
    Gọi 1 lần khi start app/worker.
    """
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            min_size=1,   # số connection tối thiểu trong pool
            max_size=10   # số connection tối đa
        )
        print("[PostgreSQL] Connection pool created")
    return db_pool


async def get_db():
    """
    Lấy 1 connection từ pool.
    Nên dùng trong async context:
        async with (await get_db()).acquire() as conn:
            ...
    """
    global db_pool
    if db_pool is None:
        await init_db()
    return db_pool
