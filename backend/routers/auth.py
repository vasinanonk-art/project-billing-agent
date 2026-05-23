from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from dependencies import get_current_user, require_roles
from security import create_access_token, hash_password, verify_password

try:
    from routers.telegram import send_message, TELEGRAM_ADMIN_CHAT_ID
except Exception:
    send_message = None
    TELEGRAM_ADMIN_CHAT_ID = ""

router = APIRouter(prefix="/auth", tags=["Auth / Access Approval"])

@router.post("/register")
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(full_name=payload.full_name, department=payload.department, position=payload.position, email=payload.email, password_hash=hash_password(payload.password), role=payload.requested_role, status="Pending")
    access_request = models.AccessRequest(full_name=payload.full_name, department=payload.department, position=payload.position, email=payload.email, requested_role=payload.requested_role, reason=payload.reason, status="Pending")

    db.add(user)
    db.add(access_request)
    db.add(models.AuditLog(actor=payload.email, action="REGISTER_REQUEST", detail=f"Requested role: {payload.requested_role}"))
    db.commit()
    db.refresh(access_request)

    if send_message and TELEGRAM_ADMIN_CHAT_ID:
        message = (
            "<b>New Access Request</b>\n"
            f"ID: {access_request.id}\n"
            f"Name: {payload.full_name}\n"
            f"Department: {payload.department or '-'}\n"
            f"Position: {payload.position or '-'}\n"
            f"Email: {payload.email}\n"
            f"Requested Role: {payload.requested_role}\n"
            f"Reason: {payload.reason or '-'}\n\n"
            f"Approve: /approve {access_request.id}\n"
            f"Reject: /reject {access_request.id}"
        )
        send_message(TELEGRAM_ADMIN_CHAT_ID, message)

    return {"status": "pending", "message": "Registration submitted. Waiting for approval.", "request_id": access_request.id}

@router.post("/login")
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != "Approved":
        return {"status": user.status, "message": "Account is waiting for approval."}
    token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "department": user.department, "position": user.position, "role": user.role, "status": user.status}}

@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "department": user.department, "position": user.position, "role": user.role, "status": user.status}

@router.get("/requests")
def access_requests(db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    return db.query(models.AccessRequest).order_by(models.AccessRequest.id.desc()).all()

@router.post("/approve/{request_id}")
def approve(request_id: int, payload: schemas.ApprovalIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    access_request = db.query(models.AccessRequest).filter(models.AccessRequest.id == request_id).first()
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    target_user = db.query(models.User).filter(models.User.email == access_request.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    access_request.status = "Approved"
    target_user.status = "Approved"
    target_user.role = payload.role
    db.add(models.AuditLog(actor=user.email, action="APPROVE_USER", detail=f"{target_user.email} as {payload.role}"))
    db.commit()
    return {"status": "approved", "email": target_user.email, "role": target_user.role}

@router.post("/reject/{request_id}")
def reject(request_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("Admin"))):
    access_request = db.query(models.AccessRequest).filter(models.AccessRequest.id == request_id).first()
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    target_user = db.query(models.User).filter(models.User.email == access_request.email).first()
    access_request.status = "Rejected"
    if target_user:
        target_user.status = "Rejected"
    db.add(models.AuditLog(actor=user.email, action="REJECT_USER", detail=access_request.email))
    db.commit()
    return {"status": "rejected", "email": access_request.email}

@router.get("/health")
def health():
    return {"status": "ok"}
