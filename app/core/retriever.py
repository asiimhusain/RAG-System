import httpx
from typing import List
from langchain_core.documents import Document
from app.core.vector_store import VectorStoreManager
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RetrieverReranker:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        logger.info(f"Initializing reranker model: {settings.RERANKER_MODEL}")
        self.reranker_url = "https://api.jina.ai/v1/rerank"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.JINA_API_KEY}"
        }
        self.client = httpx.Client(headers=self.headers, timeout=15.0)
        self.async_client = httpx.AsyncClient(headers=self.headers, timeout=15.0)

    def retrieve_and_rerank(self, query: str, top_k: int = None, top_n: int = None) -> List[dict]:
        k = top_k or settings.RETRIEVAL_TOP_K
        n = top_n or settings.RERANK_TOP_N

        # Stage 1: Vector Search
        logger.info(f"Retrieving top {k} candidates via vector search for: '{query}'")
        retrieved_docs_with_scores = self.vector_store.similarity_search_with_score(query, top_k=k)
        
        if not retrieved_docs_with_scores:
            return []

        doc_objects = [doc for doc, _ in retrieved_docs_with_scores]
        doc_texts = [doc.page_content for doc in doc_objects]

        # Stage 2: Reranking
        logger.info("Computing cross-encoder scores via Jina API...")
        data = {
            "model": settings.RERANKER_MODEL,
            "query": query,
            "top_n": n,
            "documents": doc_texts,
            "return_documents": False
        }
        
        response = self.client.post(self.reranker_url, json=data)
        response.raise_for_status()
        
        reranked_results = response.json().get("results", [])

        # Combine docs with new scores
        final_docs = []
        for result in reranked_results:
            original_idx = result["index"]
            doc = doc_objects[original_idx]
            final_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(result["relevance_score"])
            })

        logger.info(f"Reranking complete. Selected top {len(final_docs)} chunks.")
        
        return final_docs

    async def async_retrieve_and_rerank(self, query: str, top_k: int = None, top_n: int = None) -> List[dict]:
        k = top_k or settings.RETRIEVAL_TOP_K
        n = top_n or settings.RERANK_TOP_N

        # Stage 1: Vector Search
        logger.info(f"Retrieving top {k} candidates via async vector search for: '{query}'")
        retrieved_docs_with_scores = await self.vector_store.asimilarity_search_with_score(query, top_k=k)
        
        if not retrieved_docs_with_scores:
            return []

        doc_objects = [doc for doc, _ in retrieved_docs_with_scores]
        doc_texts = [doc.page_content for doc in doc_objects]

        # Stage 2: Reranking
        logger.info("Computing async cross-encoder scores via Jina API...")
        data = {
            "model": settings.RERANKER_MODEL,
            "query": query,
            "top_n": n,
            "documents": doc_texts,
            "return_documents": False
        }
        
        response = await self.async_client.post(self.reranker_url, json=data)
        response.raise_for_status()
        
        reranked_results = response.json().get("results", [])

        # Combine docs with new scores
        final_docs = []
        for result in reranked_results:
            original_idx = result["index"]
            doc = doc_objects[original_idx]
            final_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(result["relevance_score"])
            })

        logger.info(f"Async Reranking complete. Selected top {len(final_docs)} chunks.")
        
        return final_docs
