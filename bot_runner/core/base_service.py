from typing import Self


class BaseService:
    name : str
    def __init__(self):
        pass
    @classmethod
    def from_config(cls, config: dict) -> Self:
        raise NotImplementedError()
