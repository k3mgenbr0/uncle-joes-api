from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    member_id: str
    name: str
    email: EmailStr
