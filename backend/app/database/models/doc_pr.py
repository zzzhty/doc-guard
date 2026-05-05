from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocPR(Base):
    __tablename__ = "doc_prs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="gitea")
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    branch_name: Mapped[str] = mapped_column(String(512), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    source_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    merged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DocPRItem(Base):
    __tablename__ = "doc_pr_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_pr_id: Mapped[int] = mapped_column(ForeignKey("doc_prs.id"), nullable=False)
    document_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    patch_id: Mapped[int | None] = mapped_column(ForeignKey("patches.id"), nullable=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False, default="update_section")
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
