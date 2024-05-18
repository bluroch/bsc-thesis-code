"""
data.py

This module contains the endpoints for managing the data.
"""

import enum
import inspect
import json
import logging
import os
import traceback
from enum import Enum
from pathlib import Path as OSPath
from types import FunctionType
from typing import Annotated, Dict, List, Type

import auth_methods as auth_methods
from data_manager import DataManager
from exceptions.data_exceptions import UniqueConstraintViolatedException
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse

# from models.base.asset_log_record import AssetLogRecord
from gagm_base.asset_model import AssetModel
from gagm_base.node_model import NodeModel
from gagm_base.edge_model import EdgeModel
from model_manager import ModelManager, ModelNotFoundError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("uvicorn")

os.chdir(OSPath(__file__).parent.parent.resolve())

DOCS_BASE_PATH = OSPath("docs/endpoints/data")

MODEL_MANAGER = ModelManager()
DATA_MANAGER = DataManager()


router = APIRouter(dependencies=[Depends(auth_methods.authenticate_user)])


def get_asset_by_id(
    asset_id: Annotated[
        str, Path(description="The ID of the asset. Example format: *Type/Key*.")
    ],
) -> AssetModel:
    asset_type_str: str = asset_id.split("/")[0]
    asset_key: str = asset_id.split("/")[1]
    return get_asset_by_type_and_key(asset_type_str, asset_key)
    # try:
    #     asset_type: type[AssetModel] = MODEL_MANAGER.get_model(asset_type_str)
    #     # if not asset_type:
    #     #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid asset type")
    #     asset_key: str = asset_id.split('/')[1]
    #     asset = DATA_MANAGER.get_asset(asset_key=asset_key, asset_type=asset_type)
    #     if not asset:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No asset found with the given ID")
    #     return asset
    # except ModelNotFoundError:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid asset type \"{asset_type_str}\"")


def get_asset_by_type_and_key(
    asset_type: Annotated[str, Path(description="The type of the asset")],
    asset_key: Annotated[str, Path(description="The key of the asset")],
):
    try:
        asset = DATA_MANAGER.get_asset(
            asset_key=asset_key, asset_type=MODEL_MANAGER.get_model(asset_type)
        )
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No asset found with the given ID",
            )
        return asset
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid asset type "{asset_type}"',
        )


def get_tag(tag_name: Annotated[str, Path(description="An asset tag")]):
    # try:
    #     asset_tag = DATA_MANAGER.get_asset(asset_key=tag_name, asset_type=Type[])
    ...


typed_routes = {}


class DataQuery(BaseModel):
    full_graph: bool = True
    types: list[str] = []
    tags: list[str] = []


class InclusionEnum(str, enum.Enum):
    """
    Filtering type.
    EXCLUDE: all items should be excluded in the response.
    INCLUDE: all items should be included in the response.
    """

    INCLUDE = "include"
    EXCLUDE = "exclude"


class GraphViewFilter(BaseModel):
    """
    Filter for the graph.
    """

    tags: list[str] = []
    tag_filter_type: InclusionEnum
    types: list[str] = []
    type_filter_type: InclusionEnum


class TypedNodes(BaseModel):
    nodes: dict[str, dict[str, NodeModel]] = dict()

    def add_node(self, node: NodeModel):
        if not node.db_id.split("/")[0] in self.nodes.keys():
            self.nodes.update({node.db_id.split("/")[0]: {}})
        self.nodes[node.db_id.split("/")[0]].update({node.db_key: node.model_dump()})

    def add_nodes(self, nodes: List[NodeModel]):
        for node in nodes:
            self.add_node(node)

    def remove_by_type(self, node_type: type[NodeModel]):
        if node_type.__name__ in self.nodes.keys():
            self.nodes.pop(node_type.__name__)

    def get_ids(self) -> list[str]:
        ids: list[str] = list()
        logger.info(self.nodes.values())
        for node_type in self.nodes.values():
            logger.info(node_type.keys())
            for node in node_type.values():
                logger.info(node)
                ids.append(node["db_id"])
            # ids.extend(node_type.values())
        return ids


