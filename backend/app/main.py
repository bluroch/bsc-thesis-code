"""
This module contains the backend API service.
It uses FastAPI to create a RESTful API service.
"""

import logging

# import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from responses.health_check import HealthCheck
from routers import data, models, authentication

logger = logging.getLogger("uvicorn")
logger.propagate = False


app: FastAPI = FastAPI(title="Game Asset Graph Manager - Backend")
app.include_router(authentication.router, tags=["authentication"], prefix="/authentication")
app.include_router(models.router, tags=["models"], prefix="/models")
app.include_router(data.router, tags=["data"], prefix="/data")

# origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


START_TIME = datetime.now()


class EndpointFilter(logging.Filter):
    """
    Filter to exclude specific endpoints from logging.
    """

    _exclude_endpoints: list[str] = ["/health"]

    def filter(self, record: logging.LogRecord) -> bool:
        return any(
            [
                record.getMessage().find(endpoint) == -1
                for endpoint in self._exclude_endpoints
            ]
        )


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
logging.getLogger("uvicorn").addFilter(EndpointFilter())


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
    return HealthCheck(
        start_time=START_TIME, last_reload=models.MODEL_MANAGER.last_reload
    )


@app.get("/")
async def root():
    """
    Index page, redirects to `/docs`.
    """
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import os

    import uvicorn

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    uvicorn.run(app, host="0.0.0.0", port=8000)
