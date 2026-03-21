from .container import ServiceContainer

class Services:
    def __init__(self, container: ServiceContainer):
        self._c = container

    @property
    def scheduler(self):
        return self._c.get("scheduler")

    @property
    def people(self):
        return self._c.get("people")

    @property
    def users(self):
        return self._c.get("users")

    @property
    def chats(self):
        return self._c.get("chats")

    @property
    def templates(self):
        return self._c.get("templates")

    @property
    def images(self):
        return self._c.get("images")

    @property
    def state(self):
        return self._c.get("event_state")