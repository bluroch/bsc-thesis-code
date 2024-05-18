
import logging
from pathlib import Path as OSPath
import os
import secrets

from fastapi import APIRouter, Depends
from auth_methods import check_frontend_key


logger = logging.getLogger("uvicorn")

os.chdir(OSPath(__file__).parent.parent.resolve())

DOCS_BASE_PATH = OSPath("docs/endpoints/auth")

# router = APIRouter(dependencies=[Depends(check_frontend_key)])
router = APIRouter()

router.get("/generate-key")
async def generate_key():
    logger.info("key generated")
    key = secrets.randbits(128).to_bytes().hex()
    return key

logger.info("auth router set up")