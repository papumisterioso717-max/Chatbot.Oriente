from fastapi import APIRouter, Request

from app.controllers.chat_controller import ChatController
from app.models.conversation import BackRequest, ConversationState, Selection
from app.models.node import Node

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def controller(request: Request) -> ChatController:
    return request.app.state.chat_controller


@router.get("/start", response_model=ConversationState)
def start(request: Request):
    return controller(request).start()


@router.post("/select", response_model=ConversationState)
def select(selection: Selection, request: Request):
    return controller(request).select(selection)


@router.get("/node/{node_id}", response_model=Node)
def node(node_id: str, request: Request):
    return controller(request).node(node_id)


@router.post("/back", response_model=ConversationState)
def back(navigation: BackRequest, request: Request):
    return controller(request).back(navigation)
