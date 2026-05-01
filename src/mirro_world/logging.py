from datetime import datetime
from loguru import logger
from mirro_world.settings import settings

def setup_logging() -> None:
    logger.add(
        sink=settings.LOGS_PATH / f"{datetime.now():%Y%m%dT%H%M%S}.log",
        enqueue=True,
        backtrace=True,
        diagnose=False
    )
