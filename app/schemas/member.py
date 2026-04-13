from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")

    member_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    home_store: str | None = None


class MemberQueryParams(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class MemberPoints(BaseModel):
    member_id: str
    total_points: int
