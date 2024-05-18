import logging

from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import auth_models
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


@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(auth_models.User).all()


@router.get("/tags")
async def get_tags():
    return ""



@router.get("/keys")
async def get_keys():
    return ""
