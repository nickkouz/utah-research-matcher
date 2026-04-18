from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import company, health, staff
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Company-to-researcher discovery API for the University of Utah.",
)

app.include_router(health.router)
app.include_router(company.router)
app.include_router(staff.router)

