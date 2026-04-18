from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.company import CompanyInterpretation, CompanyInput
from app.schemas.match import CompanyMatchResponse
from app.services.company_interpreter import interpret_company_input
from app.services.retrieval_service import match_company_to_staff


router = APIRouter(prefix="/company", tags=["company"])


@router.post("/interpret", response_model=CompanyInterpretation)
def interpret_company(payload: CompanyInput) -> CompanyInterpretation:
    return interpret_company_input(payload)


@router.post("/match", response_model=CompanyMatchResponse)
def match_company(payload: CompanyInput, db: Session = Depends(get_db)) -> CompanyMatchResponse:
    company = interpret_company_input(payload)
    matches = match_company_to_staff(db=db, company=company)
    return CompanyMatchResponse(company=company, matches=matches)

