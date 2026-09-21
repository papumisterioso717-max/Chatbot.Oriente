from dataclasses import dataclass, field
from threading import RLock
from time import monotonic
from uuid import uuid4

from app.models.conversation import ConversationState
from app.models.knowledge import Knowledge
from app.models.node import Node


class ChatError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class Session:
    current: str
    history: list[str] = field(default_factory=list)
    revision: int = 0
    touched: float = field(default_factory=monotonic)


class ChatbotEngine:
    """Content-independent navigation; sessions belong to one local process."""

    def __init__(self, knowledge: Knowledge, ttl: float = 3600, max_sessions: int = 1000):
        self.knowledge = knowledge
        self.ttl = ttl
        self.max_sessions = max_sessions
        self.sessions: dict[str, Session] = {}
        self.lock = RLock()

    def get_node(self, node_id: str) -> Node:
        if node_id not in self.knowledge.nodes:
            raise ChatError("El nodo no existe.", 404)
        return self.knowledge.nodes[node_id].model_copy(deep=True)

    def _state(self, session_id: str, session: Session) -> ConversationState:
        return ConversationState(
            session_id=session_id, bot_name=self.knowledge.bot.name,
            node_id=session.current, node=self.get_node(session.current),
            history=list(session.history), revision=session.revision,
        )

    def _expire(self):
        now = monotonic()
        for session_id in list(self.sessions):
            if now - self.sessions[session_id].touched >= self.ttl:
                del self.sessions[session_id]

    def start(self) -> ConversationState:
        with self.lock:
            self._expire()
            if len(self.sessions) >= self.max_sessions:
                raise ChatError("Se alcanzó el límite de sesiones. Intenta más tarde.", 503)
            session_id = str(uuid4())
            session = Session(current=self.knowledge.bot.start_node)
            self.sessions[session_id] = session
            return self._state(session_id, session)

    def back(self, session_id: str, revision: int) -> ConversationState:
        with self.lock:
            self._expire()
            session = self.sessions.get(session_id)
            if session is None:
                raise ChatError("Sesión inexistente o caducada. Inicia una conversación.", 404)
            if revision != session.revision:
                raise ChatError("Selección desactualizada. Usa el último estado recibido.", 409)
            if session.history:
                session.current = session.history.pop()
            session.revision += 1
            session.touched = monotonic()
            return self._state(session_id, session)

    def select(self, session_id: str, option_id: str, revision: int) -> ConversationState:
        with self.lock:
            self._expire()
            session = self.sessions.get(session_id)
            if session is None:
                raise ChatError("Sesión inexistente o caducada. Inicia una conversación.", 404)
            if revision != session.revision:
                raise ChatError("Selección desactualizada. Usa el último estado recibido.", 409)
            option = next((item for item in self.get_node(session.current).options
                           if item.id == option_id), None)
            if option is None:
                raise ChatError("La opción no pertenece al nodo actual.")
            if option.next is not None:
                if len(session.history) >= 1000:
                    raise ChatError("Historial lleno. Vuelve atrás o reinicia.", 409)
                session.history.append(session.current)
                session.current = option.next
            elif option.action == "back":
                if session.history:
                    session.current = session.history.pop()
            elif option.action == "restart":
                session.current = self.knowledge.bot.start_node
                session.history.clear()
            session.revision += 1
            session.touched = monotonic()
            return self._state(session_id, session)
