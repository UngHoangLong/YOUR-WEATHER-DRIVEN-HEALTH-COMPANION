import os
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from .tool_agent import get_data_weather_climate_uv, get_name_disease, get_data_from_vector_database
from dotenv import load_dotenv, find_dotenv
from core.redis_client import get_redis_data, get_redis_cache_conn, get_redis_history_conn
import json
import traceback
import google.api_core.exceptions
from backend.storage_history_message import append_chat_history
from langchain.schema import SystemMessage
import redis.asyncio as redis
import time
from redis.exceptions import ResponseError, ConnectionError, TimeoutError


load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
QUEUE_CHATBOT = os.getenv("QUEUE_CHATBOT", "queue_chatbot")
# Khởi tạo một danh sách để chứa tất cả API key từ file .env
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

# tool lấy dữ liệu thời tiết, climate, uv
@tool
async def get_weather_report(dates: list[dict], city_id: int):
    """
    Truy vấn cơ sở dữ liệu để lấy và diễn giải dữ liệu thời tiết cho các ngày và thành phố cụ thể.
    Dùng công cụ này khi người dùng hỏi về thời tiết, chất lượng không khí, hoặc chỉ số UV.

    Args:
        dates (list[dict]): Danh sách các từ điển, mỗi từ điển biểu diễn một ngày.
                            Mỗi từ điển phải có các khóa sau:
                            - 'day' (int): Ngày trong tháng (ví dụ: 17).
                            - 'month' (int): Tháng trong năm (ví dụ: 9).
                            - 'year' (int): Năm (ví dụ: 2025).
        city_id (int): ID của thành phố để lấy dữ liệu.
    """
    print(f"\n--- Công cụ 'get_weather_report' được gọi với các ngày: {dates} và city_id: {city_id} ---")
    
    reports = []
    for date_data in dates:
        day = date_data['day']
        month = date_data['month']
        year = date_data['year']
        
        # Hàm get_data_weather_climate_uv bây giờ trả về một danh sách các chuỗi
        daily_interpretations_list = await get_data_weather_climate_uv(day, month, year, city_id)
        
        if daily_interpretations_list:
            # 🌟 Sửa lỗi ở đây: Nối các chuỗi trong danh sách lại
            daily_interpretation = "\n".join(daily_interpretations_list)
            reports.append(f"Ngày {day}/{month}/{year}:\n{daily_interpretation}")
        else:
            reports.append(f"Ngày {day}/{month}/{year}: Không có dữ liệu.")
            
    return reports

# tool lấy dữ liệu bệnh lý
@tool
async def get_user_disease_info(user_id: int):
    """
    Truy vấn cơ sở dữ liệu để lấy thông tin về bệnh lý và tình trạng sức khỏe của người dùng.
    
    Sử dụng tool này nếu cần biết về thông tin bệnh lý của người dùng. Tool này trả về tên bệnh và mô tả tình trạng sức khoẻ
    mà người dùng đã cung cấp.

    Args:
        user_id (int): ID của người dùng để truy vấn thông tin.
    """
    response_text = await get_name_disease(user_id)
    if response_text is None: return "không có dữ liệu"
    return response_text

@tool
async def retrieve_health_guideline(query_question: str, disease_name: str):
    """
    Truy vấn cơ sở dữ liệu vector để tìm kiếm các tài liệu học thuật chi tiết
    về mối liên hệ giữa các yếu tố môi trường (thời tiết, khí hậu, UV) và bệnh lý của người dùng.
    
    Sử dụng tool này khi người dùng hỏi các câu hỏi chi tiết về mối quan hệ giữa
    thời tiết hoặc khí hậu và một bệnh cụ thể. Ví dụ: "Làm thế nào để phòng tránh tác động của tia UV
    đối với bệnh dị ứng?", hoặc "Không khí ô nhiễm có làm trầm trọng thêm
    bệnh hen suyễn không?".
    Args:
        query_question (str): Câu hỏi chi tiết của người dùng cần được truy vấn.
        disease_name (str): Tên bệnh của người dùng được lấy từ tool "get_user_disease_info". 
        Vì nó chính là collection name cần truy xuất
    """
    response_text = await get_data_from_vector_database(query_question, disease_name)
    if response_text is None: return "không có dữ liệu"
    return response_text

