from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StaffRegistry(Base):
    __tablename__ = "staff_registry"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    profile_slug: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    profile_url: Mapped[str] = mapped_column(Text, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    primary_school: Mapped[str | None] = mapped_column(Text)
    school_affiliations: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    department: Mapped[str | None] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(Text, default="profiles.faculty.utah.edu")
    has_publication_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    eligible_for_matching: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    match_profile: Mapped["StaffMatchProfile | None"] = relationship(
        back_populates="staff",
        uselist=False,
        cascade="all, delete-orphan",
    )
    papers: Mapped[list["Paper"]] = relationship(back_populates="staff", cascade="all, delete-orphan")


class StaffMatchProfile(Base):
    __tablename__ = "staff_match_profiles"

    staff_id: Mapped[str] = mapped_column(ForeignKey("staff_registry.id", ondelete="CASCADE"), primary_key=True)
    ai_research_summary: Mapped[str] = mapped_column(Text, nullable=False)
    research_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    sector_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    technical_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    last_active_year: Mapped[int | None] = mapped_column(Integer)
    openalex_author_id: Mapped[str | None] = mapped_column(Text)
    embedding_summary: Mapped[list[float] | None] = mapped_column(Vector(1536))
    embedding_research: Mapped[list[float] | None] = mapped_column(Vector(1536))
    publication_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_count_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    staff: Mapped[StaffRegistry] = relationship(back_populates="match_profile")


from app.models.paper import Paper  # noqa: E402

