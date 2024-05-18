from datetime import datetime

from pydantic import BaseModel, computed_field


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"
    start_time: datetime

    @computed_field
    @property
    def uptime(self) -> str:
        """Return the uptime as a string."""
        return f"{(datetime.now() - self.start_time)}"