class TypedEdges(BaseModel):
    edges: dict[str, dict[str, EdgeModel]] = dict()

    def add_edge(self, edge: EdgeModel):
        logger.info(edge)
        if not edge.db_id.split("/")[0] in self.edges.keys():
            self.edges.update({edge.db_id.split("/")[0]: {}})
        self.edges[edge.db_id.split("/")[0]].update({edge.db_key: edge.model_dump()})

    def add_edges(self, edges: List[EdgeModel]):
        for edge in edges:
            self.add_edge(edge)

    def remove_by_type(self, edge_type: type[EdgeModel]):
        if edge_type.__name__ in self.edges.keys():
            self.edges.pop(edge_type.__name__)


class BackendGraph(BaseModel):
    # nodes: TypedNodes = TypedNodes()
    nodes: dict[str, dict[str, NodeModel]] = dict()
    # edges: TypedEdges = TypedEdges()
    edges: dict[str, dict[str, EdgeModel]] = dict()

    def add_node(self, node: NodeModel):
        if not node.db_id.split("/")[0] in self.nodes.keys():
            self.nodes.update({node.db_id.split("/")[0]: {}})
        self.nodes[node.db_id.split("/")[0]].update({node.db_key: node.model_dump()})

    def add_nodes(self, nodes: List[NodeModel]):
        for node in nodes:
            self.add_node(node)

    def remove_node_by_type(self, node_type: type[NodeModel]):
        if node_type.__name__ in self.nodes.keys():
            self.nodes.pop(node_type.__name__)

    def get_node_ids(self) -> list[str]:
        ids: list[str] = list()
        logger.info(self.nodes.values())
        for node_type in self.nodes.values():
            logger.info(node_type.keys())
            for node in node_type.values():
                logger.info(node)
                ids.append(node["db_id"])
            # ids.extend(node_type.values())
        return ids

    def add_edge(self, edge: EdgeModel):
        logger.info(edge)
        if not edge.db_id.split("/")[0] in self.edges.keys():
            self.edges.update({edge.db_id.split("/")[0]: {}})
        self.edges[edge.db_id.split("/")[0]].update({edge.db_key: edge.model_dump()})

    def add_edges(self, edges: List[EdgeModel]):
        for edge in edges:
            self.add_edge(edge)

    def remove_edge_by_type(self, edge_type: type[EdgeModel]):
        if edge_type.__name__ in self.edges.keys():
            self.edges.pop(edge_type.__name__)


@router.get("/", summary="Get the whole graph.")
async def get_all_data():
    data = BackendGraph()
    for name in MODEL_MANAGER.get_all_model_names():
        model: Type[AssetModel] = MODEL_MANAGER.get_model(name)
        if issubclass(model, NodeModel):
            nodes: List[NodeModel] = [
                asset for asset in DATA_MANAGER.get_assets_by_type(model)
            ]
            data.add_nodes(nodes)
        else:
            edges: List[EdgeModel] = [
                asset for asset in DATA_MANAGER.get_assets_by_type(model)
            ]
            data.add_edges(edges)

    return data


