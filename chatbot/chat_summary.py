from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from typing import List, Dict
from dotenv import load_dotenv, find_dotenv
import os
import asyncio
load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')


GEMINI_API_KEYS = []
for i in range(12):  # Duyệt từ 0 đến 11
    key = os.environ.get(f"API_GEMINI_{i}")
    if key:
        GEMINI_API_KEYS.append(key)
    else:
        # Dừng lại nếu không tìm thấy key tiếp theo
        break
# Khởi tạo một chỉ mục toàn cục để xoay vòng các key
key_index = 0
key_lock = asyncio.Lock()

async def get_next_key() -> str:
    """
    Hàm bất đồng bộ để lấy API key tiếp theo trong danh sách.
    Sử dụng lock để đảm bảo an toàn khi chạy đa luồng.
    """
    global key_index
    async with key_lock:
        key = GEMINI_API_KEYS[key_index]
        key_index = (key_index + 1) % len(GEMINI_API_KEYS)
        return key


async def summarize_chat_history(history_context: List[Dict[str, str]]) -> str:
    """
    Nhận history_context (list of dict {"role": ..., "content": ...})
    Trả về 1 chuỗi tóm tắt ~6 câu.
    """

    if not GEMINI_API_KEYS:
        raise ValueError("Không tìm thấy GEMINI API keys nào trong file .env.")
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            # 1. Chuyển list of dict thành 1 chuỗi dài
            history_text = ""
            for msg in history_context:
                role = msg["role"]
                content = msg["content"]
                history_text += f"{role.upper()}: {content}\n"

            # 2. Tạo prompt tóm tắt
            prompt = (
                "Bạn là một trợ lý AI, nhiệm vụ là tóm tắt đoạn hội thoại dưới đây để "
                "cung cấp context cho một agent xử lý tiếp theo. "
                "Tóm tắt nên giữ các thông tin quan trọng, ý chính, "
                "bỏ bớt chi tiết không cần thiết và viết gọn thành khoảng 6 câu. "
                "Hãy sử dụng ngôn ngữ tự nhiên, dễ đọc, và theo trình tự thời gian của các tin nhắn.\n\n"
                f"Hội thoại:\n{history_text}\n\n"
                "Trả về kết quả tóm tắt duy nhất, không kèm thẻ hay định dạng khác."
            )

            api_key = await get_next_key()
            # 3. Gọi model Gemini thông qua LangChain
            chat_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",  # hoặc model khác bạn có
                temperature=0.0,
                google_api_key=api_key
            )

            response = await chat_model.agenerate([[HumanMessage(content=prompt)]])
            
            summary_text = response.generations[0][0].message.content.strip()
            return summary_text

        except google.api_core.exceptions.ServiceUnavailable as e:
            print(f"[RAG ERROR] API call failed with ServiceUnavailable error. This is a server-side issue. Retrying with a new key... {e}")
            await asyncio.sleep(2) # Chờ lâu hơn một chút
        # Giữ lại khối `except` để bắt lỗi 429 (Too Many Requests)
        except google.api_core.exceptions.ResourceExhausted as e:
            print(f"[RAG ERROR] API call failed with ResourceExhausted error. Retrying with a new key... {e}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[RAG ERROR] Failed to perform RAG for job: {e}")
            return
    
    # Nếu tất cả các key đều bị lỗi, trả về một lỗi cuối cùng
    print('tất cả key đã bị rate limit')
    return