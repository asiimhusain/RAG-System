# Contextual RAG System

A production-grade Retrieval-Augmented Generation (RAG) system featuring dual-stage retrieval (Dense Vector Search + Cross-Encoder Reranking), persistent chat history management, and a clean, responsive web interface.

---
* Live Link - *  https://ragsystem.grayground-1f565d06.centralindia.azurecontainerapps.io
---

## 🚀 Key Features

- **Dual-Stage Retrieval**:
  - **Stage 1 (Vector Search)**: Queries dense embedding vectors using the **Jina v5-small** model and **ChromaDB Cloud** (with automated local offline ChromaDB file fallbacks).
  - **Stage 2 (Reranking)**: Refines candidates using the **Jina Multilingual Reranker** to prevent context loss and maximize factual synthesis.
- **Fast Generation**: Orchestrates system prompts utilizing **Claude 4.7** via LangChain LCEL pipelines.
- **Persistent Chat History**:
  - Automatically stores chat sessions, message histories, and source document citations inside a local **SQLite** database (`data/db/chats.db`).
  - Optimized with Write-Ahead Logging (`WAL` mode) and `synchronous=NORMAL` configuration for fast, lock-free concurrent database accesses.
- **Responsive Web UI**:
  - Clean, borderless ChatGPT-style layout with a collapsible left sidebar to switch, rename, or delete chat sessions.
  - Native dark mode support, microphone speech-to-text input, and custom icons.
- **High-Performance Architecture**:
  - **Lazy Initialization**: Critical ML models and external cloud connections defer initialization until needed, allowing the web server to start instantly.
  - **Non-Blocking Handlers**: All API route handlers are offloaded to FastAPI's background worker threadpool, ensuring the event loop never blocks during heavy I/O tasks.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, LangChain, Pydantic, SQLite (WAL mode), ChromaDB
- **Models**: `jina-embeddings-v5-text-small`, `jina-reranker-v2-base-multilingual`, `anthropic/claude-opus-4.7` (via FastRouter API)
- **Frontend**: HTML5, TailwindCSS, Lucide Icons, Vanilla JavaScript

---

## 💻 Local Setup & Development

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and supply your API keys:
```env
OPENAI_API_KEY=your_fastrouter_or_openai_key
OPENAI_BASE_URL=https://api.fastrouter.ai/api/v1
JINA_API_KEY=your_jina_api_key
CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_chroma_tenant_id
CHROMA_DATABASE=rag-system
```

### 4. Run Server
Start the Uvicorn development server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🌐 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/query` | `POST` | Execute RAG pipeline with history context |
| `/api/v1/upload` | `POST` | Upload a document (`.txt`, `.pdf`, `.docx`) for background ingestion |
| `/api/v1/status` | `GET` | Retrieve vector store document counts and status |
| `/api/v1/sessions` | `GET` | Fetch all historical chat sessions for the sidebar |
| `/api/v1/sessions/{id}/messages` | `GET` | Fetch messages and source citations for a session |
| `/api/v1/sessions/{id}` | `PUT` | Rename a chat session title |
| `/api/v1/sessions/{id}` | `DELETE` | Delete a chat session and its history |

---

## ☁️ Azure Deployment Guide

This application is designed to be easily deployed to **Azure App Service** as a Python Web App.

### Option A: Azure App Service (Code Deployment)

#### 1. Configure Startup Command
Azure Linux App Services run Python web applications utilizing Gunicorn. Set the startup command configuration in Azure:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

#### 2. Set App Settings (Environment Variables)
Navigate to **Settings > Configuration** in your Azure App Service portal and add your environment variables matching the `.env` parameters:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `JINA_API_KEY`
- `CHROMA_API_KEY`
- `CHROMA_TENANT`
- `CHROMA_DATABASE`

#### 3. Persistent Database Storage
Because the chat history is stored in a local SQLite file (`data/db/chats.db`), you **MUST** ensure the files are persisted across container recycles:
- Under App Service Configuration, set the environment setting:
  `WEBSITES_ENABLE_APP_SERVICE_STORAGE = true`
- This ensures the `/data` directory mounts to persistent Azure storage, saving your chats and local vector DB fallbacks safely.

---

### Option B: Deploy via Docker (Azure Container Apps)
If you prefer containerized deployment, create a `Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim

WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
```
Deploy the container to **Azure Container Apps** and mount an **Azure File Share** to `/workspace/data` to persist your chat database.

---

* Developer * - Asim Husain - www.asimhusain.dev
