import json
import logging
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.config import settings
from app.core.doc_utils import apply_patch_to_section, extract_sections, find_section_by_heading, generate_unified_diff
from app.database.models.doc_impact import DocImpact
from app.database.models.patch import Patch
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.commit_scanner import CommitScanner
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class PatchService:
    def __init__(self, db: Session):
        self.db = db

    async def generate_patch(self, impact_id: int, change_type: str = "update_section") -> Patch:
        impact = self.db.query(DocImpact).filter(DocImpact.id == impact_id).first()
        if not impact:
            raise ValueError(f"Impact {impact_id} not found")

        commit = self.db.query(ScannedCommit).filter(ScannedCommit.id == impact.commit_id).first()
        project = self.db.query(Project).filter(Project.id == commit.project_id).first()

        scanner = CommitScanner(self.db)
        code_diff = scanner.get_commit_diff(commit.id)

        provider = ProjectService.get_git_provider(project)
        original_content = provider.get_file_content(impact.document_path) or ""

        # Extract relevant sections
        sections = extract_sections(original_content)
        sections_text = "\n\n".join(
            f"[{s['heading']}]\n{s['content'][:500]}" for s in sections[:10]
        )

        patch_result, effective_change_type = await self._generate_patch_result(
            original=sections_text if sections_text else original_content[:3000],
            code_diff=code_diff[:3000],
            change_type=change_type,
        )
        patched_content, effective_change_type = self._build_patched_content(
            original_content=original_content,
            patch_result=patch_result,
            change_type=effective_change_type,
        )
        review = await self._review_patch(
            original=sections_text[:2000],
            patched=patched_content[:2000],
            change_type=effective_change_type,
        )

        # Generate diff
        diff_text = generate_unified_diff(
            original_content[:5000],
            patched_content if patched_content else original_content,
            filename=impact.document_path,
        )

        patch = Patch(
            doc_impact_id=impact.id,
            document_path=impact.document_path,
            change_type=effective_change_type,
            original_content=original_content[:10000],
            patched_content=patched_content[:10000],
            diff=diff_text[:10000],
            quality_report=json.dumps({
                "issues": review.issues,
                "overall_score": review.overall_score,
                "requires_review": review.requires_review,
            }),
            status="pending",
        )
        self.db.add(patch)
        self.db.commit()
        self.db.refresh(patch)

        impact.patch_id = patch.id
        impact.status = "patch_generated"
        self.db.commit()

        return patch

    async def _generate_patch_result(self, original: str, code_diff: str, change_type: str):
        if not settings.llm_api_key:
            return (
                SimpleNamespace(
                    target_section_heading="",
                    new_content=(
                        "DocWatcher identified this document as potentially affected by the source change. "
                        "LLM_API_KEY is not configured, so this patch is a review marker rather than a generated "
                        "documentation rewrite."
                    ),
                    change_summary="Mark document for manual review",
                    source_commit_referenced=False,
                ),
                "append_section" if change_type == "update_section" else change_type,
            )

        llm = LLMService()
        return (
            await llm.generate_patch(
                {
                    "original": original,
                    "diff": code_diff,
                    "change_type": change_type,
                }
            ),
            change_type,
        )

    def _build_patched_content(self, original_content: str, patch_result, change_type: str) -> tuple[str, str]:
        new_content = patch_result.new_content or ""
        heading = patch_result.target_section_heading or ""

        if change_type == "update_section" and heading and find_section_by_heading(original_content, heading):
            return apply_patch_to_section(original_content, heading, new_content), "update_section"

        if change_type == "mark_stale":
            marker = "> [!WARNING]\n> DocWatcher marked this document as potentially stale for manual review.\n"
            return f"{marker}\n{original_content}" if original_content else marker, "mark_stale"

        section_heading = heading if heading.startswith("#") else f"## {heading or 'DocWatcher Review Required'}"
        section = f"{section_heading}\n\n{new_content}".strip()
        separator = "\n\n" if original_content.strip() else ""
        return f"{original_content.rstrip()}{separator}{section}\n", "append_section"

    async def _review_patch(self, original: str, patched: str, change_type: str):
        if not settings.llm_api_key:
            return SimpleNamespace(
                issues=[
                    {
                        "type": "manual_review",
                        "severity": "warning",
                        "description": "LLM_API_KEY is not configured; patch requires human review.",
                    }
                ],
                overall_score=70,
                requires_review=True,
            )

        llm = LLMService()
        return await llm.review_patch(original=original, patched=patched, change_type=change_type)

    def get_patch(self, patch_id: int) -> Patch | None:
        return self.db.query(Patch).filter(Patch.id == patch_id).first()

    def get_patches_for_project(self, project_id: int) -> list[Patch]:
        commit_ids = (
            self.db.query(ScannedCommit.id)
            .filter(ScannedCommit.project_id == project_id)
            .subquery()
        )
        impact_ids = (
            self.db.query(DocImpact.id)
            .filter(DocImpact.commit_id.in_(commit_ids))
            .subquery()
        )
        return (
            self.db.query(Patch)
            .filter(Patch.doc_impact_id.in_(impact_ids))
            .order_by(Patch.created_at.desc())
            .all()
        )

    def update_patch(self, patch_id: int, content: str) -> Patch | None:
        patch = self.get_patch(patch_id)
        if not patch:
            return None
        patch.patched_content = content[:10000]
        patch.diff = generate_unified_diff(
            patch.original_content or "",
            content,
            filename=patch.document_path,
        )
        patch.status = "edited"
        patch.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(patch)
        return patch

    def approve_patch(self, patch_id: int) -> Patch | None:
        patch = self.get_patch(patch_id)
        if not patch:
            return None
        if patch.status not in {"pending", "edited"}:
            raise ValueError(f"Patch cannot be approved from status: {patch.status}")
        return self._set_patch_status(patch_id, "approved")

    def reject_patch(self, patch_id: int) -> Patch | None:
        return self._set_patch_status(patch_id, "rejected")

    def _set_patch_status(self, patch_id: int, status: str) -> Patch | None:
        patch = self.get_patch(patch_id)
        if not patch:
            return None
        patch.status = status
        patch.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(patch)
        return patch
