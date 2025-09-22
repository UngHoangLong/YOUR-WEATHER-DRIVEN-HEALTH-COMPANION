import asyncio
from core.redis_client import get_redis_history_conn

async def flush_db2():
    redis_history = await get_redis_history_conn()
    await redis_history.flushdb()
    print("✅ Đã xóa toàn bộ dữ liệu trong DB 2.")

# Chạy
asyncio.run(flush_db2())

# python clear_storage.py