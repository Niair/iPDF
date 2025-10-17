"""Document models"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """Types of content extracted from PDF"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    FORMULA = "formula"


class DocumentMetadata(BaseModel):
    """Metadata for a document"""
    filename: str
    file_hash: str
    file_size: int
    upload_date: datetime = Field(default_factory=datetime.now)
    page_count: int = 0
    processing_status: str = "pending"


class ContentElement(BaseModel):
    """Individual content element extracted from PDF"""
    element_id: str
    content_type: ContentType
    content: str
    page_number: int
    metadata: Dict[str, Any] = {}


class ProcessingResult(BaseModel):
    """Result of PDF processing"""
    filename: str
    text: str
    elements: List[ContentElement] = []
    metadata: Dict[str, Any] = {}
    success: bool
    error: Optional[str] = None


class Document(BaseModel):
    """Complete document model"""
    id: str
    metadata: DocumentMetadata
    content_elements: List[ContentElement] = []
    embeddings_generated: bool = False
    indexed_in_vectorstore: bool = False
