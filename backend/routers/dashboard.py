from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
import models
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return {"total_projects": db.query(func.count(models.Project.id)).scalar() or 0, "total_contract_value": db.query(func.sum(models.Contract.total_value)).scalar() or 0, "total_invoice_amount": db.query(func.sum(models.Invoice.invoice_amount)).scalar() or 0, "total_paid_amount": db.query(func.sum(models.Invoice.paid_amount)).scalar() or 0, "total_outstanding": db.query(func.sum(models.Invoice.outstanding_amount)).scalar() or 0, "document_count": db.query(func.count(models.Document.id)).scalar() or 0}

@router.get("/pm-summary")
def pm_summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    projects = db.query(models.Project).order_by(models.Project.id.desc()).all()
    rows = []
    total_milestones = 0
    billed_milestones = 0
    for p in projects:
        contracts = db.query(models.Contract).filter(models.Contract.project_id == p.id).all()
        contract_ids = [c.id for c in contracts]
        milestones = db.query(models.BillingMilestone).filter(models.BillingMilestone.contract_id.in_(contract_ids)).all() if contract_ids else []
        milestone_ids = [m.id for m in milestones]
        invoices = db.query(models.Invoice).filter(models.Invoice.milestone_id.in_(milestone_ids)).all() if milestone_ids else []
        total_milestones += len(milestones)
        billed_milestones += len([m for m in milestones if m.status in ["Billed", "Invoiced", "Paid"]])
        rows.append({"project_id": p.id, "project_name": p.project_name, "customer_name": p.customer_name, "status": p.status, "contract_value": sum(c.total_value or 0 for c in contracts), "milestone_total": len(milestones), "milestone_billed": len([m for m in milestones if m.status in ["Billed", "Invoiced", "Paid"]]), "invoice_total": sum(i.invoice_amount or 0 for i in invoices), "paid_total": sum(i.paid_amount or 0 for i in invoices), "outstanding_total": sum(i.outstanding_amount or 0 for i in invoices)})
    total_invoice = db.query(func.sum(models.Invoice.invoice_amount)).scalar() or 0
    total_paid = db.query(func.sum(models.Invoice.paid_amount)).scalar() or 0
    return {"total_projects": len(projects), "total_contract_value": db.query(func.sum(models.Contract.total_value)).scalar() or 0, "total_milestones": total_milestones, "billed_milestones": billed_milestones, "billing_progress": round((billed_milestones / total_milestones) * 100, 2) if total_milestones else 0, "total_invoice_amount": total_invoice, "total_paid_amount": total_paid, "total_outstanding": db.query(func.sum(models.Invoice.outstanding_amount)).scalar() or 0, "collection_rate": round((total_paid / total_invoice) * 100, 2) if total_invoice else 0, "projects": rows}

@router.get("/billing-eligibility")
def billing_eligibility(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    result = []
    for p in db.query(models.Project).order_by(models.Project.id.desc()).all():
        contracts = db.query(models.Contract).filter(models.Contract.project_id == p.id).all()
        contract_ids = [c.id for c in contracts]
        milestones = db.query(models.BillingMilestone).filter(models.BillingMilestone.contract_id.in_(contract_ids)).all() if contract_ids else []
        ms = []
        for m in milestones:
            invs = db.query(models.Invoice).filter(models.Invoice.milestone_id == m.id).all()
            invoice_amount = sum(i.invoice_amount or 0 for i in invs)
            paid_amount = sum(i.paid_amount or 0 for i in invs)
            outstanding_amount = sum(i.outstanding_amount or 0 for i in invs)
            if invs and outstanding_amount <= 0 and paid_amount > 0:
                status, rec = "Paid", "จ่ายแล้ว ตรวจสอบเอกสารปิดงวดได้"
            elif invs and paid_amount > 0:
                status, rec = "Partial Paid", "รับเงินบางส่วนแล้ว ยังไม่ควรปิดงวด"
            elif invs:
                status, rec = "Billed - Waiting Payment", "วางบิลแล้ว รอติดตามรับเงิน"
            else:
                status, rec = "Ready to Bill", "สามารถพิจารณาให้ ผรม. วางบิลได้ หากงานและเอกสารครบ"
            ms.append({"milestone_id": m.id, "milestone_name": m.milestone_name, "milestone_percent": m.milestone_percent or 0, "milestone_amount": m.milestone_amount or 0, "milestone_status": m.status, "invoice_numbers": [i.invoice_number for i in invs], "invoice_amount": invoice_amount, "paid_amount": paid_amount, "outstanding_amount": outstanding_amount, "eligibility_status": status, "recommendation": rec})
        result.append({"project_id": p.id, "project_name": p.project_name, "customer_name": p.customer_name, "status": p.status, "ready_to_bill_count": len([x for x in ms if x["eligibility_status"] == "Ready to Bill"]), "paid_milestone_count": len([x for x in ms if x["eligibility_status"] == "Paid"]), "total_outstanding_amount": sum(x["outstanding_amount"] for x in ms), "milestones": ms})
    return result
