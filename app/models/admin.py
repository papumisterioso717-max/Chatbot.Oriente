from pydantic import BaseModel, ConfigDict, Field

from app.models.node import Node
from app.models.knowledge import Knowledge


class TreeWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str
    knowledge: Knowledge


class NodeWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str
    node_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    node: Node


class DeleteNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str
