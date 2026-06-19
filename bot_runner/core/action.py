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


def get_action_type_from_string(type_str: str | ActionType | None) -> ActionType:
    if isinstance(type_str, ActionType):
        return type_str

    if not isinstance(type_str, str):
        return ActionType.OTHER

    type_str = type_str.strip()

    if type_str.upper() in ActionType.__members__:
        return ActionType[type_str.upper()]

    try:
        return ActionType(type_str.lower())
    except ValueError:
        return ActionType.OTHER