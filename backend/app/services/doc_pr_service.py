import logging
import json
import re
from datetime import datetime
from pathlib import PurePosixPath
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR, DocPRItem
from app.database.models.patch import Patch
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.git_providers import FileChange, PRInfo
from app.git_providers.local import LocalGitProvider
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

ALLOWED_DOC_PREFIXES = ("docs/", "wiki/", "meta/")
ALLOWED_DOC_FILES = {"docops.yml"}


class DocPRService:
    def __init__(self, db: Session):
        self.db = db

    async def create_pr(self, project_id: int, patch_ids: list[int]) -> DocPR:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        if not patch_ids:
            raise ValueError("patch_ids is required")

        requested_patch_ids = set(patch_ids)
        patches = self.db.query(Patch).filter(Patch.id.in_(requested_patch_ids)).all()
        if len(patches) != len(requested_patch_ids):
            raise ValueError("Some patches were not found")

        if any(p.status != "approved" for p in patches):
            raise ValueError("All patches must be approved before creating a PR")
        self._validate_document_paths([p.document_path for p in patches])

        impact_ids = [p.doc_impact_id for p in patches]
        impacts = self.db.query(DocImpact).filter(DocImpact.id.in_(impact_ids)).all()
        if len(impacts) != len(set(impact_ids)):
            raise ValueError("Some patch impacts were not found")
        if any(i.doc_pr_id for i in impacts):
            raise ValueError("One or more patches already belong to a DocWatcher PR")

        commit_ids = {i.commit_id for i in impacts}
        if len(commit_ids) != 1:
            raise ValueError("Patches from multiple source commits are not supported in MVP")
        commits = self.db.query(ScannedCommit).filter(ScannedCommit.id.in_(commit_ids)).all()
        if len(commits) != len(commit_ids):
            raise ValueError("Source commit was not found")
        if any(c.project_id != project.id for c in commits):
            raise ValueError("All patches must belong to the requested project")

        source_commit = commits[0]
        source_hash = source_commit.commit_hash[:7]
        module = self._slug(impacts[0].module_name or "docs")
        branch_name = f"doc-watcher/update-{module}-{source_hash}"

        changed_files = self._collect_changed_files(commits)
        affected_docs = [p.document_path for p in patches]
        patch_summaries = [self._summarize_patch(p) for p in patches]

        pr_desc = await self._build_pr_description(
            module=module,
            commit=source_commit,
            changed_files=changed_files,
            affected_docs=affected_docs,
            patch_summaries=patch_summaries,
            patches=patches,
        )

        try:
            provider = ProjectService.get_git_provider(project)
            self._apply_patches(
                provider=provider,
                branch_name=branch_name,
                base_branch=project.default_branch,
                module=module,
                source_commit=source_commit,
                patches=patches,
            )

            pr_info: PRInfo | None = None
            if not isinstance(provider, LocalGitProvider):
                pr_info = provider.create_pr(
                    pr_desc.title,
                    pr_desc.body,
                    branch_name,
                    project.default_branch,
                )

            doc_pr = DocPR(
                project_id=project.id,
                provider=project.provider,
                pr_number=pr_info.number if pr_info else None,
                pr_url=pr_info.url if pr_info else None,
                branch_name=branch_name,
                base_branch=project.default_branch,
                source_commit=source_commit.commit_hash,
                title=pr_desc.title,
                body=pr_desc.body,
                status=pr_info.status if pr_info else "local_branch",
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
            files.update(c.changed_files)
        return sorted(files)

    def _summarize_patch(self, patch: Patch) -> str:
        return f"{patch.change_type}: {patch.document_path}"

    def _apply_patches(
        self,
        provider,
        branch_name: str,
        base_branch: str,
        module: str,
        source_commit: ScannedCommit,
        patches: list[Patch],
    ) -> None:
        if not provider.create_branch(branch_name, base_branch):
            raise RuntimeError(f"Failed to create branch {branch_name}")

        files = [
            FileChange(
                path=p.document_path,
                content=p.patched_content if p.patched_content is not None else p.original_content or "",
            )
            for p in patches
        ]
        commit_msg = (
            f"docs({module}): update documentation\n\n"
            f"Source commit: {source_commit.commit_hash}\n"
            "Generated-by: DocWatcher"
        )
        if not provider.commit_files(branch_name, commit_msg, files):
            raise RuntimeError(f"Failed to commit documentation changes to {branch_name}")

    async def _build_pr_description(
        self,
        module: str,
        commit: ScannedCommit,
        changed_files: list[str],
        affected_docs: list[str],
        patch_summaries: list[str],
        patches: list[Patch],
    ):
        context = {
            "commit_hash": commit.commit_hash,
            "commit_message": commit.message,
            "changed_files": changed_files[:20],
            "affected_docs": affected_docs,
            "patch_summaries": patch_summaries,
            "review_notes": ["Please verify accuracy of documentation changes"],
        }
        if settings.llm_api_key:
            try:
                return await LLMService().write_pr_description(context)
            except Exception as exc:
                logger.warning("Failed to generate PR description with LLM: %s", exc)

        return SimpleNamespace(
            title=f"[DocWatcher] Update {module} documentation",
            body=self._fallback_pr_body(
                commit=commit,
                changed_files=changed_files,
                affected_docs=affected_docs,
                patch_summaries=patch_summaries,
                patches=patches,
            ),
        )

    def _fallback_pr_body(
        self,
        commit: ScannedCommit,
        changed_files: list[str],
        affected_docs: list[str],
        patch_summaries: list[str],
        patches: list[Patch],
    ) -> str:
        commit_title = commit.message.splitlines()[0] if commit.message else ""
        return "\n\n".join(
            [
                "## Summary\nDocWatcher generated this documentation update from approved patch previews.",
                (
                    "## Source Change\n"
                    f"- Source commit: `{commit.commit_hash}`\n"
                    f"- Commit title: {commit_title or 'Not recorded'}\n"
                    f"- Changed files:\n{self._markdown_list(changed_files)}"
                ),
                f"## Affected Docs\n{self._markdown_list(affected_docs)}",
                f"## Proposed Documentation Changes\n{self._markdown_list(patch_summaries)}",
                (
                    "## Review Notes\n"
                    "- Verify that the generated wording matches the source change.\n"
                    "- Confirm examples, configuration names, and links before merge."
                ),
                f"## Quality Checks\n{self._quality_summary(patches)}",
            ]
        )

    def _quality_summary(self, patches: list[Patch]) -> str:
        lines = []
        for patch in patches:
            if not patch.quality_report:
                lines.append(f"- `{patch.document_path}`: no quality report recorded")
                continue
            try:
                report = json.loads(patch.quality_report)
            except json.JSONDecodeError:
                lines.append(f"- `{patch.document_path}`: quality report could not be parsed")
                continue
            score = report.get("overall_score", "n/a")
            review = "review required" if report.get("requires_review") else "review not required"
            issues = report.get("issues") or []
            lines.append(f"- `{patch.document_path}`: score {score}, {review}, {len(issues)} issue(s)")
        return "\n".join(lines) if lines else "- No quality checks recorded"

    def _validate_document_paths(self, paths: list[str]) -> None:
        for path in paths:
            parsed = PurePosixPath(path)
            if parsed.is_absolute() or ".." in parsed.parts:
                raise ValueError(f"Unsafe document path: {path}")
            if path in ALLOWED_DOC_FILES:
                continue
            if not path.startswith(ALLOWED_DOC_PREFIXES):
                raise ValueError(f"Patch path is outside writable documentation roots: {path}")

    def _markdown_list(self, values: list[str]) -> str:
        if not values:
            return "- None recorded"
        return "\n".join(f"- `{value}`" for value in values)

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "docs"

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

        project = self.db.query(Project).filter(Project.id == doc_pr.project_id).first()
        if not project or project.provider == "local" or doc_pr.pr_number is None:
            self._sync_linked_records(doc_pr)
            self.db.commit()
            self.db.refresh(doc_pr)
            return doc_pr

        provider = ProjectService.get_git_provider(project)
        pr_info = provider.get_pr(doc_pr.pr_number)
        return self.apply_remote_status(
            doc_pr=doc_pr,
            status=self._normalize_remote_status(pr_info),
            merged_at=pr_info.merged_at,
            pr_url=pr_info.url,
            title=pr_info.title,
        )

    def close_pr(self, doc_pr_id: int) -> DocPR | None:
        doc_pr = self.get_pr(doc_pr_id)
        if not doc_pr:
            return None

        project = self.db.query(Project).filter(Project.id == doc_pr.project_id).first()
        if project and project.provider == "gitea" and doc_pr.pr_number is not None:
            provider = ProjectService.get_git_provider(project)
            if not provider.close_pr(doc_pr.pr_number):
                raise RuntimeError(f"Failed to close PR {doc_pr.pr_number}")

        return self.apply_remote_status(doc_pr=doc_pr, status="closed")

    def apply_remote_status(
        self,
        doc_pr: DocPR,
        status: str,
        merged_at: datetime | None = None,
        pr_url: str | None = None,
        title: str | None = None,
    ) -> DocPR:
        doc_pr.status = status
        if pr_url:
            doc_pr.pr_url = pr_url
        if title:
            doc_pr.title = title
        if status == "merged":
            doc_pr.merged_at = merged_at or doc_pr.merged_at or datetime.utcnow()

        self._sync_linked_records(doc_pr)
        self.db.commit()
        self.db.refresh(doc_pr)
        return doc_pr

    def _normalize_remote_status(self, pr_info: PRInfo) -> str:
        if pr_info.merged_at or pr_info.status == "merged":
            return "merged"
        if pr_info.status in {"closed", "rejected"}:
            return "closed"
        return "open"

    def _sync_linked_records(self, doc_pr: DocPR) -> None:
        impacts = self.db.query(DocImpact).filter(DocImpact.doc_pr_id == doc_pr.id).all()
        items = self.db.query(DocPRItem).filter(DocPRItem.doc_pr_id == doc_pr.id).all()

        if doc_pr.status == "merged":
            impact_status = "pr_merged"
            item_status = "merged"
        elif doc_pr.status in {"closed", "rejected"}:
            impact_status = "pr_rejected"
            item_status = "rejected"
        else:
            impact_status = "pr_created"
            item_status = "included"

        for impact in impacts:
            impact.status = impact_status
        for item in items:
            item.status = item_status
