import enum
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, List
from uuid import uuid4

import requests
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
    PlainTextResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import auth_crud
from auth_models import User
import auth_schemas
from database import SessionLocal
from responses.health_check import HealthCheck
from routers import auth, forward, dashboard
from utils import BackendGraph, backend_to_visjs
from configuration import CONFIG

app = FastAPI(title="Game Asset Graph Manager - Frontend")


logger = logging.getLogger("uvicorn")
logger.propagate = False

secret_key = os.getenv("BACKEND_KEY") or "secret_key"
if not CONFIG.backend_secret:
    logger.fatal("Couldn't find backend communication key!")
    sys.exit(1)

logger.info("Secret: " + CONFIG.backend_secret) if CONFIG.debug_mode else None

# session_middleware = SessionMiddleware(
#     app=app,
#     secret_key=secret_key,
#     session_cookie="session",
#     same_site="lax",
#     https_only=False,
# )


app.include_router(forward.router, tags=["forward"], prefix="/forward")
app.include_router(auth.router, tags=["auth"])
app.include_router(dashboard.router, prefix="/dashboard")

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(
    directory="templates",
    autoescape=True,
    auto_reload=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


class AuthException(Exception): ...


@app.exception_handler(exc_class_or_status_code=status.HTTP_401_UNAUTHORIZED)
async def redirect_to_login(request: Request, exc: HTTPException):
    request.session.pop("user", None)
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@app.exception_handler(exc_class_or_status_code=status.HTTP_403_FORBIDDEN)
async def redirect_to_home(request: Request, exc: HTTPException):
    return RedirectResponse("/main", status_code=status.HTTP_302_FOUND)


@app.exception_handler(AuthException)
async def auth_failed(request: Request, exc: AuthException):
    return templates.TemplateResponse(
        "user/login.html",
        status_code=status.HTTP_401_UNAUTHORIZED,
        context={
            "error": {"message": "Incorrect credentials!", "status": "Failed"},
            "request": request,
        },
    )


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


if CONFIG.debug_mode:
    db = SessionLocal()
    admin = auth_crud.create_user(
        db,
        auth_schemas.UserCreate(email=CONFIG.admin_email, password=CONFIG.admin_pass),
    )
    result = (
        db.query(User)
        .filter_by(id=admin.id)
        .update({"is_admin": True, "is_active": True})
    )
    (
        logger.info(f"Admin user created: {admin}")
        if result != 0
        else logger.error("Admin user creation failed!")
    )
    admin_key = auth_crud.create_api_key(
        db, admin.id, "asd", (datetime.now() + timedelta(days=30))
    )
    (
        logger.info(f"API key created with ID: {admin_key.id}")
        if admin_key
        else logger.error("API key creation failed!")
    )
    db.commit()
    db.close()


BACKEND_SESSIONS: dict[str, requests.Session] = {}


def is_authenticated(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Checks if the request contains a valid session cookie.

    Args:
        request (Request): The request object.

    Raises:
        HTTPException: 401 if the user is not authenticated.

    Returns:
        User: The authenticated user.
    """
    user_email = request.session.get("user")
    # logger.info(f"Login check\n{request.session=}")
    # logger.info(f"{user_email=}")
    user: User = db.query(User).filter_by(email=user_email).first()
    # logger.info(f"{BACKEND_SESSIONS.get(str(user.id))=}") # type: ignore
    if not user_email or not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def is_admin(user: User = Depends(is_authenticated)) -> User:
    """
    Checks if the user is an admin.

    Args:
        user (User): The authenticated user.

    Raises:
        HTTPException: 403 if the user is not an admin.

    Returns:
        User: The authenticated user.
    """
    if not bool(user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


def create_backend_user_session(user_id: str) -> None:
    user_session = requests.Session()
    user_session.headers.update(
        {"X-FRONTEND-API-KEY": CONFIG.backend_secret, "X-FRONTEND-USER-ID": user_id}
    )  # type: ignore
    BACKEND_SESSIONS.update({user_id: user_session})


def authenticate(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    """
    Authenticate a user based on email and password.

    Args:
        email (str): The user's email.
        password (str): The user's password.

    Raises:
        HTTPException: 401 if the user is not authenticated.

    Returns:
        User: The authenticated user.
    """
    hashed_password = hashlib.sha512(password.encode("utf-8")).hexdigest()
    if not auth_crud.check_password(db, email, hashed_password):
        raise AuthException()
    user = auth_crud.get_user_by_email(db, email)
    create_backend_user_session(str(user.id))
    return user


def get_api_keys(
    user: User = Depends(is_authenticated), db: Session = Depends(get_db)
) -> List[auth_schemas.ApiKey]:
    """
    Get the API keys for the authenticated user.

    Args:
        user (User): The authenticated user.

    Returns:
        List[APIKey]: The API keys for the user.
    """
    return auth_crud.get_api_keys_by_user_id(db, user.id)


START_TIME = datetime.now()


@app.get(
    "/health",
    tags=["health_check"],
    summary="Perform a Health Check",
    description=Path("docs/endpoints/health_check.md").read_text(encoding="utf-8"),
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def health_check() -> HealthCheck:
    """
    Endpoint to perform a health check on the service.

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(start_time=START_TIME)


@app.get("/", response_class=HTMLResponse)
async def index_get(request: Request):
    return RedirectResponse("/main", status_code=status.HTTP_302_FOUND)


@app.get("/login")
def login_page(request: Request):
    logger.info(BACKEND_SESSIONS)
    logger.info(request.session)
    if request.session.get("user"):
        return RedirectResponse("/main", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("user/login.html", context={"request": request})


@app.post("/login")
async def login(
    request: Request,
    user: User = Depends(authenticate),
):
    request.session.update({"user": user.email})
    response = RedirectResponse("/main", status_code=status.HTTP_302_FOUND)
    return response


@app.post("/logout")
async def logout(request: Request, user: User = Depends(is_authenticated)):
    try:
        logger.info(request.session)
        request.session.pop("user")
        BACKEND_SESSIONS.pop(str(user.id))
    finally:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


# @app.post("/update_asset", response_class=HTMLResponse)
# async def update_asset(request: Request):
#     # logger.info(request.get("json"))
#     # request form
#     # logger.info(await request.form())
#     # request_form = await request.form()
#     json_data: dict = await request.json()
#     type_name = json_data["type"]
#     db_key = json_data['db_key']
#     logger.info(json_data["type"])
#     logger.info(json_data)
#     # logger.info(type(data))

#     result = requests.put(
#         f"http://{CONFIG['backend']['ip']}:{CONFIG['backend']['port']}/data/{type_name}/{db_key}",
#         json=json_data,
#         timeout=5,
#         headers={"X-API-KEY": "test_key"}
#     )
#     if result.status_code != 200:
#         raise HTTPException(result.status_code, result.content)
#     # logger.info(result.content)
#     # return RedirectResponse(url="/graph-view")
#     return "ok"


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


def get_tags(
    user: User = Depends(is_authenticated),) -> list[str]:
    tags = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/tags",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()
    return tags


@app.get("/graph-view/", response_class=HTMLResponse)
async def graph_view_get(
    request: Request,
    # graph_filter: GraphViewFilter = GraphViewFilter(
    #     tag_filter_type=InclusionEnum.EXCLUDE, type_filter_type=InclusionEnum.EXCLUDE
    # ),
    user: User = Depends(is_authenticated),
    # db: Session = Depends(get_db),
):
    # logger.info(graph_filter)
    # Mock tags (["tag1": {"name": "Tag 1"}, ...])
    # tags = requests.get(
    #     url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/tags",
    #     headers={
    #         "X-FRONTEND-API-KEY": CONFIG.backend_secret,
    #         "X-FRONTEND-USER-ID": str(user.id),
    #     },
    # ).json()
    tags = get_tags(user)
    logger.info(tags)
    # mock_tags = []
    # response = RedirectResponse(url=)
    graph = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()

    logger.error(json.dumps(graph))

    graph = BackendGraph(edges=graph.get("edges"), nodes=graph.get("nodes"))
    visjs_graph = backend_to_visjs(backend_graph=graph)

    model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    node_model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/?model_type=node",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    edge_model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/?model_type=edge",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    return templates.TemplateResponse(
        "user/graph_view.html",
        {
            "request": request,
            "tags": tags,
            "edges": json.dumps(visjs_graph["edges"]),
            "nodes": json.dumps(visjs_graph["nodes"]),
            "model_names": model_names,
            "node_model_names": node_model_names,
            "edge_model_names": edge_model_names,
            # "current_filter": graph_filter,
        },
        status_code=200,
    )


@app.post("/get_graph")
async def get_graph(
    request: Request,
    graph_filter: GraphViewFilter = GraphViewFilter(
        tag_filter_type=InclusionEnum.EXCLUDE, type_filter_type=InclusionEnum.EXCLUDE
    ),
    user: User = Depends(is_authenticated),
):
    logger.info(graph_filter.model_dump_json())
    tags = get_tags(user)
    graph = requests.post(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/filtered",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
        data=graph_filter.model_dump_json()
    ).json()

    graph = BackendGraph(**graph)
    visjs_graph = backend_to_visjs(backend_graph=graph)

    model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    node_model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/?model_type=node",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    edge_model_names: list[str] = requests.get(
        url=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/models/?model_type=edge",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        },
    ).json()["model_names"]

    # tags: list[str] = []
    return JSONResponse(content={
        "edges": json.dumps(visjs_graph["edges"]),
        "nodes": json.dumps(visjs_graph["nodes"]),
        "current_filter": graph_filter.model_dump_json(),
    })

    return templates.TemplateResponse(
        "user/graph_view.html",
        {
            "request": request,
            "tags": tags,
            "edges": json.dumps(visjs_graph["edges"]),
            "nodes": json.dumps(visjs_graph["nodes"]),
            "model_names": model_names,
            "node_model_names": node_model_names,
            "edge_model_names": edge_model_names,
            "current_filter": graph_filter,
        },
        status_code=200,
    )


class GraphViewQuery(BaseModel):
    full_graph: bool
    active_tags: list[str]


@app.post("/visjs_graph")
async def graph_view_post(request: GraphViewQuery):
    if request is None:
        request = GraphViewQuery(full_graph=True, active_tags=[])

    graph = None
    if request.full_graph:
        graph = (
            requests.get(
                f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/"
            ).json()
            or {}
        )
        graph = BackendGraph(**graph)

    visjs_graph = backend_to_visjs(backend_graph=graph)
    return visjs_graph


@app.get("/main", response_class=HTMLResponse)
async def main_page(request: Request, user: User = Depends(is_authenticated)):
    return templates.TemplateResponse(
        "user/main.html", {"request": request, "user": user}, status_code=200
    )


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(is_authenticated),
    api_keys: List[auth_schemas.ApiKey] = Depends(get_api_keys),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "user/profile.html",
        {"request": request, "user_data": user, "api_keys": api_keys},
        status_code=200,
    )


@app.post("/generate_key")
async def generateApiKey(
    data: auth_schemas.ApiKeyCreate,
    user: User = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    logger.info(data)
    user_id: int = user.id
    api_key = str(uuid4())
    auth_crud.create_api_key(db, user_id, api_key, data.expiration_date)
    return JSONResponse(
        content={
            "api_key": api_key,
            "expiration_date": data.expiration_date.isoformat(),
        }
    )


@app.post("/update_api_key")
async def updateApiKey(
    data: auth_schemas.ApiKeyUpdate,
    user: User = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    auth_crud.update_api_key(db, data.id, data.active)
    return PlainTextResponse("OK")


@app.post("/profile", response_class=HTMLResponse)
async def update_profile(request: Request):
    return "Unimplemented"


@app.get("/admin-dashboard")
async def admin_dashboard(request: Request, user: User = Depends(is_admin)):
    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request, "user": user.id}, status_code=200
    )


@app.get("/admin/users")
def user_management_page(
    request: Request,
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
) -> List[auth_schemas.User]:
    logger.info(auth_crud.get_users(db, 0, 100))
    return auth_crud.get_users(db, 0, 100)


@app.get("/admin/users/{id}")
def get_user(
    id: int,
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
) -> auth_schemas.User:
    return auth_crud.get_user(db, id)


@app.post("/admin/users")
def create_user(
    user: auth_schemas.UserCreate,
    db: Session = Depends(get_db),
):
    return auth_crud.create_user(db, user)


@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
):
    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself!"
        )
    auth_crud.delete_user(db, user_id)
    return PlainTextResponse("OK")


