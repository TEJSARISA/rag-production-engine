import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.document import DocumentUploadResponse, DocumentStatusResponse
from app.models.document import Document, DocumentStatus
from app.workers.tasks import process_document_task
from app.api.deps import get_db

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    doc = Document(
        id=uuid.uuid4(),
        filename=file.filename or "uploaded_doc.txt",
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    content = await file.read()

    task = process_document_task.delay(str(doc.id), content)

    return DocumentUploadResponse(
        document_id=str(doc.id),
        task_id=task.id,
        status=doc.status,
    )

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_db)):
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id UUID format")

    result = await db.get(Document, doc_uuid)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(
        document_id=document_id,
        status=result.status,
    )