@router.post("/filtered", summary="Get filtered data.")
async def get_filtered_data(query: GraphViewFilter, request: Request):
    data = BackendGraph()
    logger.info("GETTING TAGGED DATA")
    tags: list[str] = []
    tagged_data: set[AssetModel] = set()
    if len(query.tags) == 0 and query.tag_filter_type == InclusionEnum.EXCLUDE:
        for name in MODEL_MANAGER.get_all_model_names():
            model: Type[AssetModel] = MODEL_MANAGER.get_model(name)
            if issubclass(model, NodeModel):
                nodes: List[NodeModel] = [
                    asset for asset in DATA_MANAGER.get_assets_by_type(model)
                ] # type: ignore
                tagged_data = tagged_data.union(nodes)
    elif query.tag_filter_type == InclusionEnum.INCLUDE:
        tags = query.tags
    else:
        tags = DATA_MANAGER.get_tags()
        [tags.remove(tag) for tag in query.tags]
    tagged_data = tagged_data.union(DATA_MANAGER.get_assets_by_tags(tags))
    # logger.info(tagged_data)
    # data.nodes.add_nodes(list(tagged_data))

    logger.info("GETTING TYPED DATA")
    node_model_names = set(MODEL_MANAGER.get_node_models().keys())
    typed_data: set[AssetModel] = set()
    type_names: list[str] = list()
    if query.type_filter_type == InclusionEnum.INCLUDE:
        type_names = list(node_model_names.intersection(query.types))
    else:
        type_names = list(node_model_names.difference(query.types))
    for type_name in type_names:
        model: Type[AssetModel] = MODEL_MANAGER.get_model(type_name)
        # typed_data.add(DATA_MANAGER.get_assets_by_type(model))
        typed_data = typed_data.union(DATA_MANAGER.get_assets_by_type(model))

    # logger.info(type_names)
    # logger.info(typed_data)

    # logger.info(typed_data)
    intersection = set.intersection(typed_data, tagged_data)
    logger.info("INTERSECTION")
    logger.info(intersection)
    # logger.info(intersection)
    data.add_nodes(list(intersection))
    # type_filtered_data: dict[str, dict[str, NodeModel]] = dict()
    node_ids = data.get_node_ids()
    logger.info(f"{node_ids=}")
    # logger.info(f"{node_ids=}")
    # for asset in tagged_data:
    #     asset_type = asset.db_id.split("/")[0]
    #     if not asset_type in type_filtered_data.keys():
    #         type_filtered_data.update({asset_type: {}})
    #     type_filtered_data[asset_type].update({asset.db_key: asset.model_dump()})
    # List[AssetModel] = [item for item in tagged_data if isinstance(item, tuple(MODEL_MANAGER.get_model(model_type) for model_type in types))]
    # node_ids = set(node.db_id for node in type_filtered_data)
    edges = DATA_MANAGER.get_edges_between_nodes(node_ids)
    # edges = set()
    logger.info(f"{edges=}")
    # typed_edges = dict[str, dict[str, EdgeModel]]
    # for edge in edges:
    #     edge_type = edge.db_id.split("/")[0]
    #     if not edge_type in typed_edges.keys():
    #         typed_edges.update({edge_type: {}})
    #     typed_edges[edge_type].update({edge.db_key: edge.model_dump()})
    data.add_edges(list(edges))  # {"nodes": type_filtered_data, "edges": edges}
    # logger.info(data)
    return data


@router.get("/tags")
def get_tags():
    return DATA_MANAGER.get_tags()


class TagInput(BaseModel):
    name: str


@router.post("/tags")
def add_tag(tag: TagInput):
    return DATA_MANAGER.create_tag(tag.name)


@router.delete("/tags/{tag_name}")
def delete_tag(tag_name: str):
    return DATA_MANAGER.delete_tag(tag_name)


@router.get(
    "/tagged/{tag}",
    summary="Get data tagged with the provided tag.",
    description=(DOCS_BASE_PATH / "get_tagged_data.md").read_text(encoding="utf-8"),
)
async def get_tagged_data(
    tag: str = Path(
        title="Tag",
        description="The tag to filter the data by.",
        example="example_tag",
        type="string",
    ),
) -> List[AssetModel]:
    logger.debug('Getting data with tag "%s"', tag)
    return DATA_MANAGER.get_connected_nodes(f"AssetTag/{tag}")


@router.get(
    "/typed/{user_type}",
    summary="Get data with the provided user type.",
    description=(DOCS_BASE_PATH / "get_data_with_type.md").read_text(encoding="utf-8"),
    response_model=Dict[str, AssetModel],
    responses={
        200: {
            "description": "Data retrieved successfully.",
        },
        400: {
            "description": "User type does not exist.",
        },
    },
)
def get_data_with_type(
    requested_type: str,
):
    try:
        model: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
        data = DATA_MANAGER.get_assets_by_type(model)
        logger.info({asset.db_key: asset.model_dump() for asset in data})
        return {asset.db_key: asset.model_dump() for asset in data}
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User type {requested_type} does not exist.",
        )


def list_endpoint_skeleton(requested_type: str):
    try:
        asset_type: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
        ModelType = Type[asset_type]
        data: List[ModelType] = DATA_MANAGER.get_assets_by_type(asset_type)  # type: ignore
        # returned: Dict[str, ModelType] = {asset.db_key: asset for asset in data}
        # logger.info({asset.db_key: asset for asset in data})
        return {asset.db_key: asset for asset in data} or {}
    except ModelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User type {requested_type} does not exist.",
        ) from exc


def get_endpoint_skeleton(requested_type: str, asset_key: str):
    asset_type: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid type {requested_type}",
        )
    data = DATA_MANAGER.get_asset(asset_key, asset_type)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {requested_type} typed asset found with id {asset_key}.",
        )
    return data


