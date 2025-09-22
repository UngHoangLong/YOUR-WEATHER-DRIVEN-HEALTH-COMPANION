from fastapi import APIRouter, Depends, HTTPException, status
import uuid
import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
# Import Pydantic model từ file model.py
from .model import UserCityInput, ChatbotRequest, ChatbotResponse, ResultResponse, UserRegister, UserLogin, DiseaseUpdate
# Import các client khác (giả định đã tồn tại)
from core.postgresql_client import get_db
from core.redis_client import get_redis_data, get_redis_cache_conn, get_redis_history_conn
from .jwt_utils import create_access_token, get_current_user, verify_access_token
from datetime import timedelta
from .storage_history_message import append_chat_history, get_recent_chat_history
from chatbot.chat_summary import summarize_chat_history

# Khởi tạo APIRouter
router = APIRouter()

# endpoint đăng ký tài khoản
@router.post("/register")
async def register(user: UserRegister, db_pool=Depends(get_db)):
    async with db_pool.acquire() as conn:
        # Check trùng username
        exists_username = await conn.fetchval(
            "SELECT 1 FROM users WHERE username=$1;", user.username
        )
        if exists_username:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Check trùng email
        exists_email = await conn.fetchval(
            "SELECT 1 FROM users WHERE email=$1;", user.email
        )
        if exists_email:
            raise HTTPException(status_code=400, detail="Email already exists")

        # Hash password
        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Insert user
        query = """
            INSERT INTO users (username, email, password)
            VALUES ($1, $2, $3);
        """
        await conn.execute(query, user.username, user.email, hashed_pw)

    return {"message": "User registered successfully"}

# endpoint đăng nhập
@router.post("/login")
async def login(user: UserLogin, db_pool=Depends(get_db)):
    async with db_pool.acquire() as conn:
        query = "SELECT user_id, password FROM users WHERE username=$1;"
        row = await conn.fetchrow(query, user.username)

        if not row:
            raise HTTPException(status_code=400, detail="Invalid username or password")

        stored_pw = row["password"]
        if not bcrypt.checkpw(user.password.encode("utf-8"), stored_pw.encode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid username or password")

        # Nếu đúng → tạo JWT token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"user_id": row["user_id"], "username": user.username},
            expires_delta=access_token_expires
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer"
        }

# endpoint này giúp cập nhật city_id cho user và thu thập dữ liệu dự đoán nếu chưa có trong database
@router.post("/update_city_info_for_user")
async def update_city_info_for_user(
    input_data: UserCityInput,
    user_id: int = Depends(get_current_user),   # lấy user_id từ JWT
    db_pool = Depends(get_db),
    redis_data = Depends(get_redis_data)
):
    city_id = input_data.city_id
    QUEUE_DATA = os.getenv("QUEUE_DATA", "queue_data")

    async with db_pool.acquire() as conn:
        # Bước 1: Thêm record vào bảng user_city (nếu chưa có)
        query_user_city = """
            INSERT INTO user_city (user_id, city_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, city_id) DO NOTHING;
        """
        await conn.execute(query_user_city, user_id, city_id)
        print(f"Đã kiểm tra và thêm/bỏ qua user_city: user_id={user_id}, city_id={city_id}")

        # Bước 2: Kiểm tra và push job vào Redis queue
        query_check_weather = "SELECT EXISTS(SELECT 1 FROM weather WHERE city_id = $1);"
        exists_in_weather = await conn.fetchval(query_check_weather, city_id)

        if not exists_in_weather:
            print(f"Không tìm thấy city_id {city_id} trong bảng weather. Đang lấy thông tin city.")

            query_get_city_info = """
                SELECT longitude, latitude
                FROM city
                WHERE city_id = $1;
            """
            city_info = await conn.fetchrow(query_get_city_info, city_id)

            if city_info:
                job_data = {
                    "job_id": str(uuid.uuid4()),
                    "city_id": city_id,
                    "longitude": city_info["longitude"],
                    "latitude": city_info["latitude"]
                }
                await redis_data.lpush(QUEUE_DATA, json.dumps(job_data))
                print(f"Đã push job {job_data['job_id']} vào Redis queue.")
            else:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy thông tin của city_id {city_id}.")
        else:
            print(f"city_id {city_id} đã tồn tại trong bảng weather. Không cần push job.")

    return {"message": "Thao tác hoàn tất."}

