from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="User Management API",
    description="A simple API for managing users",
    version="1.0.0"
)

# In-memory data
users: List[str] = []

class UserResponse(BaseModel):
    users: List[str]
    count: int

class MessageResponse(BaseModel):
    message: str
    status: str = "success"

class UserRequest(BaseModel):
    name: str

@app.get("/", response_model=MessageResponse)
def hello_world():
    return MessageResponse(message="Hello, World!")

@app.get("/users", response_model=UserResponse)
def get_all_users():
    return UserResponse(users=users, count=len(users))

@app.post("/user", response_model=UserResponse)
def add_user(user_request: UserRequest):
    name = user_request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if name in users:
        raise HTTPException(status_code=409, detail="User already exists")
    users.append(name)
    return UserResponse(users=users, count=len(users))



# Add other endpoints as you have
