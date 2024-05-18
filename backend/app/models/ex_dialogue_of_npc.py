from typing import ClassVar, List

from pydantic import Field

from gagm_base.edge_model import EdgeModel


class DialogueOfNPC(EdgeModel):
    repeatable: bool = Field(
        description="Indicates whether the dialogue can be repeated or not.",
        default=False,
    )
    origin_type: ClassVar[List[str]] = ["NPC"]
    target_type: ClassVar[List[str]] = ["DialogueElement"]

    class Config:
        """
        Configuration of the DialogueElementElement
        """

        title: str = "DialogueOfNPC"
        description: str = "An example model that should represent the connection between a DialogueElement and an NPC. It has a repeatable property, which indicates whether the dialogue can be repeated or not."
        version = "v1"
