import os, urllib.parse, urllib.request
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

def tg_api(method: str, params: dict):
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN is not set"}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except Exception as error:
        return {"ok": False, "error": str(error)}

def send_message(chat_id: str, text: str):
    return tg_api("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def money(value: str):
    try:
        return float(value.replace(",", "").strip())
    except Exception:
        return 0

def project_status_text(project_name: str, db: Session):
    project = db.query(models.Project).filter(models.Project.project_name.ilike(f"%{project_name}%")).first()
    if not project:
        return "ไม่พบโครงการ"
    contracts = db.query(models.Contract).filter(models.Contract.project_id == project.id).all()
    contract_ids = [item.id for item in contracts]
    milestones = db.query(models.BillingMilestone).filter(models.BillingMilestone.contract_id.in_(contract_ids)).all() if contract_ids else []
    milestone_ids = [item.id for item in milestones]
    invoices = db.query(models.Invoice).filter(models.Invoice.milestone_id.in_(milestone_ids)).all() if milestone_ids else []
    ready = [m.milestone_name for m in milestones if not [i for i in invoices if i.milestone_id == m.id]]
    ready_text = "\n".join([f"- {item}" for item in ready]) if ready else "- ไม่มี"
    return f"<b>{project.project_name}</b>\nมูลค่างานรวม: {sum(c.total_value or 0 for c in contracts):,.2f} บาท\nจำนวนงวดงาน: {len(milestones)} งวด\nวางบิลแล้ว: {sum(i.invoice_amount or 0 for i in invoices):,.2f} บาท\nรับเงินแล้ว: {sum(i.paid_amount or 0 for i in invoices):,.2f} บาท\nค้างรับ: {sum(i.outstanding_amount or 0 for i in invoices):,.2f} บาท\n\n<b>งวดที่ยังไม่พบ Invoice</b>\n{ready_text}"

def handle_command(text: str, actor: str, db: Session):
    parts = [item.strip() for item in text.strip().split("|")]
    cmd = parts[0].split()[0].lower() if parts else ""
    if cmd in ["/help", "help"]:
        return "<b>Commands</b>\n/status Cloud 11\n/addproject Project | Customer | Value\n/pay INV001 | Amount\n/requests\n/approve 1\n/reject 1"
    if cmd == "/status":
        name = text.replace("/status", "").strip()
        return project_status_text(name, db) if name else "กรุณาระบุชื่อโครงการ เช่น /status Cloud 11"
    if cmd == "/addproject" and len(parts) >= 3:
        name = parts[0].replace("/addproject", "").strip()
        item = models.Project(project_name=name, customer_name=parts[1], contract_value=money(parts[2]), project_manager=actor, status="Active")
        db.add(item)
        db.add(models.AuditLog(actor=actor, action="TG_ADD_PROJECT", detail=name))
        db.commit()
        return f"เพิ่มโครงการแล้ว: {name}"
    if cmd == "/pay" and len(parts) >= 2:
        inv_no = parts[0].replace("/pay", "").strip()
        inv = db.query(models.Invoice).filter(models.Invoice.invoice_number == inv_no).first()
        if not inv:
            return f"ไม่พบ Invoice: {inv_no}"
        paid = money(parts[1])
        inv.paid_amount = paid
        inv.outstanding_amount = max(inv.invoice_amount - paid, 0)
        inv.payment_status = "Paid" if inv.outstanding_amount <= 0 else "Partial Paid"
        db.add(models.AuditLog(actor=actor, action="TG_UPDATE_PAYMENT", detail=f"{inv_no}: {paid}"))
        db.commit()
        return f"อัปเดตรับเงินแล้ว\nInvoice: {inv_no}\nPaid: {paid:,.2f} บาท\nOutstanding: {inv.outstanding_amount:,.2f} บาท"
    if cmd == "/requests":
        reqs = db.query(models.AccessRequest).filter(models.AccessRequest.status == "Pending").order_by(models.AccessRequest.id.desc()).all()
        if not reqs:
            return "ไม่มีรายการขอสิทธิ์ที่รออนุมัติ"
        return "\n".join([f"ID: {r.id}\nName: {r.full_name}\nEmail: {r.email}\nRole: {r.requested_role}\nApprove: /approve {r.id}\nReject: /reject {r.id}\n" for r in reqs])
    if cmd == "/approve":
        rid = text.replace("/approve", "").strip()
        if not rid.isdigit():
            return "รูปแบบไม่ถูกต้อง เช่น /approve 1"
        req = db.query(models.AccessRequest).filter(models.AccessRequest.id == int(rid)).first()
        if not req:
            return "ไม่พบคำขอสิทธิ์"
        user = db.query(models.User).filter(models.User.email == req.email).first()
        if not user:
            return "ไม่พบ User"
        req.status = "Approved"
        user.status = "Approved"
        user.role = req.requested_role or "Viewer"
        db.add(models.AuditLog(actor=actor, action="TG_APPROVE_USER", detail=req.email))
        db.commit()
        return f"อนุมัติแล้ว: {req.full_name} ({user.role})"
    if cmd == "/reject":
        rid = text.replace("/reject", "").strip()
        if not rid.isdigit():
            return "รูปแบบไม่ถูกต้อง เช่น /reject 1"
        req = db.query(models.AccessRequest).filter(models.AccessRequest.id == int(rid)).first()
        if not req:
            return "ไม่พบคำขอสิทธิ์"
        user = db.query(models.User).filter(models.User.email == req.email).first()
        req.status = "Rejected"
        if user:
            user.status = "Rejected"
        db.add(models.AuditLog(actor=actor, action="TG_REJECT_USER", detail=req.email))
        db.commit()
        return f"ปฏิเสธแล้ว: {req.full_name}"
    return "ไม่รู้จักคำสั่ง พิมพ์ /help"

@router.get("/setup-webhook")
def setup_webhook(base_url: str):
    url = f"{base_url.rstrip('/')}/telegram/webhook"
    return {"webhook_url": url, "result": tg_api("setWebhook", {"url": url})}

@router.post("/command")
def command(payload: schemas.TelegramCommandIn, db: Session = Depends(get_db)):
    return {"reply": handle_command(payload.text, payload.actor or "web-user", db)}

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    update = await request.json()
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    sender = msg.get("from") or {}
    chat_id = str(chat.get("id", ""))
    text = msg.get("text", "")
    actor = sender.get("username") or str(sender.get("id", "telegram-user"))
    if chat_id and text:
        send_message(chat_id, handle_command(text, actor, db))
    return {"ok": True}
