from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.types import Message as TelegramMessage
from core.models import UniversalMessage


class TelegramAdapter:
    def __init__(self, bot):
        self.bot : Bot = bot

    async def send(self, chat_id, text, photo=None):
        if photo:
            file = FSInputFile(photo)
            await self.bot.send_photo(chat_id, photo=file, caption=text, parse_mode="HTML")
        else:
            await self.bot.send_message(chat_id, text, parse_mode="HTML")

    
    def convert_message(self, tg_message: TelegramMessage) -> UniversalMessage:
        """Конвертирует сообщение Telegram в универсальный формат"""
        return UniversalMessage(
            message_id=str(tg_message.message_id),
            chat_id=str(tg_message.chat.id),
            chat_type=tg_message.chat.type,
            text=tg_message.text or tg_message.caption or "",
            raw_text=tg_message.text or tg_message.caption or "",
            sender_id=str(tg_message.from_user.id),
            sender_name=tg_message.from_user.full_name,
            sender_username=tg_message.from_user.username,
            date=tg_message.date,
            has_media=bool(tg_message.photo or tg_message.video or tg_message.document),
            media_type=self._get_media_type(tg_message),
            media_data=self._get_media_data(tg_message),
            reply_to=self._convert_reply(tg_message.reply_to_message) if tg_message.reply_to_message else None,
            raw=tg_message,
            extra={
                "entities": tg_message.entities,
                "caption_entities": tg_message.caption_entities,
            }
        )