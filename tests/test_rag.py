import pytest
from app.api.schemas import QueryRequest

def test_query_schema():
    req = QueryRequest(query="What is RAG?")
    assert req.query == "What is RAG?"
    assert req.top_k is None
    assert req.top_n is None
