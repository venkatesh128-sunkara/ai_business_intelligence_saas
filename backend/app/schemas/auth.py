from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None
    is_active: bool | None = None


class WorkspaceOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = ""


class UsageOut(BaseModel):
    year_month: str
    query_count: int
    query_limit: int
    storage_bytes: int
    storage_limit_mb: int
    dataset_count: int
    dataset_limit: int
