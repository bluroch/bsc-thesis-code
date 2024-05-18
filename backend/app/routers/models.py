"""
models.py

This module contains the endpoints for the models.
"""

from enum import Enum
import logging
import os
from pathlib import Path as OSPath
from typing import Dict, Union

from fastapi import APIRouter, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic.fields import FieldInfo

from model_manager import ModelManager
from responses.model_response import ModelResponse
from responses.models_response import ModelsResponse
from responses.reduced_models_response import ReducedModelsResponse

# os.chdir(OSPath(__file__).parent.parent.resolve())

MODEL_MANAGER = ModelManager()

DOCS_BASE_PATH = OSPath("docs/endpoints/models/")

logger = logging.getLogger("uvicorn")

router = APIRouter()


class ModelType(Enum):
    NODE = "node"
    EDGE = "edge"
    ASSET = "asset"


@router.get(
    "/",
    summary="List all available models",
    description=(DOCS_BASE_PATH / "list_models.md").read_text(encoding="utf-8"),
    response_model=Union[ModelsResponse, ReducedModelsResponse],
    responses={
        200: {
            "description": "Models retrieved successfully",
            # "content": ModelsResponse.model_json_schema(),
        },
    },
)
async def get_models(
    names_only: bool = Query(True, description="Only return model names"),
    model_type: ModelType = Query(ModelType.ASSET, description="Filter models by type"),
):
    """
    List all available models

    Args:
        names_only (bool): Only return model names
    """
    models = dict()
    match model_type:
        case ModelType.NODE:
            models = MODEL_MANAGER.get_node_models()
        case ModelType.EDGE:
            models = MODEL_MANAGER.get_edge_models()
        case ModelType.ASSET:
            all_models = MODEL_MANAGER.get_all_models()
            models = {**all_models["node"], **all_models["edge"]}

    if names_only:
        return ReducedModelsResponse(model_names=list(models.keys()))

    model_responses: dict = {}
    for name in models:
        model_responses[name] = ModelResponse(model_name=name, model_schema=MODEL_MANAGER.get_model_schema(name))
    return ModelsResponse(models=model_responses)


@router.get(
    "/{model_name}",
    summary="Get a model by name",
    description=(DOCS_BASE_PATH / "get_model.md").read_text(encoding="utf-8"),
    response_class=JSONResponse,
    response_model=ModelResponse,
    responses={
        200: {
            "description": "Model retrieved successfully",
        },
        404: {
            "description": "Model not found",
            "content": {
                "application/json": {
                    "example": {
                        "errors": ["Model not found"],
                    }
                }
            },
        },
    },
)
async def get_model(model_name: str = Path(description="Name of a model")):
    """
    Get a model by name

    Args:
        model_name (str): Name of the model
        response (JSONResponse): Response object

    Returns:
        JSONResponse: Response object
    """
    if MODEL_MANAGER.is_model_present(model_name):
        model_schema: dict = MODEL_MANAGER.get_model_schema(model_name)
        return ModelResponse(model_name=model_name, model_schema=model_schema)
    else:
        raise HTTPException(status_code=404, detail=f'Model "{model_name}" not found')


# @router.post(
#     "/",
#     summary="Upload a model",
#     description=(DOCS_BASE_PATH / "upload_model.md").read_text(encoding="utf-8"),
#     status_code=status.HTTP_201_CREATED,
#     responses={
#         201: {
#             "description": "Model uploaded successfully",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "message": "Model uploaded successfully",
#                     }
#                 }
#             },
#         },
#         400: {
#             "description": "Model could not be uploaded",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "errors": ["Model could not be uploaded"],
#                     }
#                 }
#             },
#         },
#     },
# )
async def post_model(file: UploadFile, response: JSONResponse):
    """
    Post a model

    Args:
        file (UploadFile): File object
        response (JSONResponse): Response object

    Returns:
        JSONResponse: Response object
    """
    message: str = ""
    errors: list[str] = []
    warnings: list[str] = []
    if not str(file.filename).endswith(".py"):
        raise HTTPException(
            status_code=400, detail="Model should be a Python file (.py)!"
        )
    # if file.filename in ("asset_model.py", "edge_model.py", "node_model.py"):
    if file.filename in os.listdir("models/base/"):
        raise HTTPException(
            status_code=400, detail="Model name cannot be one of the reserved names!"
        )
    if file.filename in os.listdir(MODEL_MANAGER.models_directory_path):
        warnings.append("File overwritten")
    try:
        if not errors:
            with open(
                MODEL_MANAGER.models_directory_path / str(file.filename), "wb"
            ) as buffer:
                buffer.write(file.file.read())
            MODEL_MANAGER.reload_models()
            message = "Model uploaded successfully"
            response.status_code = status.HTTP_201_CREATED
    except Exception as exception:
        os.remove(MODEL_MANAGER.models_directory_path / str(file.filename))
        raise HTTPException(
            status_code=500, detail="Model could not be uploaded"
        ) from exception
    if warnings:
        return {"message": message, "warnings": warnings}
    return {"message": message}


@router.post(
    "/reload",
    summary="Reload models",
    description=(DOCS_BASE_PATH / "reload_models.md").read_text(encoding="utf-8"),
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {
            "description": "Models will be reloaded",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Models reloaded successfully",
                    }
                }
            },
        },
    },
)
async def reload_models():
    """
    ## Reload models
    Tries to reload all models in the API.
    """
    MODEL_MANAGER.reload_models()
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "Models reloaded successfully"},
    )


def get_field_descriptions(model_name: str):
    model = MODEL_MANAGER.get_model(model_name)
    descriptions: dict = {}
    for field_name, field_info in model.model_fields:
        descriptions.update({field_name: field_info.description or "unspecified"}) # type: ignore
