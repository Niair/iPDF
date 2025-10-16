# src/config/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root

class _Settings:
    def __init__(self):
        load_dotenv(ROOT / ".env")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        self.DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.FAISS_INDEX_DIR = os.getenv("FAISS_INDEX_DIR", str(ROOT / "faiss_index"))
        self.USE_GPU = os.getenv("USE_GPU", "false").lower() in ("1", "true", "yes")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = _Settings()

def init_environment():
    # set tesseract path if present
    os.environ["TESSERACT_CMD"] = settings.TESSERACT_PATH
