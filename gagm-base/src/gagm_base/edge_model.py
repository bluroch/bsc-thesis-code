"""
edge_model.py

This module contains the class of the base model for edges.
"""

from typing import ClassVar, List

from .asset_model import AssetModel
from pydantic import Field


class EdgeModel(AssetModel):
    """
    Base model for edges.
    """

    origin_id: str = Field(description="ID of the origin Node", alias="_from", default=None)
    target_id: str = Field(description="ID of the target Node", alias="_to", default=None)
    origin_type: ClassVar[List[str]] = Field(description="Type of the origin Node", default=[])
    target_type: ClassVar[List[str]] = Field(description="Type of the target Node", default=[])

    class Config:
        """
        Configuration of the EdgeModel
        """

        title: str = "EdgeModel"
        description: str = "Base model for edges."
        version = "v1"
