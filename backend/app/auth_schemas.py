from datetime import datetime
import random
from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
        from_attributes = True


class APIKeyBase(BaseModel):
    key: str
    key_type: int


class APIKeyCreate(APIKeyBase):
    key: str = hex(random.getrandbits(128))[2:]
    user_id: int
    key_type: int = 2
    creation_date: str = datetime.now().isoformat()
    active: bool = True


class APIKeyUpdate(APIKeyBase):
    id: int
    active: bool


class APIKey(APIKeyBase):
    id: int
    user_id: int
    key_type: int
    creation_date: str
    active: bool

    class Config:
        from_attributes = True
        from_attributes = True
