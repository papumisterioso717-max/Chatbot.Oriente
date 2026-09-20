from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Option(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    label: str = Field(min_length=1)
    next: str | None = Field(default=None, min_length=1)
    action: Literal["back", "restart"] | None = None

    @model_validator(mode="after")
    def validate_destination(self):
        if (self.next is None) == (self.action is None):
            raise ValueError("Una opción debe tener exactamente un destino next o una action.")
        return self
