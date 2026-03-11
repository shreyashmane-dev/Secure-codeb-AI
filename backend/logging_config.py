from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)
        return

    existing_types = {type(handler) for handler in root.handlers}
    if RotatingFileHandler not in existing_types:
        root.addHandler(file_handler)
    if logging.StreamHandler not in existing_types:
        root.addHandler(console_handler)
