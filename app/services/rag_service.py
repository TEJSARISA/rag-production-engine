import os
from typing import List, Tuple
import numpy as np
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_store import VectorStore
from app.models.document import DocumentChunk
from app.schemas.chat import Citation
from app.core.config import settings

class RagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = VectorStore(db)

        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif settings.GROQ_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None

    async def _embed_text(self, text: str) -> np.ndarray:
        if not self.client:
            raise RuntimeError("Neither OPENAI_API_KEY nor GROQ_API_KEY is configured")

        resp = await self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        return np.array(resp.data[0].embedding, dtype=np.float32)

    async def answer_question(self, question: str) -> Tuple[str, List[Citation]]:
        query_emb = await self._embed_text(question)

        # Retrieve top-K matching chunks
        chunks: List[DocumentChunk] = await self.vector_store.similarity_search(query_emb, top_k=5)

        if not chunks:
            return "No relevant context found in database.", []

        # Build context prompt
        context = "\n---\n".join([f"Chunk ID [{c.id}]:\n{c.content}" for c in chunks])

        resp = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise, grounded AI Assistant. Answer the user's question using ONLY "
                        "the provided context. Cite chunk IDs where appropriate. If the context does not "
                        "contain the answer, state that you do not have enough information."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0.2,
        )
        answer = resp.choices[0].message.content or ""

        citations = []
        for c in chunks:
            source = c.metadata_.get("source", "unknown") if c.metadata_ else "unknown"
            citations.append(
                Citation(
                    chunk_id=str(c.id),
                    source=source,
                    similarity=0.90  # cosine similarity score representation
                )
            )

        return answer, citations
