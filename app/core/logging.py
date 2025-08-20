import logging
import sys
from app.core.config import settings


JSON_FORMAT = (
    "{\"level\":\"%(levelname)s\",\"time\":\"%(asctime)s\",\"name\":\"%(name)s\","
    "\"message\":\"%(message)s\"}"
)


def setup_logging():
    # Idempotent setup
    if getattr(setup_logging, "_configured", False):
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(JSON_FORMAT)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    root.handlers = [handler]

    setup_logging._configured = True