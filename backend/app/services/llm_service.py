import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ChangeInterpretation:
    summary: str
    affected_areas: list[str]
    changed_files_grouped: dict[str, list[str]]


@dataclass
class ImpactResult:
    document_path: str
    impact_level: str
    reason: str
    confidence: float


@dataclass
class PatchResult:
    target_section_heading: str
    new_content: str
    change_summary: str
    source_commit_referenced: bool


@dataclass
class QualityReport:
    issues: list[dict]
    overall_score: int
    requires_review: bool


@dataclass
class PRDescription:
    title: str
    body: str


class LLMService:
    def __init__(self):
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
        return self._client

    async def _call_llm(
        self, prompt: str, temperature: float = 0.3, response_json: bool = True
    ) -> str:
        kwargs = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if response_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def interpret_change(self, diff: str, commit_message: str) -> ChangeInterpretation:
        from app.llm.change_interpreter import ChangeInterpreter

        agent = ChangeInterpreter()
        prompt = agent.build_prompt({"diff": diff, "commit_message": commit_message})
        raw = await self._call_llm(prompt)
        result = agent.parse_response(raw)
        return ChangeInterpretation(**result)

    async def analyze_impact(self, context: dict) -> list[ImpactResult]:
        from app.llm.impact_analyzer import ImpactAnalyzer

        agent = ImpactAnalyzer()
        prompt = agent.build_prompt(context)
        raw = await self._call_llm(prompt)
        items = agent.parse_response(raw)
        return [ImpactResult(**item) for item in items]

    async def generate_patch(self, context: dict) -> PatchResult:
        from app.llm.patch_writer import PatchWriter

        agent = PatchWriter()
        prompt = agent.build_prompt(context)
        raw = await self._call_llm(prompt, temperature=0.2)
        result = agent.parse_response(raw)
        return PatchResult(**result)

    async def review_patch(self, original: str, patched: str, change_type: str) -> QualityReport:
        from app.llm.doc_reviewer import DocReviewer

        agent = DocReviewer()
        prompt = agent.build_prompt({
            "original": original,
            "patched": patched,
            "change_type": change_type,
        })
        raw = await self._call_llm(prompt)
        result = agent.parse_response(raw)
        return QualityReport(**result)

    async def write_pr_description(self, context: dict) -> PRDescription:
        from app.llm.pr_author import PRAuthor

        agent = PRAuthor()
        prompt = agent.build_prompt(context)
        raw = await self._call_llm(prompt, temperature=0.5)
        result = agent.parse_response(raw)
        return PRDescription(**result)
