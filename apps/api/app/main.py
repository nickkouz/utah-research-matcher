from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import company, diagnostics, health, staff
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Company-to-researcher discovery API for the University of Utah.",
)

cors_origins = settings.cors_allowed_origins
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if "*" in cors_origins else cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(diagnostics.router)
app.include_router(company.router)
app.include_router(staff.router)
