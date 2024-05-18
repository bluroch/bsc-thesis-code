"""
tag_model.py

This module contains the class of the base model for tags.
"""

from pydantic import Field
from .asset_model import AssetModel


class AssetTag(AssetModel):
    """
    Base model for for tags.
    """
    name: str = Field(description="Name of the tag", default=None)

    class Config:
        """
        Configuration of the AssetTag
        """

        title: str = "AssetTag"
        description: str = "Base model for tags."
        version = "v1"
