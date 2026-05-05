import logging

from sqlalchemy.orm import Session

from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR, DocPRItem
from app.database.models.patch import Patch
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.git_providers.local import LocalGitProvider
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class DocPRService:
    def __init__(self, db: Session):
        self.db = db

    async def create_pr(self, project_id: int, patch_ids: list[int]) -> DocPR:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        patches = self.db.query(Patch).filter(Patch.id.in_(patch_ids)).all()
        if not patches:
            raise ValueError("No valid patches found")

        patches = [p for p in patches if p.status == "approved"]
        if not patches:
            raise ValueError("No approved patches found")

        # Get source commit info
        impact_ids = [p.doc_impact_id for p in patches]
        impacts = self.db.query(DocImpact).filter(DocImpact.id.in_(impact_ids)).all()
        commit_ids = list(set(i.commit_id for i in impacts))
        commits = self.db.query(ScannedCommit).filter(ScannedCommit.id.in_(commit_ids)).all()

        # Build branch name
        source_hash = commits[0].commit_hash[:7] if commits else "unknown"
        module = impacts[0].module_name if impacts else "docs"
        branch_name = f"docguard/update-{module}-{source_hash}"

        # Build PR description via LLM
        llm = LLMService()
        changed_files = self._collect_changed_files(commits)
        affected_docs = [p.document_path for p in patches]
        patch_summaries = [self._summarize_patch(p) for p in patches]

        pr_desc = await llm.write_pr_description({
            "commit_hash": source_hash,
            "commit_message": commits[0].message if commits else "",
            "changed_files": changed_files[:20],
            "affected_docs": affected_docs,
            "patch_summaries": patch_summaries,
            "review_notes": ["Please verify accuracy of documentation changes"],
        })

        # For local provider: create branch locally, apply patches, commit, push
        try:
            provider = ProjectService.get_git_provider(project)
            if isinstance(provider, LocalGitProvider):
                provider.create_branch(branch_name, project.default_branch)
                from app.git_providers import FileChange
                files = []
                for p in patches:
                    files.append(FileChange(
                        path=p.document_path,
                        content=p.patched_content or p.original_content or "",
                    ))
                commit_msg = f"docs({module}): update documentation\n\nSource commit: {commits[0].commit_hash if commits else 'unknown'}\nGenerated-by: DocGuard"
                provider.commit_files(branch_name, commit_msg, files)

            # Create PR in DocGuard DB (PR creation on remote handled separately)
            doc_pr = DocPR(
                project_id=project.id,
                provider=project.provider,
                branch_name=branch_name,
                base_branch=project.default_branch,
                source_commit=commits[0].commit_hash if commits else None,
                title=pr_desc.title,
                status="open",
            )
            self.db.add(doc_pr)
            self.db.commit()
            self.db.refresh(doc_pr)

            # Create PR items
            for p in patches:
                item = DocPRItem(
                    doc_pr_id=doc_pr.id,
                    document_path=p.document_path,
                    patch_id=p.id,
                    change_type=p.change_type,
                    review_required=True,
                    status="included",
                )
                self.db.add(item)

            # Update impact status
            for i in impacts:
                i.doc_pr_id = doc_pr.id
                i.status = "pr_created"

            self.db.commit()
            self.db.refresh(doc_pr)

            logger.info("Created doc PR %s with %d patches", branch_name, len(patches))
            return doc_pr

        except Exception as e:
            logger.error("Failed to create PR: %s", str(e))
            raise e

    def _collect_changed_files(self, commits: list[ScannedCommit]) -> list[str]:
        files = set()
        for c in commits:
            # Simple extraction from message - actual files come from scan
            for line in c.message.split("\n"):
                line = line.strip()
                if "/" in line and not line.startswith("#"):
                    pass
        return list(files)

    def _summarize_patch(self, patch: Patch) -> str:
        return f"{patch.change_type}: {patch.document_path}"

    def get_pr(self, doc_pr_id: int) -> DocPR | None:
        return self.db.query(DocPR).filter(DocPR.id == doc_pr_id).first()

    def get_prs_for_project(self, project_id: int) -> list[DocPR]:
        return (
            self.db.query(DocPR)
            .filter(DocPR.project_id == project_id)
            .order_by(DocPR.created_at.desc())
            .all()
        )

    def get_pr_items(self, doc_pr_id: int) -> list[DocPRItem]:
        return self.db.query(DocPRItem).filter(DocPRItem.doc_pr_id == doc_pr_id).all()

    def refresh_status(self, doc_pr_id: int) -> DocPR | None:
        doc_pr = self.get_pr(doc_pr_id)
        if not doc_pr:
            return None
        # For MVP, status is manually updated or via webhook
        # In production, this would call Gitea API
        doc_pr.status = doc_pr.status
        self.db.commit()
        return doc_pr

    def close_pr(self, doc_pr_id: int) -> DocPR | None:
        doc_pr = self.get_pr(doc_pr_id)
        if not doc_pr:
            return None
        doc_pr.status = "closed"
        self.db.commit()
        self.db.refresh(doc_pr)

        # Update linked impacts
        impacts = self.db.query(DocImpact).filter(DocImpact.doc_pr_id == doc_pr_id).all()
        for i in impacts:
            i.status = "pr_rejected"
        self.db.commit()

        return doc_pr
