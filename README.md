# Project Billing Agent Full v1.9

This is a full clean package. Do not mix with older patch files.

## Backend
```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
python3 -m pip install -r requirements.txt
python seed.py
python3 -m uvicorn main:app --reload
```

Backend:
http://127.0.0.1:8000/docs

Default login:
admin@example.com
admin1234

## Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend:
http://localhost:5173

## Features
- Login/Register/Approval
- Role-based access
- Data Entry: Project, Contract, Milestone, Invoice
- Manage Data: List + Delete
- Payment update
- PM Dashboard
- Billing Eligibility
- Telegram command API
- Telegram webhook-ready
- Documents upload/mock OCR
- Audit Log model

## Deploy
```bash
git add .
git commit -m "Full package v1.9"
git push
```
