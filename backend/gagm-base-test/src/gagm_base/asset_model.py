"""
asset_model.py

This module contains the base model for all assets.
"""

from pydantic import BaseModel, Field


class AssetModel(BaseModel):
    """
    Base model for all assets.
    """

    notes: str = Field(default_factory=str, description="Markdown notes of the asset", exclude=True)
    db_id: str = Field(description="DB id of the asset", alias="_id", default=None, serialization_alias="_id")
    db_key: str = Field(description="DB key of the asset", alias="_key", serialization_alias="_key", min_length=1)

    class Config:
        """
        Configuration of the AssetModel
        """

        title = "AssetModel"
        description = "The base class for all other assets."
        version = "v1"
        populate_by_name = True
        frozen = True
