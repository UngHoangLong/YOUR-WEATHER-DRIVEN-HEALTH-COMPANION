from pydantic import BaseModel
from typing import Optional
class UserCityInput(BaseModel):
    # user_id: int  bỏ vì đã dùng jwt
    city_id: int

class ChatbotRequest(BaseModel):
    city_id: int
    # user_id: int
    user_input: str

class ChatbotResponse(BaseModel):
    request_id: str
    status: str
    message: str

class ResultResponse(BaseModel):
    request_id: str
    status: str
    message: str
    data: Optional[str] = None

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class DiseaseUpdate(BaseModel):
    disease_id: int
    describe_disease: str