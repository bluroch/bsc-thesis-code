from gagm_base.node_model import NodeModel
from pydantic import field_validator
from .ex_location import Location


class Dungeon(NodeModel):
    name: str
    max_players: int = 1
    starting_point: Location
    description: str

    @field_validator("max_players")
    @classmethod
    def min_max_player_count(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("Max player count should be between 1 and 5.")
        return value

    class Config:
        """
        Configuration of the Dungeon
        """

        title: str = "Dungeon"
        description: str = "An example model that can represent a dungeon."
        version = "v1"
