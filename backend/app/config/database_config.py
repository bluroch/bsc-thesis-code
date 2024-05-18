"""
This module contains the configuration class for the database connection.
"""

import json
from pathlib import Path

from pydantic import BaseModel


class DataBaseConfig(BaseModel):
    """
    Configuration class for the database connection.

    Attributes:
        host (str): The IP address of the database server.
        port (int): The port number of the database server.
        protocol (str): The protocol used for the database connection.
        path (str): The path to the database server.
    """

    host: str = "127.0.0.1"
    port: int = 10466
    protocol: str = "gremlin"
    path: str = "gremlin-server"

    # ws://localhost:8182/gremlin

    def __str__(self):
        return f"{self.protocol}//{self.host}:{self.port}/{self.path}"

    def __init__(self, config_path: Path):
        with open(file=config_path, mode="r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        super().__init__(**config)
