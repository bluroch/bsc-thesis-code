import enum
import logging
from pydantic import BaseModel, Field
import requests

from configuration import CONFIG

logger = logging.getLogger("uvicorn")


class BackendGraph(BaseModel):
    """
    Represents a graph returned by the backend.
    """

    edges: dict[str, dict]
    nodes: dict[str, dict]


def backend_to_visjs(backend_graph: BackendGraph) -> dict:
    """
    Converts a graph returned by the GAGM backend into a VisJS compatible format.

    Args:
        backend_graph (BackendGraph): The graph from the GAGM backend.

    Returns:
        dict: The graph in a VisJS compatible format.
    """
    logger.info(backend_graph)
    visjs_graph = {"edges": [], "nodes": []}
    typed_edges: dict[str, dict[str, dict]] = backend_graph.edges
    for edge_type, edges_with_type in typed_edges.items():
        for edge_key, edge_data in edges_with_type.items():
            db_id: str = edge_data["db_id"]
            type_str = f"[{edge_type}]"
            key_str = f"*{edge_key}*"
            label = str.join('\n', [type_str, key_str])
            transformed_edge = {
                "id": edge_data["db_id"],
                "label": label,
                "type": edge_type,
                "from": edge_data["origin_id"],
                "to": edge_data["target_id"],
                **edge_data,
            }
            visjs_graph["edges"].append(transformed_edge)

    typed_nodes: dict[str, dict[str, dict]] = backend_graph.nodes
    for node_type, nodes_with_type in typed_nodes.items():
        for node_key, node_data in nodes_with_type.items():
            db_id: str = node_data["db_id"]
            type_str = f"[{db_id.split('/')[0]}]"
            key_str = f"*{db_id.split('/')[1]}*"
            label = str.join('\n', [type_str, key_str])
            transformed_node = {
                "id": node_data["db_id"],
                # "label": data["db_key"],
                "label": label,
                "type": node_type,
                **node_data,
            }
            visjs_graph["nodes"].append(transformed_node)

    return visjs_graph


class RequestTypeEnum(enum.Enum):
    GET = requests.get
    POST = requests.post
    PUT = requests.put
    PATCH = requests.patch
    DELETE = requests.delete
    OPTIONS = requests.options
    HEAD = requests.head

    def __call__(self, url: str, *args, **kwargs):
        return self.value(*args, **kwargs)


class AuthenticatedRequest(BaseModel):
    """
    A special request that should be used when the frontend communicates with the backend.
    """
    method: RequestTypeEnum = Field()
    resource_path: str = Field()
    user_id: int = Field()
    base_url: str = Field(default=f"http://{CONFIG.backend_ip}:{CONFIG.backend_port}")

    def _send(self) -> requests.Response:
        return self.method(url=f"{self.base_url}/{self.resource_path}", headers={"X-FRONTEND-API-KEY": CONFIG.backend_secret, "X-FRONTEND-USER-ID": str(self.user_id)})

    def json(self) -> dict:
        return self._send().json()

    def text(self) -> str:
        return self._send().text
