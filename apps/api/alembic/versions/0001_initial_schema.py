from __future__ import annotations

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "staff_registry",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("profile_slug", sa.Text(), unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("profile_url", sa.Text(), nullable=False),
        sa.Column("bio", sa.Text()),
        sa.Column("primary_school", sa.Text()),
        sa.Column("school_affiliations", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("department", sa.Text()),
        sa.Column("source_system", sa.Text(), nullable=False, server_default=sa.text("'profiles.faculty.utah.edu'")),
        sa.Column("has_publication_signal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("eligible_for_matching", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "staff_match_profiles",
        sa.Column("staff_id", sa.Text(), sa.ForeignKey("staff_registry.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ai_research_summary", sa.Text(), nullable=False),
        sa.Column("research_keywords", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sector_tags", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("technical_tags", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_active_year", sa.Integer()),
        sa.Column("openalex_author_id", sa.Text()),
        sa.Column("embedding_summary", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("embedding_research", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("publication_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("citation_count_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "papers",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("staff_id", sa.Text(), sa.ForeignKey("staff_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("openalex_work_id", sa.Text()),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer()),
        sa.Column("venue", sa.Text()),
        sa.Column("abstract", sa.Text()),
        sa.Column("paper_url", sa.Text()),
        sa.Column("pdf_url", sa.Text()),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("sector_tags", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("technical_tags", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("embedding_paper", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("is_recent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_top_cited", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "paper_authors",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("paper_id", sa.Text(), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_name", sa.Text(), nullable=False),
        sa.Column("author_position", sa.Integer()),
        sa.Column("is_uofu", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("matched_staff_id", sa.Text(), sa.ForeignKey("staff_registry.id")),
        sa.Column("affiliation", sa.Text()),
        sa.Column("profile_url", sa.Text()),
    )

    op.create_table(
        "company_queries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("ticker", sa.Text()),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("primary_sector", sa.Text(), nullable=False),
        sa.Column("subsector", sa.Text()),
        sa.Column("products_services", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("technical_themes", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("market_keywords", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("research_need_summary", sa.Text(), nullable=False),
        sa.Column("school_affinities", sa.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("confidence", sa.Text()),
        sa.Column("embedding_summary", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("embedding_themes", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("idx_staff_registry_matching", "staff_registry", ["eligible_for_matching"])
    op.create_index("idx_staff_match_profiles_openalex", "staff_match_profiles", ["openalex_author_id"])
    op.create_index("idx_papers_staff_id", "papers", ["staff_id"])
    op.create_index("idx_papers_year", "papers", ["year"])
    op.create_index("idx_papers_citations", "papers", ["citation_count"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS staff_summary_vec_idx "
        "ON staff_match_profiles USING ivfflat (embedding_summary vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS staff_research_vec_idx "
        "ON staff_match_profiles USING ivfflat (embedding_research vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS paper_vec_idx "
        "ON papers USING ivfflat (embedding_paper vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS paper_vec_idx")
    op.execute("DROP INDEX IF EXISTS staff_research_vec_idx")
    op.execute("DROP INDEX IF EXISTS staff_summary_vec_idx")
    op.drop_index("idx_papers_citations", table_name="papers")
    op.drop_index("idx_papers_year", table_name="papers")
    op.drop_index("idx_papers_staff_id", table_name="papers")
    op.drop_index("idx_staff_match_profiles_openalex", table_name="staff_match_profiles")
    op.drop_index("idx_staff_registry_matching", table_name="staff_registry")
    op.drop_table("company_queries")
    op.drop_table("paper_authors")
    op.drop_table("papers")
    op.drop_table("staff_match_profiles")
    op.drop_table("staff_registry")
