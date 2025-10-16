# src/config/logger.py
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

LOGS_DIR = Path(os.getcwd()) / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_log_file_path(prefix: str = "ipdf") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.log"
    return LOGS_DIR / filename

def get_logger(name: str = __name__, level: int = logging.INFO, file_prefix: Optional[str] = "ipdf") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s")
    file_path = get_log_file_path(file_prefix)
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False
    return logger

logger = get_logger(__name__)
