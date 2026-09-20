from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from pydantic import TypeAdapter, ValidationError

from app.models.content import Content
from app.services.file_manager import FileManager
from app.services.yaml_manager import YamlManager
import test_phase1

ROOT = test_phase1.ROOT


class ContentTests(unittest.TestCase):
    def test_valid_types_and_legacy_text(self):
        adapter = TypeAdapter(Content)
        for item in [
            {"type": "text", "text": "Hola"},
            {"type": "link", "label": "Web", "url": "https://example.com"},
            {"type": "image", "file": "images/foto.png"},
            {"type": "document", "label": "Guía", "file": "documents/guía.pdf"},
        ]:
            self.assertEqual(adapter.validate_python(item).type, item["type"])

    def test_reject_unsafe_links_and_paths(self):
        adapter = TypeAdapter(Content)
        for url in ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,test",
                    "https://user:secret@example.com", "no es una URL"]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                adapter.validate_python({"type": "link", "label": "Web", "url": url})
        for path in ["../secreto.txt", "/documents/a.txt", "documents/../a.txt",
                     "documents/%2e%2e/a.txt", "documents/a.html", "documents/a.txt?x=1",
                     "documents\\a.txt", "documents//a.txt", "images/a.txt"]:
            with self.subTest(path=path), self.assertRaises(ValidationError):
                adapter.validate_python({"type": "document", "label": "Archivo", "file": path})
        with self.assertRaises(ValidationError):
            adapter.validate_python({"type": "image", "file": "images/script.svg"})

    def test_missing_unpublished_and_symlink_files(self):
        knowledge = YamlManager(ROOT / "data/knowledge.yaml").load()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = FileManager(root, knowledge)
            with self.assertRaises(ValueError):
                manager.validate()
            (root / "secret.txt").write_text("private", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                manager.resolve("secret.txt")
            with self.assertRaises(FileNotFoundError):
                manager.resolve("../requirements.txt")
            (root / "documents").mkdir()
            target = root / "documents/guia.txt"
            try:
                target.symlink_to(root / "secret.txt")
            except OSError:
                self.skipTest("El sistema no permite crear enlaces simbólicos.")
            with self.assertRaises(FileNotFoundError):
                manager.resolve("documents/guia.txt")


class FileApiTests(unittest.TestCase):
    setUpClass = classmethod(test_phase1.ApiTests.setUpClass.__func__)
    tearDownClass = classmethod(test_phase1.ApiTests.tearDownClass.__func__)
    request_json = test_phase1.ApiTests.request_json
    def test_file_preview_download_and_image(self):
        for suffix, disposition in [("", "inline"), ("?download=true", "attachment")]:
            with urlopen(self.base + "/api/files/documents/guia.txt" + suffix) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(disposition, response.headers["Content-Disposition"])
                self.assertIn("text/plain", response.headers["Content-Type"])
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertIn("GUÍA", response.read().decode("utf-8"))
        with urlopen(self.base + "/api/files/images/recorrido.png") as response:
            self.assertEqual(response.headers["Content-Type"], "image/png")
            self.assertTrue(response.read().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_file_access_denied(self):
        for path in ["documents/missing.txt", "../requirements.txt",
                     "%2e%2e/requirements.txt", "documents/%2e%2e/%2e%2e/requirements.txt"]:
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.base + "/api/files/" + path)
            self.assertEqual(error.exception.code, 404)

    def test_mixed_content_preserves_order(self):
        code, node = self.request_json("/api/chat/node/recursos")
        self.assertEqual(code, 200)
        self.assertEqual([item["type"] for item in node["content"]],
                         ["text", "image", "document", "link"])
        self.assertEqual(node["content"][1]["file"], "images/recorrido.png")
