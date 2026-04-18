from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CompanyQuery(Base):
    __tablename__ = "company_queries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    ticker: Mapped[str | None] = mapped_column(Text)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    primary_sector: Mapped[str] = mapped_column(Text, nullable=False)
    subsector: Mapped[str | None] = mapped_column(Text)
    products_services: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    technical_themes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    market_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    research_need_summary: Mapped[str] = mapped_column(Text, nullable=False)
    school_affinities: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    confidence: Mapped[str | None] = mapped_column(Text)
    embedding_summary: Mapped[list[float] | None] = mapped_column(Vector(1536))
    embedding_themes: Mapped[list[float] | None] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

