from dataclasses import dataclass
from datetime import datetime
import enum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from rel_db import Base, engine


@dataclass
class User(Base):
    """
    Represents the users table in the database.
    """

    __tablename__ = "User"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    def __str__(self):
        return f"User({self.email}, {self.is_active=}, {self.is_admin=})"


class APIKeyType(enum.Enum):
    """
    Enums for the API key types.

    FRONTEND: Keys automatically generated by the frontend application for each user.
    USER_GENERATED: Keys generated by the users.
    """

    FRONTEND = 1
    USER_GENERATED = 2


@dataclass
class APIKey(Base):
    """
    Represents the API keys table in the database.
    """

    __tablename__ = "UserKey"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), index=True)
    # key_type: Mapped[str] = mapped_column(Enum(APIKeyType))
    key_hash: Mapped[str] = mapped_column(String, unique=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    expiration_date: Mapped[datetime] = mapped_column(DateTime)
    active: Mapped[bool] = mapped_column(Boolean, default=False)

class Tag(Base):
    """
    Represents tags that can be used to mark assets in the graph database.
    """

    __tablename__ = "Tag"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default="")


Base.metadata.create_all(engine)