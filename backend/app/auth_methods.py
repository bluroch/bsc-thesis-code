import hashlib
import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Security, Header, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

import auth_crud
from rel_db import SessionLocal
from auth_models import User

logger = logging.getLogger("uvicorn")

# Base.metadata.create_all(bind=engine)

debug_mode = os.environ.get("APP_DEBUG") == "true"

api_keys = [hashlib.sha512(b"test_key").hexdigest()]

frontend_key = os.environ.get("FRONTEND_SECRET") or "secret_key"

frontend_key_header = APIKeyHeader(name="X-FRONTEND-API-KEY", auto_error=False, scheme_name="Backend secret")
frontend_user_id_header = APIKeyHeader(name="X-FRONTEND-USER-ID", auto_error=False, scheme_name="Frontend user ID")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False, scheme_name="API key")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_api_key(
    db: Session = Depends(get_db), key: str = Security(api_key_header)
) -> Optional[User]:
    if not key:
        return
    owner_of_key = auth_crud.check_key(
        db, key
    )
    # logger.info(f"{owner_of_key=}")
    # logger.info(f"{key=}")
    return owner_of_key


def check_frontend_key(
    db: Session = Depends(get_db),
    frontend_secret: str = Security(frontend_key_header),
    user_id: str = Security(frontend_user_id_header),
) -> Optional[User]:
    # logger.info(f"{user_id=}\n{frontend_secret=}\n{frontend_key=}")
    if not (frontend_secret and user_id):
        return
    user: User = db.query(User).filter_by(id=user_id).first()
    key_check = frontend_secret == frontend_key
    return user if key_check else None


def authenticate_user(
    api_key_result: User = Depends(authenticate_api_key),
    frontend_auth_result: User = Depends(check_frontend_key),
) -> str:
    """
    Provides authentication for the API.
    Two authentication methods are implemented, authentication fails if both
    are present (a request should only have headers for one auth method at once).

    Args:
        api_key_result (User, optional): API key based authentication.
        frontend_auth_result (User, optional): Frontend secret based authentication.

    Raises:
        HTTPException: 401 if authentication fails

    Returns:
        str: Email of the authenticated user
    """
    # logger.info(f"{api_key_result=}")
    # logger.info(f"{frontend_auth_result=}")
    # Ensures that only one type of authentication was successful
    if bool(api_key_result) + bool(frontend_auth_result) != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Unauthenticated {api_key_result=}, {frontend_auth_result=}"
        )
    user: User = api_key_result or frontend_auth_result
    # logger.info(f"Authenticated {str(user.email)}")
    return str(user.email)
