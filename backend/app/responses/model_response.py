"""
model_response.py

This file contains
"""

from pydantic import BaseModel


class ModelResponse(BaseModel):
    """
    A response class that contains information about an user uploaded model in the API
    """

    model_name: str
    model_schema: dict
