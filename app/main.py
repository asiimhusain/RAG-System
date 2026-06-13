from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Re-ranking RAG API",
    description="A production-ready Retrieval-Augmented Generation API with two-stage retrieval (Vector Search + Cross-Encoder Reranking).",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

# Mount static frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/chat")
def read_chat():
    return FileResponse(os.path.join(frontend_dir, "chat.html"))

@app.get("/documents")
def read_documents():
    return FileResponse(os.path.join(frontend_dir, "documents.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
