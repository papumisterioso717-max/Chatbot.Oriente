from pydantic import BaseModel, ConfigDict, Field

from app.models.node import Node


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=128)
    option_id: str = Field(min_length=1, max_length=128)
    revision: int = Field(ge=0)


class ConversationState(BaseModel):
    session_id: str
    bot_name: str
    node_id: str
    node: Node
    history: list[str]
    revision: int
