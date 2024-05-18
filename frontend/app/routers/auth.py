import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import auth_crud
from auth_schemas import User, UserCreate
from database import SessionLocal

logger = logging.getLogger("uvicorn")

# auth_models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# class User(Base):
#     """
#     Represents the users table in the database.
#     """
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)


@router.post("/api/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return auth_crud.create_user(db=db, user=user)


@router.get("/api/users/", response_model=list[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = auth_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/api/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = auth_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/api/users/{user_id}", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = auth_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return auth_crud.delete_user(db=db, user_id=user_id)


# class Permission(Base):
#     """
#     Represents the permissions table in the database.
#     """
#     __tablename__ = "permissions"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)
#     description = Column(String)


# class HasPermission(Base):
#     """
#     Represents the table that connects users to permissions in the database.
#     """
#     __tablename__ = "has_permissions"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     permission = Column(Integer, ForeignKey("permissions.id"))


def register(user: UserCreate):
    pass


async def get_user(request: Request):
    pass
