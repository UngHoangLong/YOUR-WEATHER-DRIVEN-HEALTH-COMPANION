import os
import json

MAX_HISTORY = 10  # số tin nhắn tối đa lưu cho mỗi user
NUM_HISTORY_FOR_CONTEXT = 6  # số tin nhắn lấy ra để gửi cho agent
async def append_chat_history(user_id: int, role: str, content: str, redis_conn):
    """
    Thêm 1 message vào lịch sử chat và giữ tối đa MAX_HISTORY phần tử.
    role: 'user' hoặc 'assistant'
    """
    key = f"chat_history:{user_id}"
    message = json.dumps({"role": role, "content": content})
    await redis_conn.lpush(key, message)
    await redis_conn.ltrim(key, 0, MAX_HISTORY - 1)  # giữ MAX_HISTORY phần tử

async def get_recent_chat_history(user_id: int, n: int, redis_conn):
    """
    Lấy n message gần nhất (từ cũ → mới) cho tóm tắt hoặc gửi vào agent.
    """
    key = f"chat_history:{user_id}"
    history_raw = await redis_conn.lrange(key, 0, n-1)
    # Đảo thứ tự: mới → cũ => cũ → mới
    history = [json.loads(msg) for msg in history_raw[::-1]]
    return history