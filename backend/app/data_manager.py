"""
data_manager.py

This module contains the DataManager class.
"""

import logging
from typing import Deque, List, Type

import base64

from arango.client import ArangoClient
from arango.database import Database
from arango.aql import AQL

from arango_connector import ArangoDB
from gagm_base.asset_model import AssetModel
from gagm_base.edge_model import EdgeModel

from model_manager import ModelManager

logger = logging.getLogger("uvicorn")


MODEL_MANAGER = ModelManager()


class DataManager(object):
    """
    DataManager class. This class is a singleton.
    It is used to manage the data in the database.
    """

    _instance = None

    _arango_client: ArangoClient
    _db: Database
    _aql: AQL

    def __init__(self) -> None:
        self._arango_client = ArangoClient(hosts="http://arango:8529")
        self._db = ArangoDB().gagm_db
        self._aql = self._db.aql
        self._graph = ArangoDB().gagm_graph

    def __new__(cls):
        if cls._instance is None:
            print("Creating the object DataManager")
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def get_asset(
        self, asset_key: str, asset_type: Type[AssetModel]
    ) -> AssetModel | None:
        """
        Get the asset by it's ID.

        Args:
            asset_id (str): The ID of the asset.

        Returns:
            dict: Properties of the asset.
        """
        type_name = str(asset_type.__name__)
        data = self._db.document(document=f"{type_name}/{asset_key}")  # type: ignore
        if not data:
            return None
        return asset_type.model_validate(obj=dict(data))

    def get_connected_nodes(self, asset_id: str) -> List[AssetModel]:
        """
        Get all assets that are connected with the given asset.

        Args:
            asset_id (str): The ID of the asset.

        Returns:
            List[AssetModel]: The connected nodes, not including the original node.
        """

        CONNECTED_NODES_QUERY = """
            FOR v, e IN 1..1 ANY @node_id
                GRAPH 'gagm'
                LET c = REGEX_SPLIT(v._id, "/")[0]
                RETURN {node: v, type: c}
        """

        found_nodes = []
        cursor = self._aql.execute(
            CONNECTED_NODES_QUERY, bind_vars={"node_id": asset_id}
        )
        for document in cursor:
            data: dict = document["node"]
            if not data:
                continue
            doc_type: str = document["type"]
            validated_model = MODEL_MANAGER.get_model(doc_type).model_validate(
                data, from_attributes=True
            )
            found_nodes.append(validated_model)

        return found_nodes

    def get_assets_by_type(self, asset_type: Type[AssetModel]) -> List[AssetModel]:
        """
        Get all assets with the specified type.

        Args:
            asset_type (Type[AssetModel]): The type of the queried assets.

        Returns:
            List[AssetModel]: The assets.
        """
        data: Deque[dict] = self._db.collection(asset_type.__name__).all() or Deque()

        parsed_data: List[AssetModel] = [asset_type(**asset) for asset in data]

        return parsed_data

    def get_connection(self, origin_id: str, target_id: str) -> EdgeModel | None:
        """
        Get the connection between two assets.

        Args:
            origin_id (str): The ID of the origin asset.
            target_id (str): The ID of the target asset.

        Returns:
            dict: The connection.
        """
        GET_EDGES_QUERY = """
            FOR v, e IN 1..3 OUTBOUND @node_id
                GRAPH 'gagm'
                LET c = REGEX_SPLIT(e._id, "/")[0]
                FILTER e._to IN @other_node_ids
                RETURN {edge: e, type: c}
        """
        edges = self._aql.execute(
            GET_EDGES_QUERY, bind_vars={"origin_id": origin_id, "target_id": target_id}
        ).batch()["edges"]
        for edge in edges:
            logger.info(edge)

        edge = self._graph.traverse(
            origin_id, direction="outbound", strategy="bfs", max_depth=1
        )
        if not edge:
            return None
        edge_type = edge["_id"].split("/")[0]
        return MODEL_MANAGER.get_model(edge_type).model_validate(
            edge, from_attributes=True
        )

    def get_edges_between_nodes(self, node_ids: list[str]) -> set[EdgeModel]:
        """
        Get all edges between a set of nodes.

        Args:
            node_ids (set[str]): Node ids

        Returns:
            dict: _description_
        """
        GET_EDGES_QUERY = """
            FOR v, e IN 1..1 ANY @node_id
                GRAPH 'gagm'
                LET c = REGEX_SPLIT(e._id, "/")[0]
                FILTER e._to IN @other_node_ids OR e._from IN @other_node_ids
                FILTER c != "TagEdge"
                RETURN {edge: e, type: c}
        """

        logger.info("GETTING EDGES BETWEEN NODES")
        edges_between_selected_nodes = []
        for node_id in node_ids:
            others = node_ids.copy()
            others.remove(node_id)
            edges = self._aql.execute(
                GET_EDGES_QUERY,
                bind_vars={"node_id": node_id, "other_node_ids": others},
            ).batch()
            for edge in edges:
                edge_data = edge.get("edge")
                edge_type = edge.get("type")
                parsed_edge = MODEL_MANAGER.get_model(edge_type).model_validate(
                    edge_data, from_attributes=True
                )
                edges_between_selected_nodes.append(parsed_edge)

        return set(edges_between_selected_nodes)

    def get_assets_by_tags(self, tags: list[str]) -> set[AssetModel]:
        tagged_assets: set[AssetModel] = set()
        for tag in tags:
            safe_tag_name = base64.urlsafe_b64encode(tag.encode("utf-8")).decode("utf-8")
            tagged_nodes = self._graph.traverse(
                direction="outbound",
                start_vertex=f"AssetTag/{safe_tag_name}",
                max_depth=1,
                strategy="bfs",
            )
            for node in tagged_nodes.get("vertices"):
                node_type = node["_id"].split("/")[0]
                if node_type == "AssetTag":
                    continue
                parsed_node = MODEL_MANAGER.get_model(node_type).model_validate(
                    node, from_attributes=True
                )
                tagged_assets.add(parsed_node)
        return tagged_assets

    def add_asset(self, asset: AssetModel) -> AssetModel:
        asset_type: Type = type(asset)
        if issubclass(asset_type, EdgeModel):
            edge_type = MODEL_MANAGER.get_model(asset_type.__name__)
            origin_type: str = asset.origin_id.split("/")[0]
            target_type: str = asset.target_id.split("/")[0]
            if asset.origin_id is None or asset.target_id is None:
                raise ValueError("Edge must have both from_id and to_id set.")
            if origin_type not in edge_type.origin_type:
                raise ValueError(
                    f"Edge origin type must be one of {edge_type.origin_type}"
                )
            if target_type not in edge_type.target_type:
                raise ValueError(
                    f"Edge target type must be one of {edge_type.target_type}"
                )
        logger.info(asset.model_dump(by_alias=True))
        result = dict(
            self._db.collection(asset_type.__name__).insert(
                document=asset.model_dump(by_alias=True),
                return_new=True,
                overwrite=False,
                keep_none=True,
            )
        )
        return asset_type(**result["new"])

    def update_asset(self, asset: AssetModel) -> AssetModel:
        """
        Update an existing asset.

        Args:
            asset (AssetModel):

        Returns:
            AssetModel: _description_
        """
        asset_type: Type = type(asset)
        logger.info(asset)
        logger.info(asset.model_dump(by_alias=True))
        # data = self._db.collection(asset_type).insert(
        #     document=asset.model_dump(by_alias=True),
        #     return_new=True,
        #     overwrite_mode="update",
        #     keep_none=True,
        # )
        result = self._db.collection(asset_type.__name__).update(
            document=asset.model_dump(by_alias=True), return_new=True
        )
        return asset_type(**result["new"])

    def delete_asset_by_id(self, asset_id: str):
        asset_key = asset_id.split("/")[1]
        asset_type = MODEL_MANAGER.get_model(asset_id.split("/")[0])
        self.delete_asset(asset_key, asset_type)

    def delete_asset(self, asset_key: str, asset_type: Type[AssetModel]) -> bool:
        """
        Delete an asset from the database.

        Args:
            asset_key (str): The key of the asset.
            asset_type (Type[AssetModel]): The type of the asset.

        Returns:
            bool: True if the asset was deleted, False otherwise.
        """
        type_name = asset_type.__name__
        logger.info(f"Deleting object {asset_key} in {type_name} collection")
        result = self._graph.delete_vertex(f"{type_name}/{asset_key}", ignore_missing=True)
        return result

    def is_asset_present(self, asset_id: str) -> bool:
        """
        Checks if an asset is present in the database.

        Args:
            asset_key (str): The key of the asset.
            asset_type (Type[AssetModel]): The type of the asset.

        Returns:
            bool: True if the asset is present in the database.
        """
        type_name = asset_id.split("/")[0]
        logger.debug(
            f"Checking object {asset_id.split('/')[1]} in {type_name} collection"
        )
        return bool(self._db.has_document(f"{asset_id}")) or False  # type: ignore

    def get_asset_notes(self, asset_id: str) -> str:
        """
        Get the notes of an asset.

        Args:
            asset_id (str): ID of the asset (prefixed with type).

        Returns:
            str: The notes.
        """
        return self._db.document(f"{asset_id}").get("notes") or ""  # type: ignore

    def set_asset_notes(self, asset_id: str, notes: str) -> str:
        """
        Set notes of an asset.

        Args:
            asset_type (str): Type of the asset.
            asset_key (str): Key of the asset.
            notes (str): The notes.
        """
        self._db.update_document({"_id": f"{asset_id}", "notes": notes})
        return self.get_asset_notes(asset_id)

    def get_tags_for_node(self, asset_id: str) -> List[str]:
        """
        Get all tags for a node.

        Args:
            asset_id (str): The ID of the asset.

        Returns:
            List[str]: List of tags.
        """
        cursor = self._graph.edges("TagEdge", asset_id, direction="inbound")

        tags = []
        for edge in cursor["edges"]:
            tags.append(edge["tag_name"])

        return tags

    def get_tags(self) -> List[str]:
        """
        Get all tags present in the database.

        Returns:
            List[str]: List of tags.
        """
        tags: list[str] = [tag["name"] for tag in self._db.collection("AssetTag").all()]
        logger.info(tags)
        return tags

    def create_tag(self, tag_name: str):
        safe_tag_name = base64.urlsafe_b64encode(tag_name.encode("utf-8")).decode("utf-8")
        return self._db.insert_document(
            "AssetTag", {"name": tag_name, "_key": safe_tag_name}
        )

    def toggle_tag(self, tag_name: str, asset_id: str) -> bool:
        """
        Toggle a tag on an asset.

        Args:
            tag (str): The tag to toggle.
            asset_id (str): The ID of the asset.

        Returns:
            bool: True if the tag was added, False if it was removed.
        """
        safe_tag_name = base64.urlsafe_b64encode(tag_name.encode("utf-8")).decode("utf-8")
        tag_id: str = f"AssetTag/{safe_tag_name}"
        edge_key = base64.urlsafe_b64encode(str(f"{tag_name}-{asset_id}").encode("utf-8")).decode("utf-8")
        edge_id = f"TagEdge/{edge_key}"
        if self._graph.has_edge(edge_id):
            self._graph.delete_edge(edge_id)
            return False
        self._graph.link(
            "TagEdge",
            from_vertex=tag_id,
            to_vertex=asset_id,
            data={"_key": edge_key, "tag_name": tag_name},
        )
        return True

    def delete_tag(self, tag_name: str):
        """
        Delete a tag and all of it's connections.

        Args:
            tag_name (str): Name of the tag.
        """
        safe_tag_name = base64.urlsafe_b64encode(tag_name.encode("utf-8")).decode("utf-8")
        tag_id: str = f"AssetTag/{safe_tag_name}"
        return self._graph.delete_vertex(tag_id, ignore_missing=True)
