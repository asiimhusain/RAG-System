from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    top_n: Optional[int] = None
    session_id: Optional[str] = None

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[DocumentChunk]
    session_id: str

class StatusResponse(BaseModel):
    status: str
    document_count: int

class ChatSession(BaseModel):
    id: str
    title: str
    created_at: str

class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    sources: List[DocumentChunk]
    created_at: str

class RenameSessionRequest(BaseModel):
    title: str
