from pathlib import Path
from aiogram.types import Message
from aiogram.filters import Command
import random

from core.base_plugin import BaseTelegramPlugin

class MemePlugin(BaseTelegramPlugin):
    def setup(self):
        memes_file = Path("data/memes/memes.txt")
        memes_file.parent.mkdir(parents=True, exist_ok=True)

        @self.router.message(Command("meme"))
        async def meme_command(message: Message):
            if message.chat.type != "private":
                await message.delete()
                return

            if not memes_file.exists():
                await message.answer("Мемов нет")
                return

            memes = [
                line.strip()
                for line in memes_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            if not memes:
                await message.answer("Мемов нет")
                return

            await message.answer_photo(
                photo=random.choice(memes)#,
                # caption="Лови мем"
            )

        
        # @self.router.message()
        # async def catch_meme(message: Message):
            

        #     if not message.photo:
        #         return

        #     file_id = message.photo[-1].file_id

        #     existing = set()
        #     if memes_file.exists():
        #         existing = set(
        #             line.strip()
        #             for line in memes_file.read_text(encoding="utf-8").splitlines()
        #         )

        #     if file_id in existing:
        #         await message.answer("⚠️ Уже есть")
        #         return

        #     with memes_file.open("a", encoding="utf-8") as f:
        #         f.write(file_id + "\n")

        #     print(f"[MEME SAVED] {file_id}")

        #     await message.answer(
        #         f"✅ Мем сохранён\n`{file_id}`"
        #     )