def post_endpoint_skeleton(request_body: AssetModel):
    try:
        new_object = DATA_MANAGER.add_asset(request_body)

        return new_object
    except ValidationError as exc:
        logger.info(traceback.format_exception(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()
        ) from exc
    except UniqueConstraintViolatedException as exc:
        raise HTTPException(
            status_code=409,
            detail="Asset already stored in the database. Use the PUT or PATCH endpoint to update it.",
        ) from exc


def put_endpoint_skeletion(asset_key: str, request_body: AssetModel):
    try:
        logger.info(request_body)
        asset_type: Type = type(request_body)
        if not DATA_MANAGER.is_asset_present(f"{asset_type}/{asset_key}"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with id {asset_type}/{asset_key} not found.",
            )
        if request_body.db_id is None or request_body.db_key is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The provided data doesn't contain all necessary fields.",
            )
        new_object = DATA_MANAGER.update_asset(request_body)

        return new_object
    except ValidationError as exc:
        logger.info(traceback.format_exception(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()
        ) from exc


class PregeneratedRoute:
    summaries = {
        "list": "List all {requested_type} typed {asset_or_edge}.",
        "get": "Get a {requested_type} typed asset.",
        "post": "Create a new {requested_type} typed {asset_or_edge}.",
        "put": "Update an existing {requested_type} typed {asset_or_edge}.",
    }
    response_model: Type = Dict[str, AssetModel]
    route_path: str = "/typed/pregenerated/{requested_type}"
    type_var: Type = AssetModel
    requested_type: str

    def __init__(self, requested_type: Type[AssetModel]):
        self.requested_type = requested_type.__name__
        self.summaries = dict(self.summaries)
        logger.info(self.requested_type)

        self.response_model = Dict[str, requested_type]

        # Summaries
        self.summaries["list"] = self.summaries["list"].format(
            requested_type=self.requested_type,
            asset_or_edge=(
                "assets" if issubclass(requested_type, NodeModel) else "edges"
            ),
        )
        self.summaries["get"] = self.summaries["get"].format(
            requested_type=self.requested_type
        )
        self.summaries["post"] = self.summaries["post"].format(
            requested_type=self.requested_type,
            asset_or_edge="asset" if issubclass(requested_type, NodeModel) else "edge",
        )
        self.summaries["put"] = self.summaries["put"].format(
            requested_type=self.requested_type,
            asset_or_edge="asset" if issubclass(requested_type, NodeModel) else "edge",
        )

        self.route_path = self.route_path.format(requested_type=self.requested_type)

        self.type_var = MODEL_MANAGER.get_model(self.requested_type)
        # Add POST endpoint for the type
        # logger.info(self.post_endpoint.__annotations__)
        sig = inspect.signature(self.post_endpoint)
        new_param = inspect.Parameter(
            "request_body",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=self.type_var,
        )
        new_sig = sig.replace(
            parameters=[
                new_param if param.name == "request_body" else param
                for param in sig.parameters.values()
            ]
        )
        code = post_endpoint_skeleton.__code__
        new_func = FunctionType(code, globals(), "new_func", None, None)
        new_func.__signature__ = new_sig
        self.post_endpoint = new_func

        # Add PUT endpoint for the type
        # TODO: add PUT endpoint
        sig = inspect.signature(self.put_endpoint)
        new_param = inspect.Parameter(
            "request_body",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=self.type_var,
        )
        new_sig = sig.replace(
            parameters=[
                new_param if param.name == "request_body" else param
                for param in sig.parameters.values()
            ]
        )
        code = put_endpoint_skeletion.__code__
        new_func = FunctionType(code, globals(), "new_func", None, None)
        new_func.__signature__ = new_sig
        self.put_endpoint = new_func

    def list_endpoint(self):
        return list_endpoint_skeleton(requested_type=self.requested_type)

    def get_endpoint(self, asset_key: str):
        return get_endpoint_skeleton(
            requested_type=self.requested_type, asset_key=asset_key
        )

    def post_endpoint(self, request_body):
        pass

    def put_endpoint(self, asset_key: str, request_body):
        pass


def init_typed_endpoints():
    """
    Initializes the typed endpoints.
    It makes the OpenAPI documentation more explorable.

    Returns:
        _type_: _description_
    """
    for name in MODEL_MANAGER.get_all_model_names():
        logger.info("Adding routes for type %s", name)

        response_model = MODEL_MANAGER.get_model(name)
        typed_endpoint = PregeneratedRoute(requested_type=response_model)

        typed_routes.update({name: typed_endpoint})

        router.add_api_route(
            typed_endpoint.route_path,
            typed_routes[name].list_endpoint,
            response_model=typed_endpoint.response_model,
            summary=typed_endpoint.summaries["list"],
            methods=["GET"],
        )

        router.add_api_route(
            typed_endpoint.route_path + "/{asset_key}",
            typed_routes[name].get_endpoint,
            response_model=response_model,
            summary=typed_endpoint.summaries["get"],
            methods=["GET"],
        )

        router.add_api_route(
            typed_endpoint.route_path,
            typed_routes[name].post_endpoint,
            response_model=response_model,
            summary=typed_endpoint.summaries["post"],
            methods=["POST"],
        )

        router.add_api_route(
            typed_endpoint.route_path + "/{asset_key}",
            typed_routes[name].put_endpoint,
            response_model=response_model,
            summary=typed_endpoint.summaries["put"],
            methods=["PUT"],
        )


init_typed_endpoints()


@router.post(
    "/{requested_type}",
    description="Post data with a user type.",
    responses={
        200: {
            "description": "Data posted successfully.",
        },
        400: {
            "description": "User type does not exist.",
        },
    },
)
async def post_data_with_type(
    request_data: dict, requested_type: str = Path(description="User type")
):
    try:
        asset_type: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
        # asset_data = json.loads(request_data)
        logger.debug("Validating JSON")
        logger.info(request_data)

        logger.debug("Creating object from\n%s", json.dumps(request_data))

        created_object = asset_type(**request_data)
        logger.info(f"{type(created_object)=}")
        logger.debug("Object created\n%s ", str(created_object))
        if hasattr(created_object, "db_key") and DATA_MANAGER.is_asset_present(
            created_object.db_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Asset already exists, use the PUT endpoint to update it.",
            )
        return DATA_MANAGER.add_asset(created_object)
    except ValidationError as error:
        logger.info(traceback.format_exception(error))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error.errors()
        ) from error
    except ModelNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User type {requested_type} does not exist.",
        ) from error
    except TypeError as error:
        logger.info(traceback.format_exception(error))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Couldn't construct model: {error}",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error: {error}",
        ) from error


