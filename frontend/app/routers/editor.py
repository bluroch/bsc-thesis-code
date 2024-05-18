import logging

from fastapi import APIRouter, Request

logger = logging.getLogger("uvicorn")

router = APIRouter()


async def get_json_editor_panel(request: Request):
    pass


async def get_note_editor_panel(request: Request):
    pass


async def get_table_editor_panel(request: Request):
    pass


async def get_graph_editor_panel(request: Request):
    pass