# Endpoint cập nhật thông tin bệnh
@router.put("/update_disease")
async def update_user_disease_info(
    payload: DiseaseUpdate,
    user_id: int = Depends(get_current_user),
    db_pool = Depends(get_db)
):
    query = """
        UPDATE users
        SET disease_id = $1,
            describe_disease = $2
        WHERE user_id = $3;
    """
    async with db_pool.acquire() as conn:
        result = await conn.execute(query, payload.disease_id, payload.describe_disease, user_id)

    if result.startswith("UPDATE 1"):
        return {"status": "success", "message": "Cập nhật thông tin bệnh thành công"}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy user hoặc không cập nhật được")


#------ Endpoint giúp lấy dữ liệu weather, climate, uv để trực qua trên front-end
@router.get("/get_data_to_visualize/{city_id}")
async def get_data_to_visual(
    city_id: int,
    db_pool = Depends(get_db)
):
    SQL_GET_DATA_TO_VISUALIZE = """
        SELECT 
            w.report_day, w.report_month, w.report_year, w.period, w.humidity,
            w.temp, w.feels_like, w.weather_description, w.weather_icon, w.pop, w.wind_speed,
            cl.aqi, cl.pm2_5, cl.pm10, u.uvi
        FROM weather w
        JOIN climate cl ON w.city_id = cl.city_id
        JOIN uv u ON w.city_id = u.city_id
        WHERE w.city_id = $1
        AND w.report_day = cl.report_day AND w.report_day = u.report_day
        AND w.report_month = cl.report_month AND w.report_month = u.report_month
        AND w.report_year = cl.report_year AND w.report_year = u.report_year
        AND w.period = cl.period AND w.period = u.period
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(SQL_GET_DATA_TO_VISUALIZE, city_id)

    if not rows:
        raise HTTPException(status_code=404, detail=f"Không có dữ liệu cho city_id {city_id}")
    # Chuyển từ list record -> list dict
    data = [dict(row) for row in rows]

    # Gom nhóm theo ngày
    grouped = {}
    for row in data:
        key = (row['report_day'], row['report_month'], row['report_year'])
        if key not in grouped:
            grouped[key] = {
                "day": row['report_day'],
                "month": row['report_month'],
                "year": row['report_year'],
                "periods": []
            }
        # Thêm period vào ngày
        grouped[key]["periods"].append({
            "period": row['period'],
            "temp": row['temp'],
            "feels_like": row['feels_like'],
            "weather_description": row['weather_description'],
            "weather_icon": row['weather_icon'],
            "pop": row['pop'],
            "humidity": row['humidity'],
            "wind_speed": row['wind_speed'],
            "aqi": row['aqi'],
            "pm2_5": row['pm2_5'],
            "pm10": row['pm10'],
            "uvi": row['uvi']
        })

    # Define a custom order for periods
    period_order = {
        'Early Morning': 1,
        'Morning': 2,
        'Noon': 3,
        'Afternoon': 4,
        'Evening': 5
    }

    # Chuyển về list, sort ngày và sort periods trong ngày
    result = list(grouped.values())
    result.sort(key=lambda x: (x['year'], x['month'], x['day']))
    for item in result:
        item["periods"].sort(key=lambda x: period_order.get(x['period'], 99))

    return {"status": "success", "data": result}  # khi có dữ liệu

#-----------
# endpoint lấy passive_suggest_tion cho user và city mà user thiết lặp
@router.get("/get_passive_suggestion/{city_id}")
async def get_passive_suggestion(
    city_id: int,
    user_id: int = Depends(get_current_user),  # lấy user_id từ JWT
    db_pool = Depends(get_db)
):
    SQL_GET_PASSIVE_SUGGESTION = """
        SELECT 
            s.text_suggestion
        FROM suggestion s
        WHERE s.city_id = $1 AND s.user_id = $2
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetch(SQL_GET_PASSIVE_SUGGESTION, city_id, user_id)

    if not row:
        # Không tìm thấy dữ liệu phù hợp
        raise HTTPException(status_code=404, detail="Không có dữ liệu suggestion cho user và city này")
    
    return {"status": "success", "suggestion": row[0]['text_suggestion']}

