"""
This module contains the database related classes.
"""

import logging
import os
from enum import Enum
from typing import Type

from arango.client import ArangoClient
from arango.collection import EdgeCollection, VertexCollection, StandardCollection
from arango.database import Database, StandardDatabase
from arango.graph import Graph
from pydantic import BaseModel

from gagm_base.asset_model import AssetModel
from gagm_base.edge_model import EdgeModel
from gagm_base.node_model import NodeModel
from gagm_base.tag_model import AssetTag
from gagm_base.tag_edge import TagEdge

logger = logging.getLogger("uvicorn")


class SchemaStrictnessEnum(str, Enum):
    """
    Schema validation levels.

    - none: The rule is inactive and validation thus turned off.
    - new: Only newly inserted documents are validated.
    - moderate: New and modified documents must pass validation, except for modified documents
      where the OLD value did not pass validation already. This level is useful if you have
      documents which do not match your target structure, but you want to stop the insertion
      of more invalid documents and prohibit that valid documents are changed to invalid documents.
    - strict: All new and modified document must strictly pass validation. No exceptions are made (default).
    """

    NONE = "none"
    NEW = "new"
    MODERATE = "moderate"
    STRICT = "strict"


class ArangoCollectionSchema(BaseModel):
    """
    Represents the collection schema configuration.
    """

    rule: dict
    level: str
    message: str = "The provided data doesn't passed the schema validation."


