from typing import Self


class BaseService:
    config_model = None
    name : str
    def __init__(self):
        pass
    @classmethod
    def from_config(cls, config: dict) -> Self:
        raise NotImplementedError()