async def agent_process(city_id_from_fastapi: int, user_id_from_fastapi: int, input_from_user: str, history_context: str ):
    """Chạy ví dụ minh họa."""
    if not GEMINI_API_KEYS:
        raise ValueError("Không tìm thấy GEMINI API keys nào trong file .env.")
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            # Lấy ngày hiện tại ở múi giờ Việt Nam
            vietnam_timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            now_vietnam = datetime.now(vietnam_timezone)
            current_date_str = now_vietnam.strftime("%Y-%m-%d")

            api_key = await get_next_key()
            # Khởi tạo mô hình Gemini với LangChain
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=api_key)

            # Định nghĩa các công cụ mà agent có thể sử dụng
            tools_list = [get_weather_report, get_user_disease_info, retrieve_health_guideline]

            # Định nghĩa prompt cho agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""Bạn là một trợ lý sức khỏe và thời tiết thông minh.
                Mục tiêu của bạn là cung cấp lời khuyên cá nhân hóa, dựa trên dữ liệu thời tiết, thông tin bệnh lý và các kiến thức tham khảo.
                Hãy luôn trả lời một cách hữu ích, dễ hiểu và chuyên nghiệp bằng ngôn ngữ *Tiếng Việt*.
                Hôm nay là {current_date_str}.
                Thông tin về thành phố mặc định của người dùng đã được cung cấp cho bạn dưới dạng 'city_id' và bạn phải sử dụng nó cho các truy vấn liên quan đến thời tiết. 
                Bạn KHÔNG cần phải hỏi người dùng về tên thành phố của họ.
                Bạn có thể sử dụng các công cụ sau để thu thập thông tin:
                - Tool 1: Lấy dữ liệu thời tiết, chất lượng không khí và chỉ số UV cho các ngày cụ thể.
                - Tool 2: Lấy thông tin về các bệnh của người dùng.
                - Tool 3: Lấy thông tin từ cơ sở dữ liệu kiến thức để đưa ra lời khuyên về sức khỏe.
                Khi trả lời, hãy tổng hợp thông tin từ tất cả các công cụ cần thiết.
                Ví dụ: Nếu người dùng hỏi Thời tiết ngày mai có ảnh hưởng gì đến bệnh của tôi không ?,
                bạn cần sử dụng tool thời tiết và tool sức khỏe để đưa ra câu trả lời đầy đủ."""),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            # Tạo agent có khả năng gọi công cụ
            agent = create_tool_calling_agent(llm, tools_list, prompt)

            # Tạo agent executor để chạy agent
            agent_executor = AgentExecutor(agent=agent, tools=tools_list, verbose=True)

            user_query = f"City_id của tôi là: {city_id_from_fastapi}, và mã user_id của tôi là {user_id_from_fastapi}. Tôi muốn hỏi bạn " + input_from_user

            if history_context:  
                chat_history_for_agent = [SystemMessage(content=history_context)]
            else:
                chat_history_for_agent = []

            # Gửi câu hỏi đến mô hình thông qua agent
            response = await agent_executor.ainvoke({
                "input": user_query, 
                "chat_history": chat_history_for_agent,
            })
            
            agent_output = response["output"]
            return agent_output
            
        # Thêm khối `except` để bắt lỗi 503 (Service Unavailable)
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
    print('tất cả key đã bị rate limit hoặc server quá tải')
    return

# hàm giúp agent luôn tỉnh và chờ job
PING_INTERVAL = 1800  # 30 phút ping Redis 1 lần
async def worker_loop():
    global redis_data
    global redis_cache
    redis_data = await get_redis_data()
    redis_cache = await get_redis_cache_conn()
    print("[Chatbot_Agent] Started worker loop...")
    last_ping = time.time()
    while True:
        if time.time() - last_ping > PING_INTERVAL:
            try:
                pong1 = await redis_data.ping()
                pong2 = await redis_cache.ping()
                if pong1 is True and pong2 is True:
                    print("[Worker] Redis ping OK")
                else:
                    print("[Worker] Redis ping failed → reconnecting")
                    redis_data = await get_redis_data()
                    redis_cache = await get_redis_cache_conn()
            except Exception as e:
                print(f"[Worker] Redis ping error: {e} → reconnecting")
                redis_data = await get_redis_data()
                redis_cache = await get_redis_cache_conn()

            last_ping = time.time()
        
        try:
            if redis_data is None or redis_cache is None:
                redis_data = await get_redis_data()
                redis_cache = await get_redis_cache_conn()

            job_json = await redis_data.brpop(QUEUE_CHATBOT, timeout=5)
        except ResponseError as e:
            print(f"[Worker] BRPOP was force-unblocked, retrying... {e}")
            await asyncio.sleep(0.5)
            continue

        except (ConnectionError, TimeoutError) as e:
            print(f"[Worker] Redis connection lost: {e}. Reconnecting...")
            redis_data = None  # force reconnect
            traceback.print_exc()
            await asyncio.sleep(1)
            continue

        except Exception as e:
            print(f"[Worker] Unexpected error during BRPOP: {e}")
            traceback.print_exc()
            await asyncio.sleep(1)
            continue

        if job_json is None:
            continue

        _, job_str = job_json
        job_data = json.loads(job_str)
        request_id = job_data["request_id"]
        city_id = job_data["city_id"]
        user_id = job_data["user_id"]
        user_input = job_data["user_input"]
        summary_history = job_data["history_context"]
        try:
            agent_output = await agent_process(city_id, user_id, user_input, summary_history)
            if agent_output is None: agent_output = "Không thể xử lý câu hỏi này"
            # Lưu kết quả vào Redis Cache (DB1) với TTL
            # TTL (time-to-live) là 1800 giây (30 phút)
            TTL_SECONDS = 1800
            await redis_cache.setex(
                name=request_id, 
                time=TTL_SECONDS, 
                value=agent_output
            )
            print(f"[Chatbot_Agent] Hoàn thành job {request_id}. Kết quả đã được lưu vào Redis cache với TTL {TTL_SECONDS} giây.")
            # 2. Push bot response vào Redis history (DB2)
            redis_history = await get_redis_history_conn()
            await append_chat_history(user_id, "bot", agent_output, redis_history)
            print(f"[Chatbot_Agent] Đã lưu vào redis history chat")

        except Exception as e:
            print(f"[Chatbot_Agent] Error in worker loop for job {request_id}: {e}")
            traceback.print_exc()
    
# Chạy chương trình
if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("\n[Chatbot_Agent] Stopped by user (Ctrl+C)")

# python -m chatbot.ai_agent