#------------------------------------------------------------------------------------------------------
#---------Endpoint_chatbot----------
QUEUE_CHATBOT = os.getenv("QUEUE_CHATBOT", "queue_chatbot")
MAX_HISTORY = 10  # số tin nhắn tối đa lưu cho mỗi user
NUM_HISTORY_FOR_CONTEXT = 6  # số tin nhắn lấy ra để gửi cho agent
@router.post("/submit_chatbot_query", response_model=ChatbotResponse)
async def submit_chatbot_query(
    request_body: ChatbotRequest,
    redis_data = Depends(get_redis_data),
    redis_history = Depends(get_redis_history_conn),
    user_id: int = Depends(get_current_user)  # lấy user_id từ JWT
) -> Dict[str, Any]:
    """
    Nhận yêu cầu từ người dùng, tạo job và đẩy vào Redis Queue để xử lý bất đồng bộ.
    Trả về request_id để người dùng có thể lấy kết quả sau.
    """
    # 1. Tạo request_id duy nhất
    request_id = str(uuid.uuid4())
    # lấy bảng tóm tắt 6 tin nhắn của user_id trong redis db2
    history_context_raw = await get_recent_chat_history(user_id, NUM_HISTORY_FOR_CONTEXT, redis_history)
    if history_context_raw:
        # Chỉ gọi tóm tắt khi có dữ liệu
        history_context_summary = await summarize_chat_history(history_context_raw)
    else:
        history_context_summary = ""  # user mới, chưa có lịch sử
    # push user_input vào trong redis db để lưu dữ liệu lịch sử. Nhớ strim
    await append_chat_history(user_id, "user", request_body.user_input, redis_history)
    # 2. Tạo job data bao gồm tất cả các tham số và request_id
    job_data = {
        "request_id": request_id,
        "city_id": request_body.city_id,
        "user_id": user_id,
        "user_input": request_body.user_input,
        "history_context": history_context_summary
    }
    
    # 3. Đẩy job vào queue (sử dụng đối tượng đã được Dependency Injection cung cấp)
    try:
        await redis_data.lpush(QUEUE_CHATBOT, json.dumps(job_data))
        print(f"[API] Đã đẩy job {request_id} vào queue '{QUEUE_CHATBOT}'")
    except Exception as e:
        print(f"[API ERROR] Không thể kết nối Redis hoặc đẩy job: {e}")
        # Trả về lỗi 500 nếu có sự cố
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error: Could not process request."
        )
    
    # 4. Trả về request_id và thông báo thành công cho người dùng
    return {
        "request_id": request_id,
        "status": "processing",
        "message": "Yêu cầu đang được xử lý. Vui lòng sử dụng request_id để lấy kết quả."
    }

@router.get("/get_chatbot_result/{request_id}", response_model=ResultResponse)
async def get_chatbot_result(
    request_id: str,
    redis_cache = Depends(get_redis_cache_conn)
) -> ResultResponse:
    """
    Sử dụng request_id để lấy kết quả từ Redis Cache.
    """
    # 1. Lấy dữ liệu từ Redis cache bằng request_id
    result = await redis_cache.get(request_id)

    # 2. Kiểm tra nếu không có dữ liệu
    if result is None:
        # Trả về 202 Accepted khi kết quả chưa sẵn sàng
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "request_id": request_id,
                "status": "processing",
                "message": "Kết quả chưa sẵn sàng. Vui lòng thử lại sau."
            }
        )
    
    # Trả về khi có kết quả
    return ResultResponse(
        request_id=request_id,
        status="completed",
        message="Đã tìm thấy kết quả.",
        data=result
    )

