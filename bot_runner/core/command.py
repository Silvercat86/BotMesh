from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Command:
    name: str
    func_name: str
    scope: str = "any"
