from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal

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


class DiagramChange(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: str
    action: Literal["create", "switch", "rename", "delete"]
    diagram_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=80)
    knowledge: Knowledge | None = None

    @model_validator(mode="after")
    def valid_action(self):
        if self.action in ("create", "rename") and not self.name:
            raise ValueError("Escribe un nombre para el diagrama.")
        if self.action != "create" and not self.diagram_id:
            raise ValueError("Selecciona un diagrama.")
        if self.knowledge is not None and self.action != "create":
            raise ValueError("Solo se puede importar al crear un diagrama.")
        return self
