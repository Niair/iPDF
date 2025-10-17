"""Multimodal content models"""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ImageElement(BaseModel):
    """Image extracted from PDF"""
    image_id: str
    page_number: int
    image_data: str  # Base64 encoded
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class TableElement(BaseModel):
    """Table extracted from PDF"""
    table_id: str
    page_number: int
    table_data: str  # Markdown or HTML format
    rows: int = 0
    columns: int = 0
    metadata: Dict[str, Any] = {}


class FormulaElement(BaseModel):
    """Formula extracted from PDF"""
    formula_id: str
    page_number: int
    latex: str
    rendered_text: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MultimodalContent(BaseModel):
    """Collection of multimodal content"""
    text_chunks: list = []
    images: list = []
    tables: list = []
    formulas: list = []
