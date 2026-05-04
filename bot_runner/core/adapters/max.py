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

        chat = max_message.chat
        user = max_message.from_user
        
        return UniversalMessage(
            message_id=str(max_message.message.url),
            chat_id=str(max_message.chat.chat_id),
            chat_type=str(max_message.chat.type),
            text=text,
            raw_text=text,
            sender_id=str(max_message.from_user.user_id or max_message.from_user.chat_id),
            sender_name = max_message.from_user.full_name,
            sender_username=getattr(max_message, 'sender_username', None),
            date=datetime.fromtimestamp(max_message.timestamp) if hasattr(max_message, 'timestamp') else datetime.now(),
            has_media=bool(getattr(max_message, 'media', None)),
            media_type=self._get_media_type(max_message),
            media_data=getattr(max_message, 'media', None),
            raw=max_message,
            extra={
                "body": max_message.body,
                "platform": "max"
            }
        )