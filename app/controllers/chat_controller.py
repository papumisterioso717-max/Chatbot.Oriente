from app.models.conversation import Selection
from app.services.chatbot_engine import ChatbotEngine


class ChatController:
    def __init__(self, engine: ChatbotEngine):
        self.engine = engine

    def start(self):
        return self.engine.start()

    def select(self, selection: Selection):
        return self.engine.select(selection.session_id, selection.option_id, selection.revision)

    def node(self, node_id: str):
        return self.engine.get_node(node_id)

    def back(self, navigation):
        return self.engine.back(navigation.session_id, navigation.revision)
