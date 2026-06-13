import httpx
from functools import lru_cache
from typing import List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class JinaEmbeddings(Embeddings):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.jina.ai/v1/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.client = httpx.Client(headers=self.headers, timeout=10.0)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        batch_size = 32
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            data = {
                "model": self.model,
                "task": "retrieval.query",
                "normalized": True,
                "input": batch
            }
            res = self.client.post(self.url, json=data)
            res.raise_for_status()
            result = res.json()
            embeddings.extend([item["embedding"] for item in result["data"]])
            
        return embeddings

    @lru_cache(maxsize=1024)
    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

class VectorStoreManager:
    def __init__(self):
        logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL}")
        self.embeddings = JinaEmbeddings(
            api_key=settings.JINA_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
        
        import chromadb
        if settings.CHROMA_MODE == "local":
            logger.info("Using OFFLINE local ChromaDB as configured.")
            self.vector_store = Chroma(
                collection_name="rag_collection",
                embedding_function=self.embeddings,
                persist_directory=str(settings.DB_DIR)
            )
        else:
            try:
                logger.info("Attempting to connect to Chroma Cloud...")
                chroma_client = chromadb.CloudClient(
                    api_key=settings.CHROMA_API_KEY,
                    tenant=settings.CHROMA_TENANT,
                    database=settings.CHROMA_DATABASE
                )
                
                self.vector_store = Chroma(
                    client=chroma_client,
                    collection_name="rag_collection",
                    embedding_function=self.embeddings
                )
                
                # Quick check to ensure the cloud DB is actually responding
                self.vector_store._client.heartbeat()
                logger.info("Successfully connected to online Chroma Cloud.")
                
            except Exception as e:
                logger.warning(f"Online ChromaDB is not responding ({e}). Falling back to OFFLINE local ChromaDB.")
                self.vector_store = Chroma(
                    collection_name="rag_collection",
                    embedding_function=self.embeddings,
                    persist_directory=str(settings.DB_DIR)
                )

    def add_documents(self, documents: List[Document]):
        if not documents:
            return
        self.vector_store.add_documents(documents)
        logger.info(f"Added {len(documents)} documents to vector store.")

    def count(self) -> int:
        return self.vector_store._collection.count()

    def similarity_search_with_score(self, query: str, top_k: int) -> List[tuple[Document, float]]:
        # Using similarity search with score. Closer to 0 is better typically in cosine distance depending on db.
        # Chroma returns Distance.
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return results

    async def asimilarity_search_with_score(self, query: str, top_k: int) -> List[tuple[Document, float]]:
        results = await self.vector_store.asimilarity_search_with_score(query, k=top_k)
        return results
