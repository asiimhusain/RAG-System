import os
import shutil
import uuid
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
from app.config import settings
from app.core.document_processor import DocumentProcessor
from app.core.vector_store import VectorStoreManager
from app.core.retriever import RetrieverReranker
from app.core.generator import AnswerGenerator
from app.core.chat_history import ChatHistoryManager
from app.api.schemas import (
    QueryRequest, QueryResponse, StatusResponse, DocumentChunk, 
    ChatSession, ChatMessage, RenameSessionRequest
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Lazy load helper functions for Core System components
_doc_processor = None
_vector_store = None
_retriever = None
_generator = None

def get_doc_processor():
    global _doc_processor
    if _doc_processor is None:
        _doc_processor = DocumentProcessor()
    return _doc_processor

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = RetrieverReranker(get_vector_store())
    return _retriever

def get_generator():
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator

_chat_history = None

def get_chat_history():
    global _chat_history
    if _chat_history is None:
        _chat_history = ChatHistoryManager()
    return _chat_history


def process_file_background(file_path: str):
    logger.info(f"Background processing of {file_path} started.")
    chunks = get_doc_processor().process_file(file_path)
    if chunks:
        get_vector_store().add_documents(chunks)
        os.remove(file_path) # Clean up
        logger.info(f"Completed and cleaned up {file_path}")
    else:
        logger.error(f"Failed to extract chunks from {file_path}")

@router.post("/upload")
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Uploads a document and indexes it in the background."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_path = settings.UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"File save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Process in background to keep endpoint responsive
    background_tasks.add_task(process_file_background, str(file_path))
    
    return {"message": "File uploaded successfully and submitted for indexing.", "filename": file.filename}

@router.post("/query", response_model=QueryResponse)
async def query_system(req: QueryRequest):
    """Executes the full RAG pipeline: retrieval -> reranking -> LLM generation with history."""
    logger.info(f"Query received: {req.query}")
    
    # Check or generate session_id
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        # First message query sets the session title
        title = req.query[:40] + ("..." if len(req.query) > 40 else "")
        get_chat_history().create_session(session_id, title)
    else:
        # Just in case session is provided but not initialized
        get_chat_history().create_session(session_id, "New Chat")
        
    # Get previous conversation messages for context
    history = get_chat_history().get_messages(session_id)
    
    # Retrieve documents using RAG pipeline
    top_docs = await get_retriever().async_retrieve_and_rerank(req.query, top_k=req.top_k, top_n=req.top_n)
    
    # Generate response incorporating recent history
    answer = await get_generator().generate_async(req.query, top_docs, history)
    
    sources = [DocumentChunk(**doc) for doc in top_docs]
    
    # Save user message and assistant answer to SQLite
    get_chat_history().add_message(session_id, "user", req.query)
    # Serialize sources as dictionary list to store in database
    sources_dict = [doc for doc in top_docs]
    get_chat_history().add_message(session_id, "assistant", answer, sources_dict)
    
    return QueryResponse(
        query=req.query,
        answer=answer,
        sources=sources,
        session_id=session_id
    )

@router.post("/query/stream")
async def query_system_stream(req: QueryRequest):
    """Streams the RAG pipeline response using Server-Sent Events (SSE)."""
    logger.info(f"Stream query received: {req.query}")
    
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        title = req.query[:40] + ("..." if len(req.query) > 40 else "")
        get_chat_history().create_session(session_id, title)
    else:
        get_chat_history().create_session(session_id, "New Chat")
        
    history = get_chat_history().get_messages(session_id)
    
    top_docs = await get_retriever().async_retrieve_and_rerank(req.query, top_k=req.top_k, top_n=req.top_n)
    sources = [DocumentChunk(**doc) for doc in top_docs]
    sources_dict = [doc for doc in top_docs]
    
    async def event_generator():
        yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'sources': [s.model_dump() for s in sources]})}\n\n"
        
        full_answer = ""
        async for chunk in get_generator().generate_stream(req.query, top_docs, history):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        
        get_chat_history().add_message(session_id, "user", req.query)
        get_chat_history().add_message(session_id, "assistant", full_answer, sources_dict)
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/status", response_model=StatusResponse)
def system_status():
    """Returns vector store document chunk count."""
    return StatusResponse(
        status="running",
        document_count=get_vector_store().count()
    )

@router.get("/sessions", response_model=List[ChatSession])
def get_sessions():
    """Fetches all chat sessions."""
    sessions = get_chat_history().get_sessions()
    return [
        ChatSession(
            id=s["id"],
            title=s["title"],
            created_at=str(s["created_at"])
        ) for s in sessions
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
def get_session_messages(session_id: str):
    """Fetches all messages for a specific session."""
    messages = get_chat_history().get_messages(session_id)
    formatted = []
    for m in messages:
        sources = []
        if m.get("sources"):
            for s in m["sources"]:
                # Ensure structure matches DocumentChunk
                sources.append(DocumentChunk(
                    content=s.get("content", ""),
                    metadata=s.get("metadata", {}),
                    score=s.get("score")
                ))
        formatted.append(ChatMessage(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            sources=sources,
            created_at=str(m["created_at"])
        ))
    return formatted

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Deletes a chat session."""
    get_chat_history().delete_session(session_id)
    return {"message": f"Session {session_id} deleted successfully."}

@router.put("/sessions/{session_id}")
def rename_session(session_id: str, req: RenameSessionRequest):
    """Renames a chat session."""
    get_chat_history().rename_session(session_id, req.title)
    return {"message": f"Session renamed to {req.title}."}
