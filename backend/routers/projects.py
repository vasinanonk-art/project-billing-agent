from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from dependencies import get_current_user, require_roles

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/")
def get_projects(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Project).order_by(models.Project.id.desc()).all()

@router.post("/")
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    item = models.Project(**payload.model_dump())
    db.add(item)
    db.add(models.AuditLog(actor=user.email, action="CREATE_PROJECT", detail=payload.project_name))
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    item = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(item)
    db.add(models.AuditLog(actor=user.email, action="DELETE_PROJECT", detail=str(project_id)))
    db.commit()
    return {"status": "deleted"}
