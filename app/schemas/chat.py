from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    question: str = Field(..., description="User query")

class Citation(BaseModel):
    chunk_id: str
    source: str
    similarity: float

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
