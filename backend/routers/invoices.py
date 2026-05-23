from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from dependencies import get_current_user, require_roles

router = APIRouter(prefix="/invoices", tags=["Invoices / Payments"])

@router.get("/")
def get_invoices(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Invoice).order_by(models.Invoice.id.desc()).all()

@router.get("/unpaid")
def get_unpaid_invoices(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Invoice).filter(models.Invoice.payment_status != "Paid").order_by(models.Invoice.id.desc()).all()

@router.get("/overdue")
def get_overdue_invoices(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    today = date.today()
    result = []
    for inv in db.query(models.Invoice).filter(models.Invoice.payment_status != "Paid").all():
        if not inv.due_date:
            continue
        try:
            due = datetime.strptime(inv.due_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if due < today:
            result.append({"id": inv.id, "invoice_number": inv.invoice_number, "invoice_amount": inv.invoice_amount, "paid_amount": inv.paid_amount, "outstanding_amount": inv.outstanding_amount, "payment_status": inv.payment_status, "due_date": inv.due_date, "overdue_days": (today - due).days, "remark": inv.remark})
    return result

@router.post("/")
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "PM", "Finance"))):
    item = models.Invoice(milestone_id=payload.milestone_id, invoice_number=payload.invoice_number, invoice_amount=payload.invoice_amount, paid_amount=0, outstanding_amount=payload.invoice_amount, payment_status="Unpaid", due_date=payload.due_date, remark=payload.remark)
    db.add(item)
    db.add(models.AuditLog(actor=user.email, action="CREATE_INVOICE", detail=payload.invoice_number))
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{invoice_id}/payment")
def update_payment(invoice_id: int, payload: schemas.PaymentUpdate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin", "Finance", "PM"))):
    item = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Invoice not found")
    item.paid_amount = payload.paid_amount
    item.outstanding_amount = max(item.invoice_amount - payload.paid_amount, 0)
    item.payment_status = "Paid" if item.outstanding_amount <= 0 else ("Partial Paid" if item.paid_amount > 0 else "Unpaid")
    if payload.remark:
        item.remark = payload.remark
    db.add(models.AuditLog(actor=user.email, action="UPDATE_PAYMENT", detail=f"{item.invoice_number}: {payload.paid_amount}"))
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    item = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(item)
    db.add(models.AuditLog(actor=user.email, action="DELETE_INVOICE", detail=str(invoice_id)))
    db.commit()
    return {"status": "deleted"}
