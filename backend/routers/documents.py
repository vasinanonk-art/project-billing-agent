from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
import models
from database import get_db
from dependencies import get_current_user, require_roles

router = APIRouter(prefix="/documents", tags=["Documents / OCR Ready"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.get("/")
def get_documents(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Document).order_by(models.Document.id.desc()).all()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), document_type: str = Form("Contract"), project_id: int | None = Form(None), db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    stored_name = f"{uuid4().hex}_{file.filename}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(await file.read())
    item = models.Document(project_id=project_id, document_type=document_type, file_name=file.filename, file_path=str(path), parsed_status="Uploaded", source_channel="Web Upload")
    db.add(item)
    db.add(models.AuditLog(actor=user.email, action="UPLOAD_DOCUMENT", detail=file.filename))
    db.commit()
    db.refresh(item)
    return item

@router.post("/{document_id}/mock-ocr")
def mock_ocr(document_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    item = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not item:
        return {"status": "error", "message": "Document not found"}
    item.raw_text = "OCR mock text: PO Number, Contract Value, Invoice No., Due Date."
    item.ai_summary = "AI summary placeholder."
    item.parsed_status = "OCR Mocked"
    db.add(models.AuditLog(actor=user.email, action="MOCK_OCR", detail=item.file_name))
    db.commit()
    db.refresh(item)
    return item
