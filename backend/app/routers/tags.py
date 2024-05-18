"""
tags.py

This module contains the endpoints for the tags.
"""

import logging
from pathlib import Path as OSPath

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.base.asset_tag import AssetTag

DOCS_BASE_PATH = OSPath("docs/endpoints/models/")

logger = logging.getLogger("uvicorn")

router = APIRouter()


@router.get("/", response_class=JSONResponse)
async def get_tags(request: Request):
    raise Exception("Unimplemented")


@router.get("/{tag_name}")
async def get_tag(tag_name: str):
    raise Exception("Unimplemented")


@router.post("/")
async def create_tag(new_tag: AssetTag):
    raise Exception("Unimplemented")


@router.put("/{tag_name}")
async def update_tag(tag_name: str, updated_tag: AssetTag):
    raise Exception("Unimplemented")
