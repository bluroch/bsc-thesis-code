from .ex_location import Location


class Position(Location):
    """
    A class that extends the Location class with yaw and pitch parameters.
    """

    yaw: float = 0.0
    pitch: float = 0.0

    class Config:
        """
        Configuration of the Position
        """

        title: str = "Position"
        description: str = "An example model that should represent a position of an entity in the game world."
        version = "v1"
