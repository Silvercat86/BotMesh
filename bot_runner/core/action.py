from dataclasses import dataclass, field
from typing import Callable
from enum import Enum

class ActionType(str, Enum):
    COMMAND = "command"
    CALLBACK = "callback"
    OTHER = "other"
    CHAT_MEMBER_JOIN = "chat_member_join"
    CHAT_MEMBER_LEAVE = "chat_member_leave"

@dataclass
class Action:
    name: str
    func_name: str
    scope: str = "any"
    type: ActionType = ActionType.COMMAND
