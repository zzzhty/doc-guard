import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.doc_impact import DocImpact
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.commit_scanner import CommitScanner
from app.services.config_parser import load_docops_for_project
from app.services.doc_scanner import DocScanner
from app.services.llm_service import LLMService
from app.services.module_matcher import ModuleMatcher

logger = logging.getLogger(__name__)


class ImpactService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze_commit(self, commit_id: int) -> list[DocImpact]:
        commit = self.db.query(ScannedCommit).filter(ScannedCommit.id == commit_id).first()
        if not commit:
            raise ValueError(f"Commit {commit_id} not found")

        existing = self.db.query(DocImpact).filter(DocImpact.commit_id == commit.id).all()
        if existing:
            if commit.analysis_status != "completed":
                commit.analysis_status = "completed"
                self.db.commit()
            return existing

        commit.analysis_status = "analyzing"
        self.db.commit()

        try:
            project = self.db.query(Project).filter(Project.id == commit.project_id).first()
            scanner = CommitScanner(self.db)
            diff = scanner.get_commit_diff(commit_id)

            changed_files = commit.changed_files or self._extract_changed_files(diff)

            config = load_docops_for_project(project)
            if not config:
                logger.warning("No docops.yml found, using empty config")
                from app.services.config_parser import DocOpsConfig
                config = DocOpsConfig()

            matcher = ModuleMatcher(config)
            candidate_docs = matcher.find_candidate_docs(changed_files)

            doc_scanner = DocScanner(project.local_path)
            scanned_docs = doc_scanner.scan_all()
            existing_docs = [d.path for d in scanned_docs["docs"] + scanned_docs["wiki"]]
            all_candidate_docs = matcher.find_affected_docs(changed_files)

            if existing_docs and not candidate_docs:
                fallback_docs = self._find_fallback_candidate_docs(changed_files, existing_docs)
                all_candidate_docs = fallback_docs
                if fallback_docs:
                    candidate_docs = [
                        {
                            "module": "general",
                            "owner": "",
                            "changed_files": changed_files,
                            "candidate_docs": fallback_docs,
                        }
                    ]

            if not existing_docs or not candidate_docs:
                commit.analysis_status = "completed"
                self.db.commit()
                return []

            if not settings.llm_api_key:
                impacts = self._create_heuristic_impacts(commit, candidate_docs, existing_docs)
                commit.analysis_status = "completed"
                self.db.commit()
                return impacts

            llm = LLMService()
            interpretation = await llm.interpret_change(diff=diff, commit_message=commit.message)
            impacts = []
            for mod_info in candidate_docs:
                result = await llm.analyze_impact({
                    "changed_files": mod_info["changed_files"],
                    "affected_areas": interpretation.affected_areas,
                    "change_summary": interpretation.summary,
                    "module_name": mod_info["module"],
                    "candidate_docs": mod_info["candidate_docs"],
                })
                for item in result:
                    if item.document_path not in existing_docs:
                        continue
                    impact = DocImpact(
                        commit_id=commit.id,
                        document_path=item.document_path,
                        module_name=mod_info["module"],
                        impact_level=item.impact_level,
                        reason=item.reason,
                        confidence=item.confidence,
                        status="pending_analysis",
                    )
                    self.db.add(impact)
                    impacts.append(impact)

            # If no module-based results, do a fallback with all candidate docs
            if not impacts and all_candidate_docs:
                result = await llm.analyze_impact({
                    "changed_files": changed_files,
                    "affected_areas": interpretation.affected_areas,
                    "change_summary": interpretation.summary,
                    "module_name": "general",
                    "candidate_docs": all_candidate_docs,
                })
                for item in result:
                    if item.document_path not in existing_docs:
                        continue
                    impact = DocImpact(
                        commit_id=commit.id,
                        document_path=item.document_path,
                        module_name="general",
                        impact_level=item.impact_level,
                        reason=item.reason,
                        confidence=item.confidence,
                        status="pending_analysis",
                    )
                    self.db.add(impact)
                    impacts.append(impact)

            commit.analysis_status = "completed"
            self.db.commit()

            logger.info("Impact analysis complete for commit %s: %d impacts", commit.commit_hash, len(impacts))
            return impacts

        except Exception as e:
            commit.analysis_status = "failed"
            self.db.commit()
            raise RuntimeError(f"Impact analysis failed: {e}") from e

    def _extract_changed_files(self, diff: str) -> list[str]:
        files = []
        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    fpath = parts[3].lstrip("b/")
                    files.append(fpath)
            elif line.startswith("--- a/") or line.startswith("+++ b/"):
                pass
        return sorted(set(files))

    def _find_fallback_candidate_docs(self, changed_files: list[str], existing_docs: list[str]) -> list[str]:
        changed_tokens = self._path_tokens(changed_files)
        if not changed_tokens:
            return []

        candidates = []
        for doc_path in existing_docs:
            doc_tokens = self._path_tokens([doc_path])
            if changed_tokens.intersection(doc_tokens):
                candidates.append(doc_path)
        return sorted(set(candidates))

    def _path_tokens(self, paths: list[str]) -> set[str]:
        tokens = set()
        for value in paths:
            path = Path(value)
            for part in path.parts:
                for token in part.replace("-", "_").split("_"):
                    stem = Path(token).stem.lower()
                    if stem and stem not in {"src", "app", "tests", "docs", "wiki", "md", "py"}:
                        tokens.add(stem)
        return tokens

    def _create_heuristic_impacts(
        self,
        commit: ScannedCommit,
        candidate_docs: list[dict],
        existing_docs: list[str],
    ) -> list[DocImpact]:
        impacts = []
        seen = set()
        existing = set(existing_docs)
        for mod_info in candidate_docs:
            for document_path in mod_info["candidate_docs"]:
                if document_path in seen or document_path not in existing:
                    continue
                seen.add(document_path)
                module_name = mod_info["module"]
                impact = DocImpact(
                    commit_id=commit.id,
                    document_path=document_path,
                    module_name=module_name,
                    impact_level="medium",
                    reason=(
                        "Candidate document matched changed files via docops or path similarity. "
                        "LLM_API_KEY is not configured, so this is a conservative heuristic impact."
                    ),
                    confidence=0.5,
                    status="pending_analysis",
                )
                self.db.add(impact)
                impacts.append(impact)
        return impacts

    def get_impacts(self, project_id: int, status: str | None = None) -> list[DocImpact]:
        commit_ids = (
            self.db.query(ScannedCommit.id)
            .filter(ScannedCommit.project_id == project_id)
            .subquery()
        )
        q = self.db.query(DocImpact).filter(DocImpact.commit_id.in_(commit_ids))
        if status:
            q = q.filter(DocImpact.status == status)
        impact_order = case(
            (DocImpact.impact_level == "high", 0),
            (DocImpact.impact_level == "medium", 1),
            (DocImpact.impact_level == "low", 2),
            else_=3,
        )
        return q.order_by(impact_order, DocImpact.created_at.desc()).all()

    def get_impact(self, impact_id: int) -> DocImpact | None:
        return self.db.query(DocImpact).filter(DocImpact.id == impact_id).first()

    def update_impact_status(self, impact_id: int, status: str) -> DocImpact | None:
        allowed_statuses = {"pending_analysis", "ignored", "false_positive"}
        if status not in allowed_statuses:
            raise ValueError(f"Unsupported impact status: {status}")
        impact = self.get_impact(impact_id)
        if not impact:
            return None
        impact.status = status
        impact.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(impact)
        return impact
