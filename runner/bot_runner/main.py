import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from core.bot_runner import BotRunner


load_dotenv()


async def main() -> None:
    logging.info("Starting BotMesh runner.")
    bot_runner = BotRunner(api_key=os.getenv("BOT_RUNNER_API_KEY", ""))
    await bot_runner.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")
