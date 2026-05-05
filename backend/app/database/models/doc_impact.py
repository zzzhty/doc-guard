from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocImpact(Base):
    __tablename__ = "doc_impacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commit_id: Mapped[int] = mapped_column(ForeignKey("scanned_commits.id"), nullable=False)
    document_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    module_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    impact_level: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    patch_id: Mapped[int | None] = mapped_column(ForeignKey("patches.id"), nullable=True)
    doc_pr_id: Mapped[int | None] = mapped_column(ForeignKey("doc_prs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending_analysis")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
