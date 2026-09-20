from pathlib import Path

from app.models.content import FileContent
from app.models.knowledge import Knowledge


MEDIA_TYPES = {
    ".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}


class FileManager:
    """Read only files explicitly referenced by the validated knowledge graph."""

    def __init__(self, root: Path, knowledge: Knowledge):
        self.root = root.resolve()
        self.references = {
            item.file for node in knowledge.nodes.values() for item in node.content
            if isinstance(item, FileContent)
        }

    def resolve(self, reference: str) -> Path:
        if reference not in self.references:
            raise FileNotFoundError("Archivo no publicado en la conversación.")
        candidate = self.root / reference
        if any(part.is_symlink() for part in (candidate, *candidate.parents) if part != self.root):
            raise FileNotFoundError("No se permiten enlaces simbólicos en las referencias.")
        path = candidate.resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise FileNotFoundError("El archivo no existe dentro de storage.")
        return path

    def validate(self):
        for reference in sorted(self.references):
            try:
                self.resolve(reference)
            except (OSError, RuntimeError) as error:
                raise ValueError(f"Referencia de archivo inválida: {reference}. {error}") from error
