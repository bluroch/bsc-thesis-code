from gagm_base.node_model import NodeModel
from .ex_position import Position


class Enemy(NodeModel):
    enemy_type: str
    spawn: Position = Position(x=0.0, y=0.0, z=0.0, yaw=45.0, pitch=45.0)

    class Config:
        """
        Configuration of the Enemy
        """

        title: str = "Enemy"
        description: str = (
            "An example model that should represent an enemy in the game world."
        )
        version = "v1"
