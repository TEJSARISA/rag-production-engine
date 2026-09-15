from pydantic import BaseModel, Field

class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="UUID of the uploaded document")
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Initial processing status")

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
