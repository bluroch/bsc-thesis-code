"""
node_model.py

This module contains the class of the base model for nodes.
"""

from .asset_model import AssetModel


class NodeModel(AssetModel):
    """
    Base model for nodes.
    """

    class Config:
        """
        Configuration of the NodeModel
        """

        title: str = "NodeModel"
        description: str = "Base model for nodes."
        version = "v1"
