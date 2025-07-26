from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter


class CustomLogger(Logger):
    def __init__(self):
        # Initialize the parent Logger
        super().__init__(name="kuberha_logger", level=LogLevel.INFO)

        # Create AsyncFileHandler
        file_handler = AsyncFileHandler(filename="kuberha.log", mode="a", encoding="utf-8")

        # Add formatter with date and time
        file_handler.formatter = Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add handler to this logger
        self.add_handler(file_handler)

    async def log_info(self, msg: str):
        await self.info(msg)

    async def log_error(self, msg: str, exc: Exception = None):
        if exc:
            await self.error(f"{msg}\nException: {exc}", exc_info=True)
        else:
            await self.error(msg)

    async def close(self):
        await self.shutdown()
