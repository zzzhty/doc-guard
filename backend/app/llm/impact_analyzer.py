from app.llm.base import BaseLLMAgent


class ImpactAnalyzer(BaseLLMAgent):
    temperature = 0.3

    def build_prompt(self, context: dict) -> str:
        changed_files = context.get("changed_files", [])
        affected_areas = context.get("affected_areas", [])
        change_summary = context.get("change_summary", "")
        module_name = context.get("module_name", "")
        candidate_docs = context.get("candidate_docs", [])

        return f"""You are a documentation impact analyzer. Given a code change, determine which documentation files are affected and at what level.

Code Change Summary:
{change_summary}

Module: {module_name}
Affected Areas: {", ".join(affected_areas)}
Changed Files:
{chr(10).join(f"- {f}" for f in changed_files)}

Candidate Documentation Files:
{chr(10).join(f"- {d}" for d in candidate_docs) if candidate_docs else "None specified — assess based on change"}

For each candidate document, assess the impact level and explain why. Output a JSON array of objects, each with:
- document_path: The path to the affected document
- impact_level: "high", "medium", or "low"
- reason: A brief explanation of why this document is affected (in the original language)
- confidence: A float between 0 and 1 indicating your confidence

Impact level guidelines:
- "high": The change directly contradicts or makes the document's information incorrect, or requires major updates to API docs, config docs, or architecture docs
- "medium": The change modifies behavior that should be reflected in docs but docs remain roughly accurate
- "low": Minor changes, clarifications, or the document is only tangentially related

Only include documents that are genuinely affected. If no documents are affected, return an empty array.
"""

    def parse_response(self, response: str) -> list[dict]:
        result = super().parse_response(response)
        if isinstance(result, dict) and "impacts" in result:
            items = result["impacts"]
        elif isinstance(result, list):
            items = result
        else:
            items = []
        return items
