# 🌦️ YOUR-WEATHER-DRIVEN-HEALTH-COMPANION

## 📋 Bảng Setup Hệ Thống

| Bước | Thành phần / Mục tiêu                 | Lệnh / Thao tác                                                                                                  |
|------|---------------------------------------|------------------------------------------------------------------------------------------------------------------|
| **1** | **Khởi tạo DB & Cache với Docker**    | Tạo file `docker-compose.yml` với Redis, PostgreSQL, ChromaDB. <br> Chạy: <br>```docker-compose up -d```         |
| **2** | **Tạo môi trường ảo & cài thư viện** | ```bash<br>python -m venv venv<br>source venv/bin/activate   # hoặc venv\Scripts\activate (Windows)<br>pip install -r requirements.txt<br>``` |
| **3.1** | **Worker thu thập dữ liệu**        | ```bash<br>python -m worker.worker<br>```                                                                        |
| **3.2** | **Worker gợi ý bị động**           | ```bash<br>python -m passive_suggestion.suggest_worker<br>```                                                    |
| **3.3** | **Worker xử lý Chatbot Agent**     | ```bash<br>python -m chatbot.ai_agent<br>```                                                                     |
| **3.4** | **Scheduler (lập lịch tác vụ)**    | ```bash<br>python -m scheduler.scheduler<br>```                                                                  |
| **3.5** | **Khởi chạy FastAPI Backend**      | ```bash<br>uvicorn backend.app:app --reload<br>```                                                               |
| **4** | **Tạo tunnel bằng Ngrok**            | ```bash<br>ngrok http 8000<br>``` <br>👉 Copy URL được tạo để frontend kết nối đến backend.                       |
| **5** | **Deploy frontend (Vite + React)**   | Deploy thư mục `vite-project` lên **Vercel**. <br>Thêm URL từ ngrok vào biến môi trường trên Vercel.              |

---

## ⚙️ Hướng dẫn chi tiết triển khai trên VPS

### 1. Cài đặt Docker & Docker Compose
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
```
docker-compose.yml
```yaml
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
```

Khởi chạy các dịch vụ
```bash 
docker-compose up -d
```

Kiểm tra container đang chạy
```bash
docker ps
```

### 2. Khởi chạy Backend & Worker
```bash
# tạo môi trường ảo
python -m venv venv
source venv/bin/activate   # hoặc venv\Scripts\activate (Windows)

# cài thư viện
pip install -r requirements.txt

# khởi động worker và scheduler
python -m worker.worker
python -m passive_suggestion.suggest_worker
python -m chatbot.ai_agent
python -m scheduler.scheduler

# chạy FastAPI
uvicorn backend.app:app --reload
```

### 3. Kết nối Internet qua Ngrok (dành cho demo)
```bash
ngrok http 8000
```
