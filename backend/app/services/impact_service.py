import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models.doc_impact import DocImpact
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.commit_scanner import CommitScanner
from app.services.config_parser import load_docops_from_repo
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

        commit.analysis_status = "analyzing"
        self.db.commit()

        try:
            project = self.db.query(Project).filter(Project.id == commit.project_id).first()
            scanner = CommitScanner(self.db)
            diff = scanner.get_commit_diff(commit_id)

            changed_files = self._extract_changed_files(diff)

            config = load_docops_from_repo(project.local_path)
            if not config:
                logger.warning("No docops.yml found, using empty config")
                from app.services.config_parser import DocOpsConfig
                config = DocOpsConfig()

            matcher = ModuleMatcher(config)
            candidate_docs = matcher.find_candidate_docs(changed_files)
            all_candidate_docs = matcher.find_affected_docs(changed_files)

            doc_scanner = DocScanner(project.local_path)
            existing_docs = [d.path for d in doc_scanner.scan_all()["docs"] + doc_scanner.scan_all()["wiki"]]

            if not existing_docs:
                all_candidate_docs = []

            llm = LLMService()

            # Step 1: Interpret the change
            interpretation = await llm.interpret_change(
                diff=diff,
                commit_message=commit.message,
            )

            # Step 2: Analyze impact for each module
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
            raise e

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
        return list(set(files))

    def get_impacts(self, project_id: int, status: str | None = None) -> list[DocImpact]:
        commit_ids = (
            self.db.query(ScannedCommit.id)
            .filter(ScannedCommit.project_id == project_id)
            .subquery()
        )
        q = self.db.query(DocImpact).filter(DocImpact.commit_id.in_(commit_ids))
        if status:
            q = q.filter(DocImpact.status == status)
        return q.order_by(DocImpact.impact_level.desc(), DocImpact.created_at.desc()).all()

    def get_impact(self, impact_id: int) -> DocImpact | None:
        return self.db.query(DocImpact).filter(DocImpact.id == impact_id).first()

    def update_impact_status(self, impact_id: int, status: str) -> DocImpact | None:
        impact = self.get_impact(impact_id)
        if not impact:
            return None
        impact.status = status
        impact.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(impact)
        return impact
