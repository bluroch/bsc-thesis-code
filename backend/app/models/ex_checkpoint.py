from gagm_base.node_model import NodeModel
from .ex_location import Location


class Checkpoint(NodeModel):
    location: Location
    activation_radius: float

    class Config:
        """
        Configuration of the Checkpoint
        """

        title: str = "Checkpoint"
        description: str = "An example model that can represent a checkpoint."
        version = "v1"
