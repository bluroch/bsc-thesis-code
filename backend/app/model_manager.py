"""
model_manager.py

This file contains the ModelLoader class which is responsible for loading all models.
"""

import logging
import os
from copy import deepcopy
from datetime import datetime
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Any, List, Optional, Tuple, Type, TypeVar

from pydantic import create_model
from pydantic.fields import FieldInfo

from arango_connector import ArangoDB

from gagm_base.asset_model import AssetModel
from gagm_base.edge_model import EdgeModel
from gagm_base.node_model import NodeModel


logger = logging.getLogger("uvicorn")


class NoModelsFoundError(Exception):
    """
    Raised when no models are found.
    """

    pass


class ModelNotFoundError(Exception):
    """
    Raised when a model is not found.
    """

    pass


class ModelManager(object):
    """
    The ModelLoader class is responsible for loading all models.
    """

    _instance = None
    _models_loaded = False

    _models: dict[str, dict[str, Type[AssetModel]]] = {"node": {}, "edge": {}}
    _all_optional_models: dict[str, Type[AssetModel]] = {}
    models_directory_path: Path = Path(__file__).parent.resolve() / "models"
    last_reload: datetime

    def __init__(self, db: ArangoDB = ArangoDB()):
        if not self._models_loaded:
            self.load_models()
            db.init_collections(self._models)
            self._models_loaded = True

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating the object ModelManager")
            cls._instance = super(ModelManager, cls).__new__(cls)

        return cls._instance

    def reload_models(self):
        """
        Reload all models.
        """
        self._models = {"node": {}, "edge": {}}
        self.load_models()

    def load_models(self, model_path: Path = models_directory_path):
        """
        Load all models from the specified directory.

        Args:
            model_path (Path): The path to the directory containing the models.
        """
        for file_path in model_path.glob("*.py"):
            if str(file_path).endswith("__init__.py"):
                continue
            logger.info("Checking %s", file_path)
            module = import_module(f"models.{file_path.stem}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, (AssetModel, EdgeModel, NodeModel))
                    and attribute not in [AssetModel, EdgeModel, NodeModel]
                ):
                    model_name: str = attribute.__name__
                    if issubclass(attribute, NodeModel):
                        self._models["node"][model_name] = attribute
                        # self._node_type_models[model_name] = attribute
                        logger.debug("Loaded node model %s", model_name)
                    elif issubclass(attribute, EdgeModel):
                        self._models["edge"][model_name] = attribute
                        # self._edge_type_models[model_name] = attribute
                        logger.debug("Loaded edge model %s", model_name)
                    else:
                        logger.warning(
                            "Model %s is not a child of the base classes, ignoring",
                            model_name,
                        )
                        continue
                    self._all_optional_models[model_name] = self._make_partial_model(
                        attribute
                    )
                else:
                    continue
        if len(self._models["node"]) + len(self._models["edge"]) == 0:
            logger.warning("No models found.")

        logger.info(
            "Loaded %d node models and %d edge models",
            len(self._models["node"]),
            len(self._models["edge"]),
        )
        logger.info("Loaded models: %s", self._models)
        logger.info("Partial models: %s", self._all_optional_models)
        self.last_reload = datetime.now()

    def remove_model(self, model_name: str) -> None:
        """
        Remove a model.

        Args:
            model_name (str): The name of the model.
        """
        if self.is_model_present(model_name):
            for models_of_type in self._models.values():
                if model_name in models_of_type:
                    os.remove(f"models/{model_name}.py")
                    del models_of_type[model_name]
                    return
        raise ModelNotFoundError(f"Model not found: {model_name}")

    def get_model_schemas(self) -> dict[str, dict]:
        """
        Get all models.

        Returns:
            dict[str, dict]: A response containing all model schemas.
        """
        model_schemas: dict[str, dict] = {}
        for model_type in self._models.values():
            model_name: str
            for model_name, model_class in model_type.items():
                model_schemas[model_name] = model_class.model_json_schema(
                    mode="serialization"
                )
        if not model_schemas:
            raise NoModelsFoundError("No models found")
        logger.debug("Returning %d models", len(model_schemas.keys()))
        return model_schemas

    def get_model_schema(self, model_name: str) -> dict:
        """
        Get a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: The model schema.
        """
        model: Type[AssetModel] = self.get_model(model_name)
        return model.model_json_schema(mode="serialization")

    def get_model(self, model_name: str) -> Type[AssetModel]:
        """
        Get a specific model.

        Args:
            model_name (str): The name of the model.

        Raises:
            ValueError: If the model is not found.

        Returns:
            Type[AssetModel]: The model.
        """
        if self.is_model_present(model_name):
            for models_of_type in self._models.values():
                if model_name in models_of_type:
                    return models_of_type[model_name]

        raise ModelNotFoundError(f"Model not found: {model_name}")

    def get_edge_models(self) -> dict[str, Type[EdgeModel]]:
        """
        Get all edge models.

        Returns:
            dict[str, Type[EdgeModel]]: The edge models.
        """
        return self._models["edge"] # type: ignore

    def get_node_models(self) -> dict[str, Type[NodeModel]]:
        """
        Get all node models.

        Returns:
            dict[str, Type[NodeModel]]: The node models.
        """
        return self._models["node"] # type: ignore

    def get_all_models(self) -> dict[str, Type[AssetModel]]:
        """
        Get all models.

        Returns:
            dict[str, Type[AssetModel]]: All models.
        """
        return self._models

    def is_model_present(self, model_name: str) -> bool:
        """
        Check if a model is present.

        Args:
            model_name (str): The name of the model.

        Returns:
            bool: True if the model is present, False otherwise.
        """
        return (
            model_name in self._models["node"].keys()
            or model_name in self._models["edge"].keys()
        )

    def get_all_model_names(self) -> List[str]:
        """
        Returns the name of all available models.

        Returns:
            List[str]: List of model names.
        """
        return list(self.get_model_schemas().keys())

    def _make_field_optional(
        self, field: FieldInfo, default: Any = None
    ) -> Tuple[Any, FieldInfo]:
        """
        Make a Pydantic model's field optional.

        Source: https://github.com/pydantic/pydantic/issues/3120#issuecomment-1528030416

        Args:
            field (FieldInfo): The field to make optional.
            default (Any, optional): Default data of the field. Defaults to None.

        Returns:
            Tuple[Any, FieldInfo]: The optional field.
        """
        new_field = deepcopy(field)
        new_field.default = default
        new_field.annotation = Optional[field.annotation]  # type: ignore
        return (new_field.annotation, new_field)

    AssetModelT = TypeVar("AssetModelT", bound=AssetModel)

    def _make_partial_model(self, model: Type[AssetModelT]) -> Type[AssetModelT]:
        """
        Make a Pydantic model partial (a model where all fields are optional).
        Used to make PATCH routes.

        Source: https://github.com/pydantic/pydantic/issues/3120#issuecomment-1528030416

        Args:
            model (Type[AssetModelT]): The model to make partial.

        Returns:
            Type[AssetModelT]: The partial model.
        """
        logger.debug("Making model %s partial", model.__name__)
        return create_model(
            f"Partial{model.__name__}",
            __base__=model,
            __module__=model.__module__,
            **{
                field_name: self._make_field_optional(field_info)
                for field_name, field_info in model.model_fields.items()
            },
        )  # type: ignore

    def get_all_optional_model(self, model_name: str) -> Type[AssetModel]:
        if self.is_model_present(model_name):
            return self._all_optional_models[model_name]

        raise ModelNotFoundError(f"Model not found: {model_name}")

    def get_enum(self) -> Enum:
        return Enum(self.get_all_model_names)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loader = ModelManager()

    print(loader.get_model_schemas())