@router.get(
    "/{asset_type}/{asset_key}",
    response_class=JSONResponse,
    summary="Get an asset with the specified type.",
)
async def get_asset(asset: AssetModel = Depends(get_asset_by_type_and_key)):
    return asset
    # try:
    #     AssetType: Type = MODEL_MANAGER.get_model(asset_type)
    #     asset = DATA_MANAGER.get_asset(asset_key=asset_id, asset_type=AssetType)
    #     if not asset:
    #         raise HTTPException(
    #             status_code=404, detail=f"{asset_type} with ID '{asset_id}' not found!"
    #         )
    #     return asset
    # except ModelNotFoundError as error:
    #     raise HTTPException(
    #         status_code=400, detail=f"Model {asset_type} not found!"
    #     ) from error


@router.put("/{asset_type}/{asset_key}")
async def full_update_asset(
    updated_asset: dict,
    request: Request,
    asset: AssetModel = Depends(get_asset_by_type_and_key),
):
    logger.info(updated_asset)
    try:
        asset_key = asset.db_key
        requested_type = asset.db_id.split("/")[0]
        logger.info(f"{type(asset)=}")
        model_type: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
        logger.info(f"{model_type=}")
        logger.info("updated_asset")
        new_object = model_type(
            _id=updated_asset["db_id"], _key=asset_key, **updated_asset
        )
        if not issubclass(new_object.__class__, NodeModel):
            new_object = model_type(
                _id=updated_asset["db_id"],
                _key=asset_key,
                **updated_asset,
            )

        DATA_MANAGER.update_asset(new_object)

        return {"message": "Asset updated"}
    except ValidationError as error:
        logger.info(traceback.format_exception(error))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error.errors()
        ) from error
    except ModelNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset type {requested_type} does not exist.",
        ) from error
    except TypeError as error:
        logger.info(traceback.format_exception(error))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Couldn't construct model: {error}",
        ) from error


@router.patch("/{requested_type}/{asset_id}")
async def partial_update_asset(requested_type: str, asset_id: str, request_data: dict):
    raise Exception("Unimplemented")


