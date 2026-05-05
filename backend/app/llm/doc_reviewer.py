from app.llm.base import BaseLLMAgent


class DocReviewer(BaseLLMAgent):
    temperature = 0.3

    def build_prompt(self, context: dict) -> str:
        original = context.get("original", "")
        patched = context.get("patched", "")
        change_type = context.get("change_type", "update_section")

        return f"""You are a documentation quality reviewer. Review the following documentation patch for quality issues.

Change Type: {change_type}

Original:
{original[:2000]}

Patched:
{patched[:2000]}

Check for these issues:
1. Duplicate content with existing sections
2. Excessive length (more than 500 words for a section)
3. Wrong document level (implementation details in API docs, etc.)
4. Speculation or facts not derivable from the code change
5. Missing source commit reference
6. Invalid markdown syntax

Output a JSON object with:
- issues: array of {{"type": string, "severity": "error"|"warning"|"info", "description": string}}
- overall_score: integer 0-100 (100 = perfect quality)
- requires_review: boolean (true if any error-level issues or score < 70)
"""

    def parse_response(self, response: str) -> dict:
        result = super().parse_response(response)
        return {
            "issues": result.get("issues", []),
            "overall_score": result.get("overall_score", 50),
            "requires_review": result.get("requires_review", True),
        }
