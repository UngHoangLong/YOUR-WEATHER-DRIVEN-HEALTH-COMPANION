# YOUR-WEATHER-DRIVEN-HEALTH-COMPANION
Các bước setup

B1: Khởi tạo các container cơ sở dữ liệu Redis, ChromaDB và Postgresql trên server của bạn với docker-compose.yml như sau

docker-compose.yml

version: '3.9'

services:
  redis:
    image: redis:latest
    container_name: redis-server
    ports:
      - "6379:6379"
    restart: always
    command: ["redis-server", "--appendonly", "yes"]   # ép chạy master + bật AOF
    volumes:
      - ./redis_data:/data

  postgres:
    image: postgres:15
    container_name: postgres-server
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: kid14124869
      POSTGRES_DB: health_twin
    ports:
      - "5432:5432"
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    restart: always

  chromadb:
    image: chromadb/chroma:1.0.20
    container_name: chromadb-server
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_data:/chroma
    restart: always

B1: Tạo thư viện ảo và tải các thư viện từ requirements.txt về

pip install requirements.txt

B2: Ta sẽ vào thư mục chính và khởi chạy các worker như sau

Worker thu thập dữ liệu
python -m worker.worker

Worker tạo lời khuyên bị động
python -m passive_suggestion.suggest_worker 

Worker xử lý tác vụ chatbot
python -m chatbot.ai_agent

Khởi tạo cơ chế lặp lịch
python -m scheduler.scheduler

Khởi tạo FastAPI
python -m uvicorn backend.app:app --reload

B4: Tạo tunnel kết nối đến internet
Vì hiện tại server đang chạy local nên ta sẽ dùng ngrok để tạo tunnel dẫn kết nối từ internet đên port nội bộ ( giúp nhận request từ website)
ngrok http 8000
sau đó ta sẽ nhận được một link url, Website sẽ kết nối đến server ta thông qua link đó.

B5: Deploy thư mục vite-project lên trên vercel, sau đó thêm link url đã lấy từ ngrok thêm vào biến môi trường.

Chúc bạn thành công


