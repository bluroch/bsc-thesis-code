from gagm_base.node_model import NodeModel


class DialogueElement(NodeModel):
    dialogue_line: str

    class Config:
        """
        Configuration of the DialogueElementElement
        """

        title: str = "DialogueElementElement"
        description: str = "An example model that should represent a line of dialogue."
        version = "v1"
