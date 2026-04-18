from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    staff_id: Mapped[str] = mapped_column(ForeignKey("staff_registry.id", ondelete="CASCADE"), nullable=False)
    openalex_work_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    paper_url: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    sector_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    technical_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    embedding_paper: Mapped[list[float] | None] = mapped_column(Vector(1536))
    is_recent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_top_cited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    staff: Mapped["StaffRegistry"] = relationship(back_populates="papers")
    authors: Mapped[list["PaperAuthor"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    author_name: Mapped[str] = mapped_column(Text, nullable=False)
    author_position: Mapped[int | None] = mapped_column(Integer)
    is_uofu: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_staff_id: Mapped[str | None] = mapped_column(ForeignKey("staff_registry.id"))
    affiliation: Mapped[str | None] = mapped_column(Text)
    profile_url: Mapped[str | None] = mapped_column(Text)

    paper: Mapped[Paper] = relationship(back_populates="authors")


from app.models.staff import StaffRegistry  # noqa: E402

