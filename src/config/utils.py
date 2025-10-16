# src/config/utils.py
import os
import sys
from pathlib import Path
from typing import Any
import dill
import pickle
import hashlib
from src.config.exception import CustomException
from src.config.logger import logger

def save_object(file_path: str, obj: Any) -> None:
    try:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            dill.dump(obj, f)
        logger.info(f"Saved object to {p}")
    except Exception as e:
        logger.exception("save_object failed")
        raise CustomException(e, sys)

def load_object(file_path: str) -> Any:
    try:
        p = Path(file_path)
        with open(p, "rb") as f:
            try:
                return pickle.load(f)
            except Exception:
                f.seek(0)
                return dill.load(f)
    except Exception as e:
        logger.exception("load_object failed")
        raise CustomException(e, sys)

def hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
