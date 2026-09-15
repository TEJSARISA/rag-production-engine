from typing import List, Tuple, Any, Dict
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import DocumentChunk

class VectorStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_chunks(self, chunks: List[Tuple[Any, str, np.ndarray, int, Dict[str, Any]]]):
        """
        chunks: List of tuples (document_id, content, embedding, chunk_index, metadata)
        """
        objs = []
        for doc_id, content, embedding, idx, meta in chunks:
            objs.append(
                DocumentChunk(
                    document_id=doc_id,
                    content=content,
                    embedding=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                    chunk_index=idx,
                    metadata_=meta,
                )
            )
        self.db.add_all(objs)
        await self.db.commit()

    async def similarity_search(self, query_emb: np.ndarray, top_k: int = 5) -> List[DocumentChunk]:
        emb_list = query_emb.tolist() if isinstance(query_emb, np.ndarray) else query_emb
        stmt = (
            select(DocumentChunk)
            .order_by(DocumentChunk.embedding.op("<=>")(emb_list))  # cosine distance
            .limit(top_k)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
