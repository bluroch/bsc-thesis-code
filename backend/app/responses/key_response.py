from pydantic import BaseModel


class KeyResponse(BaseModel):
    api_key: str
    email: str
