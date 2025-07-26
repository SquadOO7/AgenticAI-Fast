from aiologger import Logger
from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter
import asyncio # Import asyncio for running async methods in synchronous context (if needed)


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

    def log_info(self, msg: str):
        # Get the current event loop, or create a new one if none exists
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError: # No running event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.info(msg))
            loop.close()
            asyncio.set_event_loop(None) # Clear the event loop for subsequent calls
            return

        # If a loop is running, schedule the async task
        loop.create_task(self.info(msg))


    def log_error(self, msg: str, exc: Exception = None):
        async def _log_error_async():
            if exc:
                await self.error(f"{msg}\nException: {exc}", exc_info=True)
            else:
                await self.error(msg)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_log_error_async())
            loop.close()
            asyncio.set_event_loop(None)
            return

        loop.create_task(_log_error_async())

    async def close(self):
        await self.shutdown()