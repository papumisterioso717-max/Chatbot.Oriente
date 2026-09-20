from hashlib import sha256
from threading import RLock

from pydantic import ValidationError

from app.models.knowledge import Knowledge
from app.services.chatbot_engine import ChatError
from app.services.file_manager import FileManager


class AdminService:
    def __init__(self, yaml_manager, engine, file_controller):
        self.yaml = yaml_manager
        self.engine = engine
        self.files = file_controller
        self.lock = RLock()

    def revision(self):
        return sha256(self.yaml.path.read_bytes()).hexdigest()

    def replace_tree(self, revision, knowledge):
        """Commit nodes and their connecting options together."""
        with self.lock, self.engine.lock:
            if revision != self.revision():
                raise ChatError("Hay cambios más recientes. Recarga antes de guardar.", 409)
            try:
                knowledge = Knowledge.model_validate(knowledge.model_dump(mode="json"))
                manager = FileManager(self.files.manager.root, knowledge)
                manager.validate()
            except ValueError as error:
                raise ChatError(str(error), 422) from error
            try:
                self.yaml.save(knowledge)
            except OSError as error:
                raise ChatError("No se pudo guardar el árbol. Tus cambios siguen en el panel.", 500) from error
            self.engine.knowledge = knowledge
            self.engine.sessions.clear()
            self.files.manager = manager
            return self.snapshot()

    def snapshot(self):
        with self.lock:
            knowledge = self.yaml.load()
            reachable, pending = set(), [knowledge.bot.start_node]
            while pending:
                node_id = pending.pop()
                if node_id in reachable:
                    continue
                reachable.add(node_id)
                pending.extend(option.next for option in knowledge.nodes[node_id].options if option.next)
            return {"revision": self.revision(), "knowledge": knowledge.model_dump(mode="json", exclude_none=True),
                    "unreachable": sorted(set(knowledge.nodes) - reachable)}

    def change(self, revision, node_id, node=None, create=False):
        with self.lock, self.engine.lock:
            if revision != self.revision():
                raise ChatError("Hay cambios más recientes. Recarga el panel antes de guardar.", 409)
            knowledge = self.yaml.load()
            if create and node_id in knowledge.nodes:
                raise ChatError("Ya existe un nodo con ese ID.", 409)
            if not create and node_id not in knowledge.nodes:
                raise ChatError("El nodo no existe.", 404)
            if node is None:
                if node_id == knowledge.bot.start_node:
                    raise ChatError("No se puede eliminar el nodo inicial.", 409)
                references = [f"{key}/{option.id}" for key, value in knowledge.nodes.items()
                              for option in value.options if option.next == node_id and key != node_id]
                if references:
                    raise ChatError("El nodo tiene referencias: " + ", ".join(references), 409)
                del knowledge.nodes[node_id]
            else:
                knowledge.nodes[node_id] = node
            try:
                knowledge = Knowledge.model_validate(knowledge.model_dump(mode="json"))
                manager = FileManager(self.files.manager.root, knowledge)
                manager.validate()
            except (ValueError, ValidationError) as error:
                raise ChatError(str(error), 422) from error
            try:
                self.yaml.save(knowledge)
            except OSError as error:
                raise ChatError("No se pudo guardar el YAML. Revisa los permisos del archivo.", 500) from error
            self.engine.knowledge = knowledge
            self.engine.sessions.clear()
            self.files.manager = manager
            return self.snapshot()
