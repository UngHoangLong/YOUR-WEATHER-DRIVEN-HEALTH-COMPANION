from core.postgresql_client import get_db
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from typing import Dict, List
import asyncio
import json
import chromadb
import google.api_core.exceptions
from dotenv import load_dotenv, find_dotenv
import os
from .create_query_question import make_query_question

load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
CHROMA_SERVER_HOST = os.environ.get("CHROMA_SERVER_HOST", "103.133.224.14")
CHROMA_SERVER_PORT = int(os.environ.get("CHROMA_SERVER_PORT", 8000))

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

async def rag_for_suggestion(job_data: dict):
    """
    Thực hiện quy trình RAG để tạo gợi ý sức khỏe hoàn chỉnh bằng LLM.
    
    Args:
        job_data (Dict): Dữ liệu job từ Redis chứa thông tin user, city và daily data.

    Returns:
        Lưu thông tin vào bảng suggestion
    """

    if not GEMINI_API_KEYS:
        raise ValueError("Không tìm thấy GEMINI API keys nào trong file .env.")
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            # Lấy thông tin cần thiết từ job_data
            user_id = job_data.get('user_id')
            city_id = job_data.get('city_id')
            
            # Kiểm tra xem user_id và city_id có tồn tại không
            if user_id is None or city_id is None:
                logger.error("Dữ liệu job_data không chứa user_id hoặc city_id.")
                return

            # Lấy ngày, tháng, năm từ daily_data đầu tiên
            first_daily_data = job_data.get('daily_data')[0]
            report_time = first_daily_data.get('report_time')
            report_year = report_time.get('report_year')
            report_month = report_time.get('report_month')
            report_day = report_time.get('report_day')

            query_question, describe_disease = make_query_question(job_data) # vừa lấy query question lẫn describe_disease sau khi translate

            # gọi api_key tiếp theo
            api_key = await get_next_key()

            # 2. Khởi tạo mô hình embedding
            embeddings = GoogleGenerativeAIEmbeddings( # nó sẽ tự chuẩn hoá sau khi embedding
                model="gemini-embedding-001",
                task_type= "QUESTION_ANSWERING",
                google_api_key=api_key
            )
            print("[RAG] Initialized GoogleGenerativeAIEmbeddings model.")
            
            # 3. Khởi tạo Chroma vector store với client và embedding model
            collection_name = job_data.get('disease_name', 'respiratory')
            print('collection_name:', collection_name)
            vector_store = Chroma(
                client=chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT),
                collection_name=collection_name,
                embedding_function=embeddings
            )

            print(f"[RAG] Initialized Chroma vector store for collection: '{collection_name}'")

            # 4. Thực hiện tìm kiếm bất đồng bộ với retriever
            # `as_retriever` sẽ biến vector store thành một đối tượng có thể tìm kiếm
            # `k=5` sẽ tìm kiếm 5 tài liệu gần nhất

            retriever = vector_store.as_retriever(search_kwargs={"k": 2})
            # `ainvoke` là phương thức bất đồng bộ để gọi retriever
            retrieved_docs = await retriever.ainvoke(query_question)

            # 5. Hợp nhất các documents thành một đoạn văn bản duy nhất
            retrieved_documents = [doc.page_content for doc in retrieved_docs]                
            context_documents_text = "\n\n".join(retrieved_documents)
            
            # 6. Xây dựng prompt và gọi LLM để tạo phản hồi
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.7,
                max_output_tokens=4096,
                google_api_key=api_key
            )

            disease_name = job_data.get('disease_name', 'disease')

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", 
                    f"You are a specialist doctor for the '{disease_name}' disease. Based on the following information, provide useful health advice for a user with this disease. "
                    "Focus on the provided weather, climate, and UV factors. Your response must be clear, concise, and only focus on providing advice. "
                    "Do not mention that you used documents to answer. "
                    "Keep the total response under 250 words (or about 250 tokens). "
                    "Reference information:\n{context}"
                ),
                ("human", 
                    f"Based on the interpreted daily weather, climate, and UV information: {query_question}\n\n"
                    f"And the following disease description from that user: '{describe_disease}'\n\n"
                    f"Provide advice in **Vietnamese** for each period of the day (Morning, Noon, Afternoon, Evening, Night)."
                    f"Each period should be 1–3 sentences only."
                )
            ])
                
            # 7. Tạo chain và gọi LLM
            llm_chain = prompt_template | llm
            
            final_response = await llm_chain.ainvoke({
                "context": context_documents_text,
                "query_question": query_question
            })
            
            # kiểm tra xem có đang bị cut do MAX TOKEN không
            if hasattr(final_response, "response_metadata"):  # Nếu object có metadata
                finish_reason = final_response.response_metadata.get("finish_reason", "")
            if finish_reason != "STOP":  # Nếu không phải STOP
                print(f"[LLM WARNING] Response cut off, finish_reason={finish_reason}")

            print("\n[LLM Response] Generated final response.")
            if hasattr(final_response, "content") and final_response.content:
                text_suggestion = final_response.content
            else:
                print("[LLM WARNING] Empty content, fallback to raw response")
                text_suggestion = json.dumps(final_response.dict(), ensure_ascii=False)
            print('check_response_object: ', text_suggestion )
            pool = await get_db()
            async with pool.acquire() as conn:
                insert_query = """
                    INSERT INTO suggestion (user_id, city_id, text_suggestion, report_year, report_month, report_day)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (user_id, city_id) DO UPDATE SET
                        text_suggestion = EXCLUDED.text_suggestion,
                        report_year = EXCLUDED.report_year,
                        report_month = EXCLUDED.report_month,
                        report_day = EXCLUDED.report_day;
                """
                await conn.execute(
                    insert_query,
                    user_id, city_id, text_suggestion, report_year, report_month, report_day
                )
            print('Already Insert to Database')
            return
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


