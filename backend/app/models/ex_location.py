from pydantic import BaseModel


class Location(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    class Config:
        """
        Configuration of the Location
        """

        title: str = "Location"
        description: str = (
            "An example model that should represent a location in the game world."
        )
        version = "v1"
        frozen = True
