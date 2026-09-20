from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.node import Node


class Bot(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1)
    start_node: str = Field(min_length=1)


class Knowledge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    bot: Bot
    nodes: dict[str, Node] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_references(self):
        if self.bot.start_node not in self.nodes:
            raise ValueError("El nodo inicial no existe.")
        for node_id, node in self.nodes.items():
            if not node_id or not node_id.isascii() or not all(
                character.isalnum() or character in "_-" for character in node_id
            ):
                raise ValueError(f"ID de nodo inválido: {node_id!r}.")
            for option in node.options:
                if option.next is not None and option.next not in self.nodes:
                    raise ValueError(f"{node_id}/{option.id}: destino inexistente {option.next!r}.")
        return self
