from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request

from app.models.admin import DeleteNode, NodeWrite, TreeWrite, DiagramChange
from app.services.chatbot_engine import ChatError


def local_admin(request: Request):
    # A custom header forces cross-origin JavaScript through a denied CORS preflight.
    if request.headers.get("X-Admin-Request") != "local-panel":
        raise ChatError("Accede desde el panel administrativo local.", 403)
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme not in ("http", "https") or parsed.netloc != request.headers.get("host"):
            raise ChatError("Origen no autorizado.", 403)
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise ChatError("Origen no autorizado.", 403)


router = APIRouter(prefix="/api/admin", tags=["Administración local"], dependencies=[Depends(local_admin)])


@router.get("/tree")
def tree(request: Request):
    return request.app.state.admin_controller.tree()


@router.post("/diagrams")
def diagram_change(body: DiagramChange, request: Request):
    return request.app.state.admin_controller.service.diagram_change(body)


@router.put("/tree")
def save_tree(body: TreeWrite, request: Request):
    return request.app.state.admin_controller.save_tree(body)


@router.post("/node", status_code=201)
def create_node(body: NodeWrite, request: Request):
    return request.app.state.admin_controller.save_node(body, create=True)


@router.put("/node/{node_id}")
def update_node(node_id: str, body: NodeWrite, request: Request):
    if node_id != body.node_id:
        raise ChatError("El ID de un nodo existente no se puede cambiar.", 422)
    return request.app.state.admin_controller.save_node(body)


@router.delete("/node/{node_id}")
def delete_node(node_id: str, body: DeleteNode, request: Request):
    return request.app.state.admin_controller.delete_node(node_id, body)
