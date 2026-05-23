from typing import Optional
from pydantic import BaseModel, EmailStr

class RegisterIn(BaseModel):
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    email: EmailStr
    password: str
    requested_role: str = "Viewer"
    reason: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ApprovalIn(BaseModel):
    role: str = "Viewer"

class ProjectCreate(BaseModel):
    project_name: str
    customer_name: Optional[str] = None
    project_manager: Optional[str] = None
    contract_value: float = 0
    status: str = "Active"

class ContractCreate(BaseModel):
    project_id: int
    po_number: str
    contract_name: Optional[str] = None
    contract_value: float = 0
    payment_term: Optional[str] = None
    status: str = "Active"

class MilestoneCreate(BaseModel):
    project_id: int
    contract_id: int
    milestone_name: str
    milestone_percent: float = 0
    milestone_amount: float = 0
    planned_billing_date: Optional[str] = None
    status: str = "Planned"
    remark: Optional[str] = None

class InvoiceCreate(BaseModel):
    milestone_id: Optional[int] = None
    invoice_number: str
    invoice_amount: float
    due_date: Optional[str] = None
    remark: Optional[str] = None

class PaymentUpdate(BaseModel):
    paid_amount: float
    remark: Optional[str] = None

class TelegramCommandIn(BaseModel):
    text: str
    actor: Optional[str] = "web-user"
    chat_id: Optional[str] = None
