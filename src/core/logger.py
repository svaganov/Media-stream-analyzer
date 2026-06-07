"""Logging setup"""
import logging
import sys
from .config import config

def setup_logging():
    """Configure application logging"""
    level = getattr(logging, config.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    return logging.getLogger("media-stream-analyzer")

logger = setup_logging()
