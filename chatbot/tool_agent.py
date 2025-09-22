from core.postgresql_client import get_db
from rag.rule_based import interpret_daily_data_for_single_user_city
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from typing import Dict, List
import chromadb
import google.api_core.exceptions
from dotenv import load_dotenv, find_dotenv
import os
import asyncio

load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
CHROMA_SERVER_HOST = os.environ.get("CHROMA_SERVER_HOST", "103.133.224.14")
CHROMA_SERVER_PORT = int(os.environ.get("CHROMA_SERVER_PORT", 8000))

GET_DATA_QUERY_WEATHER_CLIMATE_UV = """
    SELECT
        w.period, w.report_day, w.report_month, w.report_year,
        w.temp, w.feels_like, w.humidity, w.pop, w.wind_speed, w.wind_gust, w.visibility, w.clouds_all,
        w.weather_main, w.weather_description,
        cl.aqi, cl.co, cl.no, cl.no2, cl.o3, cl.so2, cl.pm2_5, cl.pm10, cl.nh3,
        uvid.uvi, w.city_id
    FROM weather w
    JOIN climate cl ON w.city_id = cl.city_id
    JOIN uv uvid ON w.city_id = uvid.city_id
    WHERE
        w.report_day = $1 AND w.report_month = $2 AND w.report_year = $3 AND
        cl.report_day = $1 AND cl.report_month = $2 AND cl.report_year = $3 AND
        uvid.report_day = $1 AND uvid.report_month = $2 AND uvid.report_year = $3 AND
        w.period = cl.period AND w.period = uvid.period
        AND w.city_id = $4 AND cl.city_id = $4 AND uvid.city_id = $4;
"""

# hàm lấy dữ liệu từ 3 bảng weather, climate, uv
async def get_data_weather_climate_uv(day: int, month: int, year: int, city_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch(GET_DATA_QUERY_WEATHER_CLIMATE_UV, day, month, year, city_id)
    
    if not rows:
        return []

    grouped_data = {}
    for row in rows:
        city_id_key = row['city_id']
        if city_id_key not in grouped_data:
            grouped_data[city_id_key] = {
                "city_id": city_id_key,
                "daily_data": []
            }
        
        grouped_data[city_id_key]["daily_data"].append({
            "period": row['period'],
            "report_time": {
                "report_day": row['report_day'],
                "report_month": row['report_month'],
                "report_year": row['report_year'],
            },
            "weather_details": {
                "temp": row['temp'], "feels_like": row['feels_like'], "humidity": row['humidity'],
                "pop": row['pop'], "wind_speed": row['wind_speed'], "wind_gust": row['wind_gust'],
                "visibility": row['visibility'], "clouds_all": row['clouds_all'],
                "weather_main": row['weather_main'], "weather_description": row['weather_description']
            },
            "climate_details": {
                "aqi": row['aqi'], "co": row['co'], "no": row['no'], "no2": row['no2'],
                "o3": row['o3'], "so2": row['so2'], "pm2_5": row['pm2_5'],
                "pm10": row['pm10'], "nh3": row['nh3']
            },
            "uvi_details": {
                "uvi": row['uvi']
            }
        })

    period_order = {
        'Morning': 1, 'Noon': 2, 'Afternoon': 3,
        'Evening': 4, 'Night': 5
    }

    final_data = list(grouped_data.values())[0]
    final_data["daily_data"].sort(key=lambda x: period_order.get(x['period'], 99))
    
    # 🌟 Sửa lỗi ở đây: Trả về danh sách chuỗi
    interpretations = interpret_daily_data_for_single_user_city(final_data)
    
    return interpretations

#--------------------------------------------------------------------------------------
# hàm lấy dữ liệu tên bệnh của bệnh nhân
GET_DATA_DISEASE = """
    SELECT d.disease_name, u.describe_disease
    FROM users u
    JOIN disease d ON u.disease_id = d.disease_id
    WHERE u.user_id = $1
"""

async def get_name_disease(user_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Sử dụng fetchrow() để lấy một record duy nhất
        row = await conn.fetchrow(GET_DATA_DISEASE, user_id)
    
    if not row:
        # Trả về None nếu không tìm thấy bệnh
        return None
    
    # row bây giờ là một record, bạn có thể truy cập bằng tên cột
    info = f"""Tên bệnh: {row['disease_name']}.
    Người dùng mô tả tình trạng sức khoẻ của họ như sau: {row['describe_disease']}
     """
    return info

#--------------------------------------------------------------------------------------


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

# Hàm lấy dữ liệu từ vector database
async def get_data_from_vector_database(query_question: str, disease_name: str):
    """
    "disease_name" được dùng làm tham số cho "name_collection"
    """
    
    if not GEMINI_API_KEYS:
        raise ValueError("Không tìm thấy GEMINI API keys nào trong file .env.")

    for _ in range(len(GEMINI_API_KEYS)):
        try:
            
            api_key = await get_next_key() # lấy api key tiếp theo
            embeddings = GoogleGenerativeAIEmbeddings( # nó sẽ tự chuẩn hoá sau khi embedding
                model="gemini-embedding-001",
                task_type= "QUESTION_ANSWERING",
                google_api_key=api_key
            )
            print("[RAG] Initialized GoogleGenerativeAIEmbeddings model.")

            collection_name = disease_name
            print('collection_name:', collection_name)
            vector_store = Chroma(
                client=chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT),
                collection_name=collection_name,
                embedding_function=embeddings
            )

            print(f"[RAG] Initialized Chroma vector store for collection: '{collection_name}'")
            retriever = vector_store.as_retriever(search_kwargs={"k": 2})
            # `ainvoke` là phương thức bất đồng bộ để gọi retriever
            retrieved_docs = await retriever.ainvoke(query_question)

            # 5. Hợp nhất các documents thành một đoạn văn bản duy nhất
            retrieved_documents = [doc.page_content for doc in retrieved_docs]                
            context_documents_text = "\n\n".join(retrieved_documents)

            print('[RAG] Đã rút trích thành công từ vector database')
            return context_documents_text

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