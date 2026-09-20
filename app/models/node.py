from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.content import Content
from app.models.option import Option


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["question", "information"]
    content: list[Content] = Field(min_length=1)
    options: list[Option] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_options(self):
        ids = [option.id for option in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("Los IDs de opciones deben ser únicos dentro de cada nodo.")
        return self
