import logging
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Body, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json

from configuration import CONFIG
from database import SessionLocal
from utils import AuthenticatedRequest, RequestTypeEnum, backend_to_visjs, BackendGraph
from authentication import is_authenticated
from auth_models import User

logger = logging.getLogger("uvicorn")

router = APIRouter()

templates = Jinja2Templates(directory="templates/forwarding")

FORWARD_SESSION: requests.Session = requests.Session()
FORWARD_SESSION.headers.update({"X-FRONTEND-API-KEY": CONFIG.backend_secret})  # type: ignore


def get_db():
    """
    Provides the database connection.

    Yields:
        Session: The database connection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GraphFilter(BaseModel):
    full_graph: bool = False
    types: List[str] = []
    tags: List[str] = []


@router.get("/get_filtered_graph")
async def get_filtered_graph(
    graph_filter: GraphFilter, user: User = Depends(is_authenticated)
):
    graph_dict: dict = FORWARD_SESSION.post(
        url=f"{CONFIG.backend_url()}/data/filtered",
        json=graph_filter,
        headers={"X-FRONTEND-USER-ID": str(user.id)},
    ).json()
    graph = BackendGraph(**graph_dict)
    return backend_to_visjs(graph)


@router.post("/update_asset/{asset_type}")
async def update_asset(
    asset_type: str,
    asset_data: dict,
    request: Request,
    user: User = Depends(is_authenticated),
):
    logger.info(asset_type)
    logger.info(asset_data)
    db_key = asset_data["db_key"]
    logger.info(db_key)
    update_request = FORWARD_SESSION.put(
        url=f"{CONFIG.backend_url()}/data/{asset_type}/{db_key}",
        json=asset_data,
        # data=json.dumps(asset_data),
        timeout=5,
        headers={"X-FRONTEND-USER-ID": str(user.id)},
    )
    logger.info(update_request.request.body)
    if update_request.status_code != 200:
        return templates.TemplateResponse(
            name="error.html",
            status_code=update_request.status_code,
            context={"errors": [update_request.status_code], "request": request},
        )
    return JSONResponse(content=update_request.json())


@router.post("/create_asset/{asset_type}")
async def add_asset(
    asset_type: str,
    request: Request,
    user: User = Depends(is_authenticated),
    asset_data: Any = Body(...),
):
    try:
        logger.info(asset_type)
        logger.info(asset_data)
        parsed_json: dict = json.loads(asset_data)
        asset_key: str = parsed_json["_key"]
        parsed_json.update({"db_id": f"{asset_type}/{asset_key}"})
        create_request = FORWARD_SESSION.post(
            f"{CONFIG.backend_url()}/data/{asset_type}",
            # json=parsed_json,
            data=json.dumps(parsed_json),
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if create_request.status_code != 200:
            return templates.TemplateResponse(
                name="error.html",
                context={"errors": [create_request.status_code], "request": request},
            )

        return templates.TemplateResponse(
            name="success.html", context={"request": request}
        )
    except Exception as e:
        logger.info(e)


@router.post("/delete_asset/{asset_type}/{asset_key}")
async def delete_asset(
    asset_type: str,
    asset_key: str,
    request: Request,
    user: User = Depends(is_authenticated),
):
    try:
        logger.info(asset_type)
        delete_request = FORWARD_SESSION.delete(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if delete_request.status_code != 200:
            return templates.TemplateResponse(
                name="error.html",
                context={"errors": [delete_request.status_code], "request": request},
            )

        return templates.TemplateResponse(
            name="success.html", context={"request": request}
        )
    except Exception as e:
        logger.info(e)


@router.get("/get_asset/{asset_type}/{asset_key}")
async def get_asset(
    asset_type: str, asset_key: str, user: User = Depends(is_authenticated)
):
    try:
        get_request = FORWARD_SESSION.get(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if get_request.status_code != 200:
            return HTMLResponse(content="<h1>Not found!</h1>")
        return JSONResponse(content=get_request.json())
    except Exception as e:
        logger.info(e)



@router.get("/get_tags/{asset_type}/{asset_key}")
async def get_tags_for_node(
    asset_type: str, asset_key: str, user: User = Depends(is_authenticated)
):
    try:
        get_request = FORWARD_SESSION.get(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}/tags",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if get_request.status_code != 200:
            return HTMLResponse(content="<h1>Not found!</h1>")
        return JSONResponse(content=get_request.json())
    except Exception as e:
        logger.info(e)


@router.get("/get_model/{asset_type}")
async def get_model(asset_type: str, user: User = Depends(is_authenticated)):
    try:
        get_request = FORWARD_SESSION.get(
            f"{CONFIG.backend_url()}/models/{asset_type}",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if get_request.status_code != 200:
            return HTMLResponse(content="<h1>Not found!</h1>")
        return JSONResponse(content=get_request.json())
    except Exception as e:
        logger.info(e)


@router.post("/toggle_tag/{asset_type}/{asset_key}/{tag}")
async def toggle_tag(asset_type: str, asset_key: str, tag: str, user: User = Depends(is_authenticated)):
    try:
        post_request = FORWARD_SESSION.post(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}/tags/{tag}",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if post_request.status_code != 200:
            return JSONResponse(post_request.json(), status_code=post_request.status_code)
    except Exception as e:
        logger.info(e)


class TagInput(BaseModel):
    name: str


@router.post("/create_tag")
async def create_tag(tag: TagInput, user: User = Depends(is_authenticated)):
    try:
        post_request = FORWARD_SESSION.post(
            f"{CONFIG.backend_url()}/data/tags",
            timeout=5,
            headers={"X-FRONTEND-USER-ID": str(user.id)},
            data=tag.model_dump_json()
        )
        if post_request.status_code != 200:
            return JSONResponse(post_request.json(), status_code=post_request.status_code)
    except Exception as e:
        logger.info(e)


@router.get("/get_notes/{asset_type}/{asset_key}")
async def get_notes(
    asset_type: str,
    asset_key: str,
    request: Request,
    user: User = Depends(is_authenticated),
):
    try:
        get_notes_request = FORWARD_SESSION.get(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}/notes",
            headers={"X-FRONTEND-USER-ID": str(user.id)},
        )
        if get_notes_request.status_code != 200:
            return templates.TemplateResponse(
                name="error.html",
                context={"errors": [get_notes_request.status_code], "request": request},
            )

        return PlainTextResponse(get_notes_request.text)
    except Exception as e:
        logger.info(e)


class NotesRequest(BaseModel):
    notes: str


@router.post("/set_notes/{asset_type}/{asset_key}")
async def update_notes(
    asset_type: str,
    asset_key: str,
    request: Request,
    notes: str = Body(default="", media_type="text/plain"),
    user: User = Depends(is_authenticated),
):
    try:
        logger.info(notes)
        update_notes_request = FORWARD_SESSION.post(
            f"{CONFIG.backend_url()}/data/{asset_type}/{asset_key}/notes",
            data=notes,
            headers={"X-FRONTEND-USER-ID": str(user.id), "Content-Type": "text/plain"},
        )
        if update_notes_request.status_code != 200:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "errors": [update_notes_request.status_code],
                    "request": request,
                },
                status_code=400,
            )

        return PlainTextResponse(update_notes_request.text, media_type="text/plain")
    except Exception as e:
        logger.info(e)
