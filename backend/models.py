from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="Viewer")
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class AccessRequest(Base):
    __tablename__ = "access_requests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    email = Column(String, nullable=False)
    requested_role = Column(String, default="Viewer")
    reason = Column(Text, nullable=True)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String, nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    project_manager = Column(String, nullable=True)
    contract_value = Column(Float, default=0)
    status = Column(String, default="Active")
    contracts = relationship("Contract", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    po_number = Column(String, nullable=False)
    contract_name = Column(String, nullable=True)
    contract_value = Column(Float, default=0)
    vat_amount = Column(Float, default=0)
    total_value = Column(Float, default=0)
    payment_term = Column(String, nullable=True)
    status = Column(String, default="Active")
    project = relationship("Project", back_populates="contracts")
    milestones = relationship("BillingMilestone", back_populates="contract", cascade="all, delete-orphan")

class BillingMilestone(Base):
    __tablename__ = "billing_milestones"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    milestone_name = Column(String, nullable=False)
    milestone_percent = Column(Float, default=0)
    milestone_amount = Column(Float, default=0)
    planned_billing_date = Column(String, nullable=True)
    status = Column(String, default="Planned")
    remark = Column(String, nullable=True)
    contract = relationship("Contract", back_populates="milestones")
    invoices = relationship("Invoice", back_populates="milestone", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(Integer, ForeignKey("billing_milestones.id"), nullable=True)
    invoice_number = Column(String, nullable=False)
    invoice_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    outstanding_amount = Column(Float, default=0)
    payment_status = Column(String, default="Unpaid")
    due_date = Column(String, nullable=True)
    remark = Column(String, nullable=True)
    milestone = relationship("BillingMilestone", back_populates="invoices")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    document_type = Column(String, default="Contract")
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    parsed_status = Column(String, default="Uploaded")
    source_channel = Column(String, default="Web Upload")
    project = relationship("Project", back_populates="documents")
