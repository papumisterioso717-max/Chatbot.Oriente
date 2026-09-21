import unittest
from pathlib import Path
from app.services.yaml_manager import YamlManager
from app.services.chatbot_engine import ChatbotEngine, ChatError

class BackTests(unittest.TestCase):
    def test_repeated_back_and_stale_request(self):
        engine = ChatbotEngine(YamlManager(Path('data/knowledge.yaml')).load())
        state = engine.start()
        root = state.node_id
        for _ in range(2):
            option = next(o for o in state.node.options if o.next)
            state = engine.select(state.session_id, option.id, state.revision)
        revision = state.revision
        state = engine.back(state.session_id, revision)
        self.assertEqual(len(state.history), 1)
        with self.assertRaises(ChatError) as error:
            engine.back(state.session_id, revision)
        self.assertEqual(error.exception.status_code, 409)
        state = engine.back(state.session_id, state.revision)
        self.assertEqual(state.node_id, root)
        self.assertEqual(state.history, [])
        self.assertEqual(engine.back(state.session_id, state.revision).node_id, root)
        with self.assertRaises(ChatError) as error:
            engine.back('missing', 0)
        self.assertEqual(error.exception.status_code, 404)

if __name__ == '__main__':
    unittest.main()
