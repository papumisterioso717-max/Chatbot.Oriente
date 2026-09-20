from fastapi.responses import FileResponse

from app.services.chatbot_engine import ChatError
from app.services.file_manager import FileManager, MEDIA_TYPES


class FileController:
    def __init__(self, manager: FileManager):
        self.manager = manager

    def read(self, reference: str, download: bool):
        try:
            path = self.manager.resolve(reference)
        except (OSError, RuntimeError) as error:
            raise ChatError("El archivo no está disponible.", 404) from error
        suffix = path.suffix.lower()
        previewable = suffix in {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
        return FileResponse(
            path, media_type=MEDIA_TYPES[suffix], filename=path.name,
            content_disposition_type="attachment" if download or not previewable else "inline",
            headers={"X-Content-Type-Options": "nosniff"},
        )
