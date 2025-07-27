from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter


class CustomLogger(Logger):
    def __init__(self):
        # Initialize the parent Logger with a specific name and level
        super().__init__(name="kuberha_logger", level=LogLevel.INFO)

        # Create an AsyncFileHandler for logging to 'kuberha.log'
        file_handler = AsyncFileHandler(filename="kuberha.log", mode="a", encoding="utf-8")

        # Define the formatter for log messages, including timestamp, level, name, and message
        file_handler.formatter = Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add the file handler to this logger instance
        self.add_handler(file_handler)

    # --- Asynchronous Logging Methods (Recommended for async contexts) ---

    async def alog_info(self, msg: str):
        await self.info(msg)

    async def alog_error(self, msg: str, exc: Exception = None):
        if exc:
            # When exc_info=True, the traceback will be included in the log
            await self.error(f"{msg}\nException: {exc}", exc_info=True)
        else:
            await self.error(msg)

    async def close(self):
        await self.shutdown()