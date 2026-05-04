# core/models.py
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime

@dataclass
class UniversalMessage:
    """Универсальное сообщение для всех платформ"""
    message_id: str
    chat_id: str
    chat_type: str  # "private", "group", "channel"
    text: str
    raw_text: str
    sender_id: str
    sender_name: str
    date: datetime
    
    sender_username: Optional[str] = None
    has_media: bool = False
    media_type: Optional[str] = None
    media_data: Optional[Any] = None
    reply_to: Optional['UniversalMessage'] = None
    raw: Any = None
    extra: dict = field(default_factory=dict)