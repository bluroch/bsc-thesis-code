from gagm_base.node_model import NodeModel
from .ex_position import Position


class NPC(NodeModel):
    npc_name: str
    pos: Position = Position(x=0.0, y=0.0, z=0.0, yaw=45.0, pitch=45.0)

    class Config:
        """
        Configuration of the NPC
        """

        title: str = "NPC"
        description: str = (
            "An example model that should represent an NPC in the game world."
        )
        version = "v1"
