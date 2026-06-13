import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_file(self, file_path: str) -> List[Document]:
        """Loads a supported file type and splits it into chunks."""
        ext = Path(file_path).suffix.lower()
        documents = []
        
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return []
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages/sections from {file_path}")
            
            # Decorate metadata
            for doc in documents:
                doc.metadata["source_file"] = Path(file_path).name
                
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []
