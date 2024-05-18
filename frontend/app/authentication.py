import logging
from fastapi import Depends, HTTPException, Request, status
from auth_models import User
from sqlalchemy.orm import Session
from database import SessionLocal


logger = logging.getLogger("uvicorn")


class AuthException(Exception):
    ...


def get_db():
    """
    Provides the database connection.

    Yields:
        Session: The database connection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user():
    ...


def is_authenticated(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Checks if the request contains a valid session cookie.

    Args:
        request (Request): The request object.

    Raises:
        HTTPException: 401 if the user is not authenticated.

    Returns:
        User: The authenticated user.
    """
    user_email = request.session.get("user")
    # logger.info(f"Login check\n{request.session=}")
    # logger.info(f"{user_email=}")
    user: User = db.query(User).filter_by(email=user_email).first()
    if not user_email or not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def is_admin(user: User = Depends(is_authenticated)):
    """
    Checks if the user is an admin.

    Args:
        user (User): The authenticated user.

    Raises:
        HTTPException: 403 if the user is not an admin.

    Returns:
        User: The authenticated user.
    """
    if not bool(user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user