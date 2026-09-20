import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import test_phase1
from app.controllers.file_controller import FileController
from app.models.node import Node
from app.models.option import Option
from app.services.admin_service import AdminService
from app.services.chatbot_engine import ChatbotEngine, ChatError
from app.services.file_manager import FileManager
from app.services.yaml_manager import YamlManager


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "knowledge.yaml"
        shutil.copyfile(test_phase1.ROOT / "data/knowledge.yaml", self.path)
        self.yaml = YamlManager(self.path)
        self.engine = ChatbotEngine(self.yaml.load())
        self.service = AdminService(self.yaml, self.engine, FileController(
            FileManager(test_phase1.ROOT / "storage", self.engine.knowledge)))

    def revision(self):
        return self.service.snapshot()["revision"]

    def node(self):
        return Node.model_validate({"type":"information", "content":[{"type":"text","text":"Prueba"}], "options":[]})

    def test_crud_and_options_roundtrip(self):
        session = self.engine.start()
        result = self.service.change(self.revision(), "prueba", self.node(), True)
        self.assertIn("prueba", result["unreachable"])
        self.assertEqual(self.yaml.load().nodes["prueba"].content[0].text, "Prueba")
        self.assertNotIn(session.session_id, self.engine.sessions)
        node = self.yaml.load().nodes["inicio"]
        node.options.append(Option(id="nueva", label="Nueva", next="prueba"))
        result = self.service.change(self.revision(), "inicio", node)
        self.assertNotIn("prueba", result["unreachable"])
        state = self.engine.start()
        self.assertEqual(self.engine.select(state.session_id,"nueva",0).node_id,"prueba")
        node.options[-1].label = "Editada"
        self.service.change(self.revision(),"inicio",node)
        self.assertEqual(self.yaml.load().nodes["inicio"].options[-1].label,"Editada")
        with self.assertRaises(ChatError):
            self.service.change(self.revision(),"prueba")
        node.options.pop()
        self.service.change(self.revision(),"inicio",node)
        self.service.change(self.revision(),"prueba")
        self.assertNotIn("prueba",self.yaml.load().nodes)

    def test_conflict_duplicate_initial_and_missing(self):
        old = self.revision()
        self.service.change(old,"prueba",self.node(),True)
        for args in [(old,"prueba",self.node()), (self.revision(),"prueba",self.node(),True),
                     (self.revision(),"inicio"), (self.revision(),"missing")]:
            with self.subTest(args=args), self.assertRaises(ChatError):
                self.service.change(*args)

    def test_invalid_reference_or_file_never_written(self):
        before = self.path.read_bytes()
        node = self.node()
        node.options.append(Option(id="bad",label="Bad",next="missing"))
        with self.assertRaises(ChatError):
            self.service.change(self.revision(),"prueba",node,True)
        node = Node.model_validate({"type":"information","content":[{"type":"document","label":"File","file":"documents/missing.pdf"}]})
        with self.assertRaises(ChatError):
            self.service.change(self.revision(),"prueba",node,True)
        self.assertEqual(before,self.path.read_bytes())

    def test_failed_atomic_replace_preserves_disk_and_engine(self):
        before = self.path.read_bytes()
        with patch("app.services.yaml_manager.os.replace",side_effect=OSError("disk error")):
            with self.assertRaises(ChatError):
                self.service.change(self.revision(),"prueba",self.node(),True)
        self.assertEqual(before,self.path.read_bytes())
        self.assertNotIn("prueba",self.engine.knowledge.nodes)
        self.assertEqual(list(self.path.parent.glob("*.tmp")),[])

    def test_atomic_branch_creation_and_navigation(self):
        revision = self.revision()
        tree = self.yaml.load()
        tree.nodes["rama"] = self.node()
        tree.nodes["hoja"] = self.node()
        tree.nodes["inicio"].options.append(Option(id="rama",label="Rama",next="rama"))
        tree.nodes["rama"].options.append(Option(id="hoja",label="Hoja",next="hoja"))
        result = self.service.replace_tree(revision,tree)
        self.assertNotIn("hoja",result["unreachable"])
        state = self.engine.start()
        state = self.engine.select(state.session_id,"rama",state.revision)
        state = self.engine.select(state.session_id,"hoja",state.revision)
        self.assertEqual(state.node_id,"hoja")
        self.assertIn("hoja",self.yaml.load().nodes)
        with self.assertRaises(ChatError):
            self.service.replace_tree(revision,tree)

    def test_whole_tree_invalid_destination_preserves_file(self):
        before = self.path.read_bytes()
        tree = self.yaml.load()
        del tree.nodes["titulacion"]
        with self.assertRaises(ChatError):
            self.service.replace_tree(self.revision(),tree)
        self.assertEqual(before,self.path.read_bytes())

    def test_whole_tree_failed_save_preserves_engine(self):
        tree = self.yaml.load()
        tree.nodes["rama"] = self.node()
        before = self.path.read_bytes()
        with patch("app.services.yaml_manager.os.replace",side_effect=OSError("disk error")):
            with self.assertRaises(ChatError):
                self.service.replace_tree(self.revision(),tree)
        self.assertEqual(before,self.path.read_bytes())
        self.assertNotIn("rama",self.engine.knowledge.nodes)


class AdminHttpTests(unittest.TestCase):
    setUpClass = classmethod(test_phase1.ApiTests.setUpClass.__func__)
    tearDownClass = classmethod(test_phase1.ApiTests.tearDownClass.__func__)

    def test_page_and_local_access_protection(self):
        with urlopen(self.base+"/admin") as response:
            self.assertIn('id="editor"',response.read().decode())
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base+"/api/admin/tree")
        self.assertEqual(error.exception.code,403)
        with urlopen(Request(self.base+"/api/admin/tree",headers={"X-Admin-Request":"local-panel"})) as response:
            self.assertIn("inicio",json.load(response)["knowledge"]["nodes"])
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base+"/api/admin/tree",headers={"X-Admin-Request":"local-panel","Origin":"https://example.com"}))
        self.assertEqual(error.exception.code,403)
