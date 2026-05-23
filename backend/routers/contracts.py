from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from dependencies import get_current_user, require_roles

router = APIRouter(prefix="/contracts", tags=["Contracts / PO"])

@router.get("/")
def get_contracts(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Contract).order_by(models.Contract.id.desc()).all()

@router.post("/")
def create_contract(payload: schemas.ContractCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    data = payload.model_dump()
    data["vat_amount"] = round(data["contract_value"] * 0.07, 2)
    data["total_value"] = round(data["contract_value"] * 1.07, 2)
    item = models.Contract(**data)
    db.add(item)
    db.add(models.AuditLog(actor=user.email, action="CREATE_CONTRACT", detail=payload.po_number))
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    item = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(item)
    db.add(models.AuditLog(actor=user.email, action="DELETE_CONTRACT", detail=str(contract_id)))
    db.commit()
    return {"status": "deleted"}
