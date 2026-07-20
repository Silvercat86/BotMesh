import maxapi
from maxapi.enums.format import Format
from core.models import UniversalMessage
from datetime import datetime
from maxapi.types import Message as MaxMessage,MessageCreated
class MaxAdapter:
    def __init__(self, bot):
        self.bot : maxapi.Bot = bot

    async def send(self, chat_id, text, photo=None):
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            attachments=[maxapi.types.InputMedia(photo)] if photo else None,
            parse_mode=Format.HTML,
        )
    def convert_message(self, max_message: MessageCreated) -> UniversalMessage:
        """Конвертирует сообщение Max в универсальный формат"""
        # Max хранит текст в body.text
        # text = getattr(max_message.body, 'text', '') if max_message.body else ''
        text = max_message.message.body.text

        message = max_message.message
        chat = max_message.chat
        user = max_message.from_user
        
        return UniversalMessage(
            message_id=str(message.url),
            chat_id=str(chat.chat_id),
            chat_type="private" if chat.type == "dialog" else "group" if chat.type == "chat" else "channel" if chat.type == "channel" else "unknown",
            text=text,
            raw_text=text,
            sender_id=str(user.user_id or user.chat_id),
            sender_name = user.full_name,
            sender_username=getattr(max_message, 'sender_username', None),
            date=datetime.now(),
            has_media=bool(getattr(max_message, 'media', None)),
            media_type=None,
            media_data=getattr(max_message, 'media', None),
            raw=max_message,
            extra={
                "body": message.body,
                "platform": "max"
            }
        )