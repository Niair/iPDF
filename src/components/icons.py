# src/components/icons.py
import base64
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

def load_icon_base64(filename: str) -> str:
    p = ASSETS_DIR / "icons" / filename
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