class ArangoDB(object):
    """
    Represents the database.
    """

    _instance = None

    client: ArangoClient
    gagm_db: Database
    gagm_graph: Graph

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating the object ArangoConnector")
            config = {
                "host": os.environ.get("GRAPH_DB_HOST", "127.0.0.1"),
                "port": os.environ.get("GRAPH_DB_PORT", 8529),
                "user": os.environ.get("GRAPH_DB_USER", "root"),
                "password": os.environ.get("GRAPH_DB_PASS", "secret"),
            }
            logger.info(config)
            cls._instance = super(ArangoDB, cls).__new__(cls)
            cls.client = ArangoClient(hosts=f"http://{config['host']}:{config['port']}")
            sys_db: StandardDatabase = cls.client.db(
                name="_system",
                username=config["user"],
                password=config["password"],
                verify=True,
            )

            if not sys_db.has_database("gagm"):
                sys_db.create_database("gagm")

            cls.gagm_db = cls.client.db(
                name="gagm", username=config["user"], password=config["password"]
            )

            if not cls.gagm_db.has_graph("gagm"):
                cls.gagm_db.create_graph("gagm")

            cls.gagm_graph = cls.gagm_db.graph("gagm")
        return cls._instance

    def create_or_update_vertex_collections(
        self, models: dict[str, Type[NodeModel]]
    ) -> None:
        """
        Create or update vertex collections.

        Args:
            models (dict[str, Type[AssetModel]]): The models.
        """
        for model in models.values():
            model_name: str = model.__name__
            schema = ArangoCollectionSchema(
                rule=model.model_json_schema(),
                level=str(SchemaStrictnessEnum.NONE.value),
            )
            if not self.gagm_db.has_collection(model_name):
                self.gagm_graph.create_vertex_collection(name=model_name)
                self.gagm_graph.vertex_collection(model_name).configure(
                    schema=schema.model_dump()
                )
            else:
                self.gagm_graph.vertex_collection(model_name).configure(
                    schema=schema.model_dump()
                )

    def create_or_update_edge_collections(
        self, models: dict[str, Type[EdgeModel]]
    ) -> None:
        for model in models.values():
            model_name: str = model.__name__
            if not self.gagm_db.has_collection(model_name):
                self.update_edge_collection(model_name, model)
            else:
                self.create_edge_collection(model_name, model)
                self.update_edge_collection(model_name, model)

    def update_edge_collection(self, name: str, edge_model: Type[EdgeModel]) -> None:
        name = edge_model.__name__
        schema = ArangoCollectionSchema(
            rule=edge_model.model_json_schema(),
            level=str(SchemaStrictnessEnum.NONE.value),
        )
        self.gagm_graph.delete_edge_definition(name)
        self.gagm_graph.create_edge_definition(
            edge_collection=name,
            from_vertex_collections=edge_model.origin_type,
            to_vertex_collections=edge_model.target_type,
        )
        self.gagm_graph.edge_collection(name).configure(schema=schema.model_dump())

    def create_edge_collection(self, name: str, edge_model: Type[EdgeModel]) -> None:
        name = edge_model.__name__
        if self.gagm_db.has_collection(name):
            return

        self.gagm_db.create_collection(name, edge=True)


    def create_tag_edge_collection(self, node_model_names: list[str]) -> None:
        """
        Create the tag edge collection.

        Args:
            node_model_names (list[str]): The node model names.
        """
        if not self.gagm_db.has_collection("TagEdge"):
            self.gagm_db.create_collection("TagEdge", edge=True)

        self.gagm_graph.delete_edge_definition("TagEdge")
        self.gagm_graph.create_edge_definition(
            edge_collection="TagEdge",
            from_vertex_collections=["AssetTag"],
            to_vertex_collections=node_model_names,
        )


    def create_collection(
        self,
        model: Type[AssetModel],
        validation_strictness: SchemaStrictnessEnum = SchemaStrictnessEnum.NONE,
    ) -> None:
        """
        Create a collection with schema validation.
        If the collection already exists update the schema.

        Args:
            model (AssetModel): The model of the to be stored data.
            validation_strictness (SchemaStrictnessEnum, optional): JSON schema validation strictness for the collections. Defaults to SchemaStrictnessEnum.NONE.
        """
        model_name: str = model.__name__
        schema = ArangoCollectionSchema(
            rule=model.model_json_schema(), level=str(validation_strictness.value)
        )
        if not self.gagm_db.has_collection(model_name):
            logger.info("Collection %s was not present, creating it...", model_name)
            if issubclass(model, EdgeModel):
                if len(model.origin_type) == 0 and len(model.target_type) == 0:
                    logger.info(
                        "No edge definitions found, creating normal edge collection..."
                    )
                    self.gagm_graph.create_edge_definition(
                        edge_collection=model_name,
                        from_vertex_collections=[],
                        to_vertex_collections=[],
                    )
                elif len(model.origin_type) == 0 or len(model.target_type) == 0:
                    logger.info(
                        "Partial edge definitions found, creating partially restricted edge collection..."
                    )
                    self.gagm_graph.create_edge_definition(
                        edge_collection=model_name,
                        from_vertex_collections=model.origin_type,
                        to_vertex_collections=model.target_type,
                    )
                else:
                    logger.info(
                        "Edge definitions found, creating restricted edge collection..."
                    )
                    self.gagm_graph.create_edge_definition(
                        edge_collection=model_name,
                        from_vertex_collections=model.origin_type,
                        to_vertex_collections=model.target_type,
                    )
                self.gagm_graph.edge_collection(model_name).configure(
                    schema=schema.model_dump()
                )
            else:
                logger.info(
                    "No edge definitions found, creating normal vertex collection..."
                )
                self.gagm_graph.create_vertex_collection(name=model_name)
                self.gagm_graph.vertex_collection(model_name).configure(
                    schema=schema.model_dump()
                )
            return

        logger.info("Collection %s was present, updating schema...", model_name)
        self.gagm_db.collection(model_name).configure(schema=schema.model_dump())
        if issubclass(model, EdgeModel):
            self.gagm_graph.create_edge_definition(
                edge_collection=model_name,
                from_vertex_collections=model.origin_type,
                to_vertex_collections=model.target_type,
            )

    def get_collection(self, model: Type[AssetModel]) -> StandardCollection:
        """
        Get a collection from the database.

        Args:
            model (AssetModel): The corresponding model.

        Returns:
            EdgeCollection | VertexCollection: The collection.
        """
        model_name: str = model.__name__
        if not self.gagm_db.has_collection(model_name):
            self.create_collection(model)

        return self.gagm_db.collection(model_name)

    def init_collections(self, models: dict[str, dict[str, Type[AssetModel]]]) -> None:
        """
        Initializes all collections.
        Updates existing collections with the new schemas.

        Args:
            models (dict[str, List[AssetModel]]): Dictionary of the models.
        """
        self.create_or_update_vertex_collections(models["node"])  # type: ignore
        self.create_or_update_edge_collections(models["edge"])  # type: ignore

        node_names: list[str] = list(models.get("node").keys())

        self.create_collection(AssetTag)
        self.create_tag_edge_collection(node_names)
        # self.create_edge_collection("TagEdge", TagEdge)
        # self.gagm_graph.create_edge_definition(
        #     edge_collection="TagEdge",
        #     from_vertex_collections=["AssetTag"],
        #     to_vertex_collections=node_names,
        # )
