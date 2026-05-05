from app.llm.base import BaseLLMAgent


class PatchWriter(BaseLLMAgent):
    temperature = 0.2

    def build_prompt(self, context: dict) -> str:
        original = context.get("original", "")
        diff = context.get("diff", "")
        change_type = context.get("change_type", "update_section")

        return f"""You are a documentation patch writer. Based on a code diff and an existing document section, write an updated version of the document section.

Only modify what is necessary to reflect the code changes. Do not rewrite the entire document. Do not add speculative content that cannot be inferred from the diff.

Change Type: {change_type}
Code Diff:
{diff[:3000]}

Original Document Section:
{original[:3000]}

Output a JSON object with:
- target_section_heading: The heading of the section being modified
- new_content: The updated content for this section (in the original document's language)
- change_summary: A one-line summary of what was changed
- source_commit_referenced: boolean, whether the source commit is referenced in the output
"""

    def parse_response(self, response: str) -> dict:
        result = super().parse_response(response)
        return {
            "target_section_heading": result.get("target_section_heading", ""),
            "new_content": result.get("new_content", ""),
            "change_summary": result.get("change_summary", ""),
            "source_commit_referenced": result.get("source_commit_referenced", False),
        }
