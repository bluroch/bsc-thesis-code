from typing import ClassVar, List
from gagm_base.edge_model import EdgeModel


class CheckpointOfDungeon(EdgeModel):
    origin_type: ClassVar[List[str]] = ["Dungeon"]
    target_type: ClassVar[List[str]] = ["Checkpoint"]

    class Config:
        """
        Configuration of the CheckpointOfDungeon
        """

        title: str = "CheckpointOfDungeon"
        description: str = (
            "An example model that should represent a checkpoint of a dungeon."
        )
        version = "v1"
