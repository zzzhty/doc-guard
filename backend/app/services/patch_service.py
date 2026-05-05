import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.doc_utils import extract_sections, generate_unified_diff
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

        llm = LLMService()

        # Generate patch
        patch_result = await llm.generate_patch({
            "original": sections_text if sections_text else original_content[:3000],
            "diff": code_diff[:3000],
            "change_type": change_type,
        })

        # Build patched content
        patched_content = patch_result.new_content if patch_result.new_content else None

        # Review the patch
        review = await llm.review_patch(
            original=sections_text[:2000],
            patched=patched_content[:2000] if patched_content else "",
            change_type=change_type,
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
            change_type=change_type,
            original_content=original_content[:10000],
            patched_content=patched_content[:10000] if patched_content else None,
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
        patch.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(patch)
        return patch

    def approve_patch(self, patch_id: int) -> Patch | None:
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
