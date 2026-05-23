import models
from database import Base, SessionLocal, engine
from security import hash_password

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

admin = models.User(full_name="System Admin", email="admin@example.com", password_hash=hash_password("admin1234"), role="Admin", status="Approved", department="Management", position="Admin")
db.add(admin)

project = models.Project(project_name="Cloud 11", customer_name="MQDC", project_manager="Beer", contract_value=10000000, status="Active")
db.add(project)
db.commit()
db.refresh(project)

contract = models.Contract(project_id=project.id, po_number="PO-CLOUD11-001", contract_name="Turnstile & VMS System", contract_value=10000000, vat_amount=700000, total_value=10700000, payment_term="30/50/20", status="Active")
db.add(contract)
db.commit()
db.refresh(contract)

milestone = models.BillingMilestone(project_id=project.id, contract_id=contract.id, milestone_name="งวดที่ 1 - Advance Payment", milestone_percent=30, milestone_amount=3000000, planned_billing_date="2026-02-01", status="Billed")
db.add(milestone)
db.commit()
db.refresh(milestone)

invoice = models.Invoice(milestone_id=milestone.id, invoice_number="INV-CLOUD11-001", invoice_amount=3000000, paid_amount=0, outstanding_amount=3000000, payment_status="Unpaid", due_date="2026-03-06")
db.add(invoice)
db.commit()
db.close()
print("Seed data created. Login: admin@example.com / admin1234")
