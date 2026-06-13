from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """
You are a reliable AI assistant. Your task is to answer the user's question. Use the provided context below if it is helpful.

Context:
{context}

Please provide a clear and concise answer. Do NOT cite any sources, source files, or document names in your response.
Do NOT start your response with phrases like "Based on the provided context," or "According to the context,". Answer the question directly and naturally.
"""

class AnswerGenerator:
    def __init__(self):
        logger.info(f"Initializing LLM: {settings.GENERATION_MODEL} at {settings.OPENAI_BASE_URL}")
        self.llm = ChatOpenAI(
            model=settings.GENERATION_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=0.0
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate(self, query: str, context_docs: List[dict], history: Optional[List[dict]] = None) -> str:
        # Format context
        context_texts = []
        for i, doc in enumerate(context_docs):
            source = doc.get("metadata", {}).get("source_file", "Unknown")
            context_texts.append(f"--- Document {i+1} (Source: {source}) ---\n{doc['content']}\n")
        
        context_str = "\n".join(context_texts)
        
        logger.info("Sending query to LLM...")
        try:
            # Build messages list dynamically with history
            messages = [("system", SYSTEM_PROMPT.format(context=context_str))]
            if history:
                for msg in history:
                    role = "human" if msg["role"] == "user" else "ai"
                    messages.append((role, msg["content"]))
            messages.append(("human", query))

            chain = self.llm | StrOutputParser()
            answer = chain.invoke(messages)
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "An error occurred while generating the answer. Please try again later."

    async def generate_async(self, query: str, context_docs: List[dict], history: Optional[List[dict]] = None) -> str:
        context_texts = []
        for i, doc in enumerate(context_docs):
            source = doc.get("metadata", {}).get("source_file", "Unknown")
            context_texts.append(f"--- Document {i+1} (Source: {source}) ---\n{doc['content']}\n")
        
        context_str = "\n".join(context_texts)
        
        logger.info("Sending query to LLM (async)...")
        try:
            messages = [("system", SYSTEM_PROMPT.format(context=context_str))]
            if history:
                for msg in history:
                    role = "human" if msg["role"] == "user" else "ai"
                    messages.append((role, msg["content"]))
            messages.append(("human", query))

            chain = self.llm | StrOutputParser()
            answer = await chain.ainvoke(messages)
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "An error occurred while generating the answer. Please try again later."

    async def generate_stream(self, query: str, context_docs: List[dict], history: Optional[List[dict]] = None):
        context_texts = []
        for i, doc in enumerate(context_docs):
            source = doc.get("metadata", {}).get("source_file", "Unknown")
            context_texts.append(f"--- Document {i+1} (Source: {source}) ---\n{doc['content']}\n")
        
        context_str = "\n".join(context_texts)
        
        logger.info("Streaming query to LLM...")
        try:
            messages = [("system", SYSTEM_PROMPT.format(context=context_str))]
            if history:
                for msg in history:
                    role = "human" if msg["role"] == "user" else "ai"
                    messages.append((role, msg["content"]))
            messages.append(("human", query))

            chain = self.llm | StrOutputParser()
            async for chunk in chain.astream(messages):
                yield chunk
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield "\nAn error occurred while generating the answer. Please try again later."
