from typing import Set

from pydantic import BaseModel

from classes.permission_model import Permission


class User(BaseModel):
    email: str
    name: str
    permissions: Set[Permission]
