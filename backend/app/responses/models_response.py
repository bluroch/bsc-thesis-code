"""
models_response.py

The ModelsResponse module contains the ModelsResponse class,
which is the response model for the get_models endpoint.
"""

from pydantic import BaseModel, computed_field

from responses.model_response import ModelResponse


class ModelsResponse(BaseModel):
    """
    The ModelsResponse class is the response model for the get_models endpoint.
    """

    models: dict[str, ModelResponse]

    @computed_field
    @property
    def count(self) -> int:
        """
        Counts the models.

        Returns:
            int: Count of the available models.
        """
        return len(self.models.keys())
