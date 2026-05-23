from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import auth, contracts, dashboard, documents, invoices, milestones, projects, telegram

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Billing Agent", version="1.9.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(contracts.router)
app.include_router(milestones.router)
app.include_router(invoices.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(telegram.router)

@app.get("/")
def root():
    return {"status": "running", "version": "1.9.0"}
