from app.llm.base import BaseLLMAgent


class PRAuthor(BaseLLMAgent):
    temperature = 0.5

    def build_prompt(self, context: dict) -> str:
        commit_hash = context.get("commit_hash", "")
        commit_message = context.get("commit_message", "")
        changed_files = context.get("changed_files", [])
        affected_docs = context.get("affected_docs", [])
        patch_summaries = context.get("patch_summaries", [])
        review_notes = context.get("review_notes", [])

        return f"""You are a PR description writer for DocWatcher, an AI documentation governance bot. Write a PR title and description for a documentation update PR.

Source Commit: {commit_hash}
Commit Message: {commit_message}

Changed Files:
{chr(10).join(f"- {f}" for f in changed_files)}

Affected Documentation:
{chr(10).join(f"- {d}" for d in affected_docs)}

Proposed Changes:
{chr(10).join(f"- {s}" for s in patch_summaries)}

Review Notes:
{chr(10).join(f"- {n}" for n in review_notes) if review_notes else "None"}

Output a JSON object with:
- title: The PR title (format: "[DocWatcher] Update {{module}} docs for {{change_summary}}")
- body: The full PR description in markdown, including Summary, Source Change, Affected Docs, Proposed Changes, Review Notes, and Quality Checks sections
"""

    def parse_response(self, response: str) -> dict:
        result = super().parse_response(response)
        return {
            "title": result.get("title", ""),
            "body": result.get("body", ""),
        }
