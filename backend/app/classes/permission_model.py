from typing import Any, Type

from pydantic import BaseModel

from .models.base.asset_model import AssetModel
from .models.base.asset_tag import AssetTag


class Permission(BaseModel):
    pass


class AssetPermission(Permission):
    model_type: Type[AssetModel]


class TagPermission(Permission):
    tag_type: Type[AssetTag]


def check_permission(object: AssetModel, user: Any):
    return True
