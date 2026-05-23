from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from dependencies import get_current_user, require_roles

router = APIRouter(prefix="/milestones", tags=["Billing Milestones"])

@router.get("/")
def get_milestones(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.BillingMilestone).order_by(models.BillingMilestone.id.desc()).all()

@router.post("/")
def create_milestone(payload: schemas.MilestoneCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    contract = db.query(models.Contract).filter(models.Contract.id == payload.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    item = models.BillingMilestone(**payload.model_dump())
    db.add(item)
    db.add(models.AuditLog(actor=user.email, action="CREATE_MILESTONE", detail=payload.milestone_name))
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{milestone_id}")
def update_milestone(milestone_id: int, payload: dict, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    item = db.query(models.BillingMilestone).filter(models.BillingMilestone.id == milestone_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for key in ["milestone_name", "milestone_percent", "milestone_amount", "planned_billing_date", "status", "remark"]:
        if key in payload:
            setattr(item, key, payload[key])
    db.add(models.AuditLog(actor=user.email, action="UPDATE_MILESTONE", detail=f"Milestone ID {milestone_id}"))
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{milestone_id}")
def delete_milestone(milestone_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    item = db.query(models.BillingMilestone).filter(models.BillingMilestone.id == milestone_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(item)
    db.add(models.AuditLog(actor=user.email, action="DELETE_MILESTONE", detail=str(milestone_id)))
    db.commit()
    return {"status": "deleted"}
