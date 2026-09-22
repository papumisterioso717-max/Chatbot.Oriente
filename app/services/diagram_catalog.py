"""Atomic collection of diagrams, with one active tree for the chatbot."""
import json
import os
import tempfile
from uuid import uuid4

from app.models.knowledge import Knowledge
from app.services.chatbot_engine import ChatError


class DiagramCatalog:
    def __init__(self, original):
        self.path = original.path.with_name("diagrams.json")
        if not self.path.exists():
            self.write({"version": 1, "active": "diagrama-1", "diagrams": {
                "diagrama-1": {"name": "Diagrama 1", "knowledge": original.load().model_dump(mode="json", exclude_none=True)}
            }})

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, data):
        descriptor, temporary = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def load(self):
        data = self.read()
        return Knowledge.model_validate(data["diagrams"][data["active"]]["knowledge"])

    def save(self, knowledge):
        data = self.read()
        data["diagrams"][data["active"]]["knowledge"] = knowledge.model_dump(mode="json", exclude_none=True)
        self.write(data)

    @staticmethod
    def change(data, action, diagram_id=None, name=None, knowledge=None):
        diagrams = data["diagrams"]
        if action in ("create", "rename"):
            if any(item["name"].casefold() == name.casefold() for key, item in diagrams.items() if key != diagram_id):
                raise ChatError("Ya existe un diagrama con ese nombre.", 409)
        if action == "create":
            diagram_id = uuid4().hex
            diagrams[diagram_id] = {"name": name, "knowledge": knowledge or {
                "version": 1, "bot": {"name": name, "start_node": "inicio"},
                "nodes": {"inicio": {"type": "question", "content": [{"type": "text", "text": "¡Hola! Elige una opción para comenzar."}], "options": []}}
            }}
            data["active"] = diagram_id
        else:
            if diagram_id not in diagrams:
                raise ChatError("El diagrama ya no existe.", 404)
            if action == "switch":
                data["active"] = diagram_id
            elif action == "rename":
                diagrams[diagram_id]["name"] = name
            elif action == "delete":
                if len(diagrams) == 1:
                    raise ChatError("Conserva al menos un diagrama. Crea otro antes de eliminar este.", 409)
                del diagrams[diagram_id]
                if data["active"] == diagram_id:
                    data["active"] = next(iter(diagrams))
        return data
