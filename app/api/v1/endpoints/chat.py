from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RagService
from app.api.deps import get_db

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    rag = RagService(db)
    try:
        answer, citations = await rag.answer_question(request.question)
        return ChatResponse(answer=answer, citations=citations)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
