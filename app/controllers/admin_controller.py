class AdminController:
    def __init__(self, service):
        self.service = service

    def tree(self):
        return self.service.snapshot()

    def save_tree(self, body):
        return self.service.replace_tree(body.revision, body.knowledge)

    def save_node(self, body, create=False):
        return self.service.change(body.revision, body.node_id, body.node, create)

    def delete_node(self, node_id, body):
        return self.service.change(body.revision, node_id)
