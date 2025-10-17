"""Qdrant-specific schemas"""
from typing import Dict, Any, List
from pydantic import BaseModel


class QdrantPayload(BaseModel):
    """Payload stored with each vector in Qdrant"""
    document_id: str
    filename: str
    page_number: int
    content_type: str  # text, table, image, formula
    content: str
    metadata: Dict[str, Any] = {}


class QdrantPoint(BaseModel):
    """Complete Qdrant point (vector + payload)"""
    id: str
    vector: List[float]
    payload: Dict[str, Any]
