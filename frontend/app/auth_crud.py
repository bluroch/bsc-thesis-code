import hashlib
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session

from auth_models import User, APIKey
import auth_schemas

# User functions
def get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def check_password(db: Session, email: str, password_hash: str) -> bool:
    user = db.query(User).filter_by(email=email, hashed_password=password_hash).first()
    if not user:
        return False
    return True


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: auth_schemas.UserCreate) -> auth_schemas.User:
    hashed_password = hashlib.sha512(user.password.encode("utf-8")).hexdigest()
    db_user = User(email=user.email, hashed_password=hashed_password, is_active=False, is_admin=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



def delete_api_keys_by_user_id(db: Session, user_id: int) -> None:
    db.query(APIKey).filter(APIKey.user_id == user_id).delete()
    db.commit()


def delete_user(db: Session, user_id: int) -> User:
    db_user = get_user(db, user_id=user_id)
    delete_api_keys_by_user_id(db, user_id)
    db.delete(db_user)
    db.commit()
    return db_user


def deactivate_user(db: Session, user_id: int) -> User:
    db_user = get_user(db, user_id=user_id)
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user


# API key functions
def create_api_key(db: Session, user_id: int, key: str, expiration_date: datetime) -> APIKey:
    hashed_key = hashlib.sha512(key.encode("utf-8")).hexdigest()
    db_key = APIKey(user_id=user_id, key_hash=hashed_key, expiration_date=expiration_date, active=True)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


def get_api_keys_by_user_id(db: Session, user_id: int) -> List[auth_schemas.ApiKey]:
    keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
    return keys


def get_all_api_keys(db: Session) -> List[APIKey]:
    return db.query(APIKey).all()


def update_api_key(db: Session, key_id: int, active: bool) -> APIKey | None:
    key: APIKey = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not key:
        return None

    key.active = active
    db.commit()
    db.refresh(key)
    return key
