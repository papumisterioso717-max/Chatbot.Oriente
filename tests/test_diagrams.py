import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.admin import DiagramChange
from app.models.knowledge import Knowledge
from app.services.yaml_manager import YamlManager
from app.services.diagram_catalog import DiagramCatalog
from app.services.chatbot_engine import ChatbotEngine, ChatError
from app.services.admin_service import AdminService
from app.services.file_manager import FileManager
from app.controllers.file_controller import FileController


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        original = YamlManager(root / "knowledge.yaml")
        original.save(Knowledge.model_validate({"version": 1, "bot": {"name": "Original", "start_node": "inicio"},
            "nodes": {"inicio": {"type": "question", "content": [{"type": "text", "text": "Original"}], "options": []}}}))
        self.original = original
        self.catalog = DiagramCatalog(original)
        knowledge = self.catalog.load()
        self.service = AdminService(self.catalog, ChatbotEngine(knowledge), FileController(FileManager(root, knowledge)))

    def change(self, action, **fields):
        return self.service.diagram_change(DiagramChange(revision=self.service.revision(), action=action, **fields))

    def test_migration_independence_restart_and_restore(self):
        first = self.service.snapshot()
        self.assertEqual(first["diagrams"], [{"id": "diagrama-1", "name": "Diagrama 1"}])
        second = self.change("create", name="Segundo")
        second_id = second["diagram_id"]
        knowledge = Knowledge.model_validate(second["knowledge"])
        knowledge.nodes["inicio"].content[0].text = "Nuevo contenido"
        self.service.replace_tree(second["revision"], knowledge)
        restored = self.change("switch", diagram_id="diagrama-1")
        self.assertEqual(restored["knowledge"]["nodes"]["inicio"]["content"][0]["text"], "Original")
        again = self.change("switch", diagram_id=second_id)
        self.assertEqual(again["knowledge"]["nodes"]["inicio"]["content"][0]["text"], "Nuevo contenido")
        self.assertEqual(DiagramCatalog(self.original).load().nodes["inicio"].content[0].text, "Nuevo contenido")
        imported = self.change("create", name="Restaurado", knowledge=knowledge)
        self.assertEqual(imported["knowledge"], again["knowledge"])

    def test_delete_last_stale_revision_and_duplicate(self):
        with self.assertRaises(ChatError):
            self.change("delete", diagram_id="diagrama-1")
        old = self.service.revision()
        second = self.change("create", name="Segundo")
        with self.assertRaises(ChatError):
            self.change("create", name="segundo")
        with self.assertRaises(ChatError):
            self.service.diagram_change(DiagramChange(revision=old, action="delete", diagram_id=second["diagram_id"]))
        result = self.change("delete", diagram_id=second["diagram_id"])
        self.assertEqual(result["diagram_id"], "diagrama-1")

    def test_failed_write_preserves_catalog_and_chat(self):
        before = self.catalog.path.read_bytes()
        session = self.service.engine.start()
        with patch("app.services.diagram_catalog.os.replace", side_effect=OSError("disk")):
            with self.assertRaises(ChatError):
                self.change("create", name="No guardado")
        self.assertEqual(self.catalog.path.read_bytes(), before)
        self.assertIn(session.session_id, self.service.engine.sessions)

    def test_switch_invalidates_chat_and_rename(self):
        session = self.service.engine.start()
        result = self.change("create", name="Segundo")
        self.assertNotIn(session.session_id, self.service.engine.sessions)
        result = self.change("rename", diagram_id=result["diagram_id"], name="Otro nombre")
        self.assertEqual(result["diagrams"][-1]["name"], "Otro nombre")


if __name__ == "__main__":
    unittest.main()
