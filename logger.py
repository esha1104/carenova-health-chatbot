"""
Structured logging configuration.
All logs go to both console and file.
"""

import logging
import logging.handlers
from pathlib import Path
import json
from datetime import datetime
from config import LOG_LEVEL, DEBUG


class JSONFormatter(logging.Formatter):
    """Convert logs to JSON for easier parsing."""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with file and console output."""
    logger = logging.getLogger(name)
    
    # Skip if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(LOG_LEVEL)
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (JSON format for parsing)
    logs_path = Path("logs")
    logs_path.mkdir(exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        logs_path / "carenova.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger


# Main logger
logger = get_logger("carenova")

# Suppress noisy external loggers
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("chroma").setLevel(logging.WARNING)
