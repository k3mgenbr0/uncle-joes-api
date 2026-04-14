from pydantic import BaseModel, EmailStr

from app.schemas.member import Member


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    member_id: str
    name: str
    email: EmailStr


class SessionResponse(BaseModel):
    authenticated: bool
    member: Member | None = None


class LogoutResponse(BaseModel):
    authenticated: bool