@app.post("/admin/users/{user_id}")
def deactivate_user(
    user_id: int,
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
):
    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself!",
        )
    auth_crud.deactivate_user(db, user_id)
    return PlainTextResponse("OK")


@app.get("/admin/api-keys")
def admin_get_api_keys(
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
) -> List[auth_schemas.ApiKeyAdminQuery]:
    return auth_crud.get_all_api_keys(db)


@app.get("/admin/tags")
def tag_management(
    tags: list[str] = Depends(get_tags),
    user: User = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return tags


@app.delete("/admin/tags/{tag_name}")
def delete_tag(
    tag_name: str,
    user: User = Depends(is_admin),
):
    result = requests.delete(
        f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}/data/tags/{tag_name}",
        headers={
            "X-FRONTEND-API-KEY": CONFIG.backend_secret,
            "X-FRONTEND-USER-ID": str(user.id),
        }
    )
    if result.status_code != 200:
        raise HTTPException(result.status_code, result.content)
    return PlainTextResponse("OK")


@app.post("/change_password")
def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(is_authenticated),
):
    logger.info(user)
    logger.info(old_password)
    logger.info(new_password)
    hashed_old_password = hashlib.sha512(old_password.encode("utf-8")).hexdigest()
    db_user = auth_crud.get_user_by_email(db, email=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not auth_crud.check_password(
        db, email=db_user.email, password_hash=hashed_old_password
    ):
        raise HTTPException(status_code=403, detail="Incorrect password")
    hashed_password = hashlib.sha512(new_password.encode("utf-8")).hexdigest()
    db_user.hashed_password = hashed_password
    db.commit()
    return RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)


app.add_middleware(SessionMiddleware, secret_key=secret_key)


if __name__ == "__main__":
    import uvicorn

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    uvicorn.run(app, host="0.0.0.0", port=5000)
