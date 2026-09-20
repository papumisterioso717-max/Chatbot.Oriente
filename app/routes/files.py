from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/files", tags=["Archivos"])


@router.get("/{reference:path}")
def read_file(reference: str, request: Request, download: bool = False):
    return request.app.state.file_controller.read(reference, download)
