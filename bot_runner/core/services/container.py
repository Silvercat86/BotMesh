class ServiceNotFoundError(RuntimeError):
    pass


class ServiceContainer:
    def __init__(self):
        self._services: dict[str, object] = {}

    def register(self, name: str, service: object):
        if name in self._services:
            raise RuntimeError(f"Service '{name}' already registered")
        self._services[name] = service

    def get(self, name: str):
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' not found")
        return self._services[name]

    def ensure(self, names: tuple[str, ...]):
        for name in names:
            if name not in self._services:
                raise ServiceNotFoundError(
                    f"Required service '{name}' is not registered"
                )