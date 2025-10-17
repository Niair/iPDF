"""Chat models"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}


class ChatHistory(BaseModel):
    """Chat conversation history"""
    messages: List[ChatMessage] = []
    max_history: int = 10
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = None):
        """Add a message to history"""
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Keep only last N messages
        if len(self.messages) > self.max_history * 2:  # user + assistant pairs
            self.messages = self.messages[-self.max_history * 2:]
    
    def get_formatted_history(self) -> List[Dict[str, str]]:
        """Get history formatted for LLM"""
        return [{"role": msg.role.value, "content": msg.content} for msg in self.messages]


class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    document_ids: Optional[List[str]] = None
    model: str = "llama3.2"
    temperature: float = 0.1
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    processing_time: float = 0.0
