import logging
import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from auth_models import User, APIKey
from auth_schemas import APIKeyUpdate, UserCreate, APIKeyCreate

logger = logging.getLogger("uvicorn")

def get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def check_password(db: Session, email: str, password_hash: str) -> bool:
    user = db.query(User).filter_by(email=email, hashed_password=password_hash).first()
    return False if not user else True


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = hashlib.sha512(user.password.encode("utf-8")).hexdigest()
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> User:
    db_user = get_user(db, user_id=user_id)
    db.delete(db_user)
    db.commit()
    return db_user


def get_key(db: Session, key_id: int):
    return db.query(APIKey).filter(APIKey.id == key_id).first()


def check_key(db: Session, key_str: str) -> Optional[User]:
    key = (
        db.query(APIKey)
        .filter_by(key_hash=hashlib.sha512(key_str.encode()).hexdigest())
        .first()
    )
    logger.info(key_str)
    logger.info(hashlib.sha512(key_str.encode()).hexdigest())
    logger.info(key)
    return None if not key else db.query(User).filter_by(id=key.user_id).first()


def create_key(db: Session, key: APIKeyCreate) -> APIKey:
    db_key = APIKey(
        user_id=key.user_id,
        key_hash=key.key,
        key_type=key.key_type,
        creation_date=key.creation_date,
        active=key.active,
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


def update_key(db: Session, key: APIKeyUpdate) -> APIKey:
    db.query(APIKey).filter(APIKey.id == key.id).update({"active": key.active})
    db.commit()
    return db.query(APIKey).filter(APIKey.id == key.id).first()
