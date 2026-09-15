# Asynchronous RAG Production Engine

Production-ready, modular, and fully deployable asynchronous Retrieval-Augmented Generation (RAG) API service with background document ingestion, vector search with PostgreSQL (`pgvector`), Redis task queuing, automated LLM evaluations (`DeepEval`), and Docker deployment configurations.

---

## 🏗️ System Architecture

```
                               ┌───────────────────────────┐
                               │     Client Application    │
                               └─────────────┬─────────────┘
                                             │ HTTP (API Key)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI Service                                    │
│  ┌────────────────────────┐    ┌────────────────────────┐    ┌──────────────────────┐  │
│  │ POST /documents/upload │    │ GET /documents/{id}    │    │ POST /chat/query     │  │
│  └───────────┬────────────┘    └────────────────────────┘    └──────────┬───────────┘  │
└──────────────┼──────────────────────────────────────────────────────────┼──────────────┘
               │ Dispatch Task                                            │ Embed & Search
               ▼                                                          ▼
┌───────────────────────────┐                            ┌───────────────────────────────┐
│     Redis Broker &        │                            │   PostgreSQL + pgvector       │
│     Celery Workers        │                            │   - documents                 │
│  (Chunking & Embedding)   │────── Bulk Vector Store ───►   - document_chunks (Vector 1536) │
└───────────────────────────┘                            └───────────────────────────────┘
               │                                                          ▲
               └───────────────── OpenAI / Groq API ──────────────────────┘
```

---

## 🚀 Quick Start (Local Docker Compose)

### 1. Environment Setup
Copy `.env.example` to `.env` and update your settings:
```bash
cp .env.example .env
```

Set your OpenAI or Groq API Key in `.env`:
```env
OPENAI_API_KEY=sk-proj-...
```

### 2. Launch Services
Run the entire stack using Docker Compose:
```bash
docker compose up --build -d
```

Services exposed:
- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL (`pgvector`)**: `localhost:5432`
- **Redis Broker**: `localhost:6379`

---

## 📡 API Endpoints & Usage

All API endpoints require the `x-api-key` header (configured via `API_KEY` in `.env`, default: `super-secret-api-key`).

### 1. Health Check
```bash
curl -H "x-api-key: super-secret-api-key" http://localhost:8000/api/v1/health/
```

### 2. Upload Document (Async Ingestion)
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "x-api-key: super-secret-api-key" \
  -F "file=@sample.pdf"
```
**Response (HTTP 202 Accepted):**
```json
{
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "task_id": "a2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "status": "PENDING"
}
```

### 3. Check Document Processing Status
```bash
curl -H "x-api-key: super-secret-api-key" \
  http://localhost:8000/api/v1/documents/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/status
```

### 4. Query RAG Chat Engine
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "x-api-key: super-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the primary architecture of the background worker?"}'
```
**Response:**
```json
{
  "answer": "The background worker uses Celery with a Redis broker to process document text chunking and batch vector embeddings asynchronously.",
  "citations": [
    {
      "chunk_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
      "source": "sample.pdf",
      "similarity": 0.90
    }
  ]
}
```

---

## 🧪 Automated LLM Evaluations (DeepEval) & Testing

Run unit tests and DeepEval metrics (Faithfulness, Answer Relevancy, Hallucination):

```bash
# Run API unit tests
pytest tests/test_api.py

# Run DeepEval evaluation suite
pytest tests/test_evals_deepeval.py
```

---

## ☁️ Deployment Instructions

### Azure Container Apps Deployment

1. **Log in to Azure CLI & set variables**:
   ```bash
   az login
   RESOURCE_GROUP="rg-rag-production"
   LOCATION="eastus"
   ACR_NAME="acrragproduction"
   ENVIRONMENT_NAME="env-rag-production"

   az group create --name $RESOURCE_GROUP --location $LOCATION
   az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic
   ```

2. **Build and push container image**:
   ```bash
   az acr build --registry $ACR_NAME --image rag-engine:latest .
   ```

3. **Deploy Container Apps Environment**:
   ```bash
   az containerapp env create \
     --name $ENVIRONMENT_NAME \
     --resource-group $RESOURCE_GROUP \
     --location $LOCATION
   ```

4. **Deploy API App**:
   ```bash
   az containerapp create \
     --name rag-api \
     --resource-group $RESOURCE_GROUP \
     --environment $ENVIRONMENT_NAME \
     --image $ACR_NAME.azurecr.io/rag-engine:latest \
     --target-port 8000 \
     --ingress external \
     --env-vars \
       DATABASE_URL="postgresql+asyncpg://<db_user>:<db_pass>@<db_host>:5432/<db_name>" \
       REDIS_URL="redis://<redis_host>:6379/0" \
       OPENAI_API_KEY="sk-proj-..." \
       API_KEY="super-secret-api-key"
   ```

### Deploy to Render / Railway
1. Point your repository to Render or Railway.
2. Select Dockerfile as build context.
3. Provision managed PostgreSQL with `pgvector` extension enabled, and Redis instance.
4. Set environment variables from `.env.example`.

---

## 📄 License

Distributed under the MIT License.
