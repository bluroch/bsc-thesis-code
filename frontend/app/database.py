"""
This module creates and stores the connection to the relational database.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

CONFIG = {
    "user": os.environ.get("REL_DB_USER") or "gagm",
    "pass": os.environ.get("REL_DB_PASS") or "password",
    "host": os.environ.get("REL_DB_HOST") or "localhost",
    "port": os.environ.get("REL_DB_PORT") or 5432,
}


SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{CONFIG['user']}:{CONFIG['pass']}"
    + f"@{CONFIG['host']}:{CONFIG['port']}"
    + "/gagm"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
