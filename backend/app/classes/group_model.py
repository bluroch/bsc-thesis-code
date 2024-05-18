from typing import Set

from pydantic import BaseModel

from classes.permission_model import Permission
from classes.user_model import User


class Group(BaseModel):
    users: Set[User]
    permissions: Set[Permission]
