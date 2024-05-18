import uuid

from pydantic import BaseModel
from datetime import datetime, timedelta

from auth_models import APIKeyType


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    active: bool = True


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyBase(BaseModel):
    key_hash: str
    user_id: int
    key_type: APIKeyType

    class Config:
        from_attributes = True


class ApiKey(ApiKeyBase):
    id: int
    active: bool
    expiration_date: datetime
    creation_date: datetime

    class Config:
        from_attributes = True


class ApiKeyUpdate(BaseModel):
    id: int
    active: bool

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    # key: str = str(uuid.uuid4())
    expiration_date: datetime
    creation_date: datetime = datetime.now()
    active: bool = True


class ApiKeyAdminQuery(BaseModel):
    expiration_date: datetime
    creation_date: datetime
    active: bool
    user_id: int
    id: int