import io
import uuid
import json
from typing import List
import numpy as np
from openai import OpenAI
from celery import shared_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def _split_text(text: str) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - CHUNK_OVERLAP
        if start < 0 or start >= len(words):
            break
    return chunks

@shared_task(bind=True, name="process_document_task")
def process_document_task(self, document_id: str, file_bytes: bytes):
    import asyncio

    async def _process():
        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as db:
            doc_uuid = uuid.UUID(document_id)
            doc = await db.get(Document, doc_uuid)
            if not doc:
                return

            doc.status = DocumentStatus.PROCESSING
            await db.commit()

            try:
                # Text extraction (PDF or plain text)
                if file_bytes.startswith(b"%PDF"):
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                    text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
                else:
                    text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = file_bytes.decode("utf-8", errors="ignore")

            chunks = _split_text(text)
            if not chunks:
                doc.status = DocumentStatus.COMPLETED
                await db.commit()
                return

            # Batch embedding generation
            embeddings = []
            if settings.OPENAI_API_KEY or settings.GROQ_API_KEY:
                client = OpenAI(
                    api_key=settings.OPENAI_API_KEY or settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1" if (not settings.OPENAI_API_KEY and settings.GROQ_API_KEY) else None
                )
                batch_size = 10
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    resp = client.embeddings.create(
                        model=settings.EMBEDDING_MODEL,
                        input=batch,
                    )
                    for item in resp.data:
                        embeddings.append(item.embedding)
            else:
                # Mock embedding for testing when no API key provided
                embeddings = [[0.0] * 1536 for _ in chunks]

            # Store chunks
            chunk_objs = []
            for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
                chunk_objs.append(
                    DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=doc_uuid,
                        content=content,
                        embedding=emb,
                        chunk_index=idx,
                        metadata_={"source": doc.filename},
                    )
                )

            db.add_all(chunk_objs)
            doc.status = DocumentStatus.COMPLETED
            await db.commit()

    asyncio.run(_process())
