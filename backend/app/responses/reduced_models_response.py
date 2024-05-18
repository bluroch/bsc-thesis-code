"""
models_response.py

The ModelsResponse module contains the ModelsResponse class,
which is the response model for the get_models endpoint.
"""

from pydantic import BaseModel, computed_field


class ReducedModelsResponse(BaseModel):
    """
    The ModelsResponse class is the response model for the get_models endpoint.
    """

    model_names: list[str]

    @computed_field
    @property
    def count(self) -> int:
        """
        Counts the models.

        Returns:
            int: Count of the available models.
        """
        return len(self.model_names)