@router.delete(
    "/{asset_id:path}",
    response_class=JSONResponse,
    responses={
        200: {
            "description": "Asset deleted successfully. The deleted asset is returned.",
            "content": {
                "application/json": {
                    "example": {"notes": "string", "_id": "string", "_key": "string"}
                }
            },
        }
    },
)
async def delete_asset_by_id(asset: AssetModel = Depends(get_asset_by_id)):
    DATA_MANAGER.delete_asset_by_id(asset.db_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=asset.model_dump_json())


@router.delete(
    "/{requested_type}/{asset_id}",
    summary="Delete an asset.",
    description="Delete an asset. Returns the asset on success.",
)
# async def delete_asset(requested_type: str, asset_id: str):
#     try:
#         model_type: Type[AssetModel] = MODEL_MANAGER.get_model(requested_type)
#         if not DATA_MANAGER.is_asset_present(asset_id):
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f'Asset with id "{asset_id}" not found',
#             )
#         DATA_MANAGER.delete_asset(asset_id, model_type)
#         return {"message": "Asset deleted"}
#     except ModelNotFoundError as error:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Asset type {requested_type} does not exist.",
#         ) from error


async def delete_asset_v2(
    asset: AssetModel = Depends(get_asset_by_type_and_key),
) -> AssetModel:
    DATA_MANAGER.delete_asset_by_id(asset.db_id)
    return asset


class Order(str, Enum):
    ASC = "asc"
    DESC = "desc"


# @router.get("/{asset_id}/logs", response_model=List[AssetLogRecord])
# async def get_asset_logs(
#     asset_id: str,
#     asset_type: str,
#     limit: int = 10,
#     offset: int = 0,
#     order: Order = Order.DESC,
# ):
#     if order not in ["ASC", "DESC"]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='Order must be "ASC" or "DESC"',
#         )
#     if limit < 1:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Limit must be greater than 0",
#         )
#     if offset < 0:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Offset must be greater than or equal to 0",
#         )
#     if limit > 100:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Limit must be less than or equal to 100",
#         )
#     if not DATA_MANAGER.is_asset_present(asset_id, MODEL_MANAGER.get_model(asset_type)):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f'Asset with id "{asset_id}" not found',
#         )
#     if order == Order.DESC:
#         pass
#     else:
#         pass
#     asset_logs = []

#     return asset_logs


@router.get(
    "/{asset_id:path}/notes",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Notes retrieved successfully.",
            "content": {
                "text/markdown": {
                    "example": (
                        "# Notes for asset with id 123\n"
                        "## 2021-01-01\n"
                        "This is a note\n"
                        "## 2021-01-02\n"
                        "This is another note\n"
                    )
                }
            },
        },
        404: {
            "description": "Asset with the provided id not found.",
            "content": {
                "application/json": {
                    "example": {"detail": 'Asset with id "123" not found'}
                }
            },
        },
    },
    summary="Get the notes of an asset.",
    description=(DOCS_BASE_PATH / "get_notes.md").read_text(encoding="utf-8"),
)
async def get_asset_notes(asset: AssetModel = Depends(get_asset_by_id)):
    notes: str = DATA_MANAGER.get_asset_notes(asset.db_id)
    return PlainTextResponse(content=notes, media_type="text/markdown")


@router.post("/{asset_id:path}/notes")
async def set_notes(
    asset: AssetModel = Depends(get_asset_by_id),
    notes: str = Body(default="", media_type="text/plain"),
):
    updated_notes = DATA_MANAGER.set_asset_notes(asset.db_id, notes)
    return PlainTextResponse(updated_notes, media_type="text/markdown")


@router.get("/{asset_id:path}/connected_nodes")
async def get_connected_nodes(asset: AssetModel = Depends(get_asset_by_id)):
    return DATA_MANAGER.get_connected_nodes(asset_id=asset.db_id)


@router.get("/{asset_id:path}/tags")
async def get_tags_for_nodes(asset: AssetModel = Depends(get_asset_by_id)) -> List[str]:
    return DATA_MANAGER.get_tags_for_node(asset_id=asset.db_id)

@router.post("/{asset_id:path}/tags/{tag}")
async def toggle_tag_for_node(tag: str, asset: AssetModel = Depends(get_asset_by_id)) -> List[str]:
    DATA_MANAGER.toggle_tag(asset_id=asset.db_id, tag_name=tag)
    return DATA_MANAGER.get_tags_for_node(asset_id=asset.db_id)
