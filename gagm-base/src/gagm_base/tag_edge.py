"""
tag_edge.py

This module contains the class of the base model for tag edges.
"""

# from typing import ClassVar, List

from .edge_model import EdgeModel


class TagEdge(EdgeModel):
    """
    Base model for for tag edges.
    """
    # origin_type: ClassVar[List[str]] = ["AssetTag"]
    # target_type: ClassVar[List[str]] = []

    class Config:
        """
        Configuration of the TagEdge
        """

        title: str = "TagEdge"
        description: str = "Base model for tag edges."
        version = "v1"
