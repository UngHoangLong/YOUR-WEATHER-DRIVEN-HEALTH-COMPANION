from fastapi import FastAPI
from dotenv import load_dotenv
from .router import router
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain truy cập
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API!"}

# python -m uvicorn backend.app:app --reload ( chạy từ thư mục gốc )