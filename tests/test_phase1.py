import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from copy import deepcopy
import yaml
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.services.chatbot_engine import ChatbotEngine, ChatError
from app.services.yaml_manager import YamlManager

ROOT = Path(__file__).resolve().parent.parent


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.knowledge = YamlManager(ROOT / "data/knowledge.yaml").load()
        self.engine = ChatbotEngine(self.knowledge)

    def choose(self, state, option):
        return self.engine.select(state.session_id, option, state.revision)

    def test_navigation_back_restart(self):
        state = self.engine.start()
        for option in ("titulacion", "modalidades", "tesis"):
            state = self.choose(state, option)
        self.assertEqual(state.node_id, "tesis")
        self.assertEqual(state.history, ["inicio", "titulacion", "modalidades"])
        state = self.choose(state, "volver")
        self.assertEqual(state.node_id, "modalidades")
        state = self.choose(state, "inicio")
        self.assertEqual((state.node_id, state.history), ("inicio", []))

    def test_shared_node_back_uses_actual_path(self):
        first = self.choose(self.engine.start(), "contacto")
        second = self.choose(self.choose(self.engine.start(), "titulacion"), "contacto")
        self.assertEqual(self.choose(first, "volver").node_id, "inicio")
        self.assertEqual(self.choose(second, "volver").node_id, "titulacion")

    def test_back_at_start_and_independent_sessions(self):
        first, second = self.engine.start(), self.engine.start()
        self.assertNotEqual(first.session_id, second.session_id)
        self.choose(first, "titulacion")
        self.assertEqual(self.choose(second, "volver").node_id, "inicio")

    def test_invalid_option_does_not_mutate_state(self):
        state = self.engine.start()
        with self.assertRaises(ChatError):
            self.choose(state, "tesis")
        self.assertEqual(self.choose(state, "contacto").node_id, "contacto")

    def test_stale_selection_and_unknown_session(self):
        state = self.engine.start()
        self.choose(state, "contacto")
        with self.assertRaises(ChatError) as error:
            self.choose(state, "contacto")
        self.assertEqual(error.exception.status_code, 409)
        with self.assertRaises(ChatError):
            self.engine.select("missing", "contacto", 0)

    def test_expiration_and_capacity(self):
        engine = ChatbotEngine(self.knowledge, max_sessions=1)
        state = engine.start()
        with self.assertRaises(ChatError):
            engine.start()
        engine.sessions[state.session_id].touched -= 3601
        with self.assertRaises(ChatError):
            engine.select(state.session_id, "contacto", 0)
        self.assertEqual(engine.start().node_id, "inicio")

    def test_cycles_supported_without_recursive_navigation(self):
        knowledge = self.knowledge.model_copy(deep=True)
        knowledge.nodes["inicio"].options[0].next = "inicio"
        engine = ChatbotEngine(knowledge)
        state = engine.start()
        state = engine.select(state.session_id, "titulacion", state.revision)
        self.assertEqual(state.history, ["inicio"])
        state = engine.select(state.session_id, "volver", state.revision)
        self.assertEqual(state.history, [])

    def test_yaml_errors(self):
        original = self.knowledge.model_dump(mode="json", exclude_none=True)
        variants = []
        def altered(change):
            data = deepcopy(original)
            change(data)
            variants.append(yaml.safe_dump(data))
        altered(lambda data: data["bot"].update(start_node="inexistente"))
        altered(lambda data: data["nodes"]["inicio"]["options"][0].update(next="inexistente"))
        altered(lambda data: data["nodes"]["inicio"]["options"][0].update(action="unknown"))
        altered(lambda data: data["nodes"]["inicio"]["options"][0].update(action="back"))
        altered(lambda data: data["nodes"]["inicio"]["options"][0].pop("next"))
        altered(lambda data: data["nodes"]["inicio"]["options"][1].update(id="titulacion"))
        altered(lambda data: data["nodes"]["inicio"]["content"][0].update(type="unknown"))
        variants.extend([yaml.safe_dump(original) + "\nversion: 1\n",
                         "!!python/object/apply:os.system ['echo forbidden']"])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.yaml"
            for content in variants:
                with self.subTest(content=content[:80]):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        YamlManager(path).load()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Choose an available local port for the short-lived test server.
        cls.server_socket = socket.socket()
        cls.server_socket.bind(("127.0.0.1", 0))
        port = cls.server_socket.getsockname()[1]
        cls.server_socket.close()
        cls.base = f"http://127.0.0.1:{port}"
        cls.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            try:
                with urlopen(cls.base + "/openapi.json", timeout=1):
                    return
            except OSError:
                if cls.process.poll() is not None:
                    break
                time.sleep(0.1)
        cls.process.terminate()
        cls.process.wait(timeout=5)
        raise RuntimeError("No inició la API de prueba.")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)

    def request_json(self, path, body=None):
        request = Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_chat_page_and_assets(self):
        for path, expected_type, fragment in [
            ("/", "text/html", 'id="options"'),
            ("/static/chat.js", "javascript", "/api/chat/select"),
            ("/static/chat.css", "text/css", "@media"),
        ]:
            with self.subTest(path=path), urlopen(self.base + path, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(expected_type, response.headers["Content-Type"])
                self.assertIn(fragment, response.read().decode("utf-8"))

    def test_api_navigation_and_errors(self):
        code, state = self.request_json("/api/chat/start")
        self.assertEqual(code, 200)
        for option, expected in [("titulacion", "titulacion"), ("modalidades", "modalidades"),
                                 ("tesis", "tesis"), ("volver", "modalidades"), ("inicio", "inicio")]:
            code, state = self.request_json("/api/chat/select", {
                "session_id": state["session_id"], "option_id": option, "revision": state["revision"]})
            self.assertEqual(code, 200)
            self.assertEqual(state["node_id"], expected)
        self.assertEqual(state["history"], [])
        self.assertEqual(self.request_json("/api/chat/node/missing")[0], 404)
        self.assertEqual(self.request_json("/api/chat/node/tesis")[0], 200)
        self.assertEqual(self.request_json("/api/chat/select", {})[0], 422)
        self.assertEqual(self.request_json("/api/chat/select", {
            "session_id": state["session_id"], "option_id": "missing", "revision": state["revision"]})[0], 400)
        self.assertEqual(self.request_json("/api/chat/select", {
            "session_id": state["session_id"], "option_id": "contacto", "revision": 0})[0], 409)


if __name__ == "__main__":
    unittest.main()
