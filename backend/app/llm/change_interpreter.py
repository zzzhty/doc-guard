from app.llm.base import BaseLLMAgent


class ChangeInterpreter(BaseLLMAgent):
    temperature = 0.3

    def build_prompt(self, context: dict) -> str:
        diff = context.get("diff", "")
        commit_message = context.get("commit_message", "")

        if len(diff) > 4000:
            diff = diff[:4000] + "\n... [diff truncated]"

        return f"""You are a code change interpreter. Analyze the following git commit and determine what changed and what areas are affected.

Commit Message:
{commit_message}

Git Diff:
{diff}

Output a JSON object with these keys:
- summary: A 2-3 sentence summary of what this commit changes (in the original language of the commit)
- affected_areas: A list of tags from: api, config, schema, deploy, behavior, ui, security, dependencies, tests, docs
- changed_files_grouped: An object mapping categories (e.g. "core_logic", "config", "tests", "docs") to lists of file paths

Only include information that can be directly inferred from the diff. Do not speculate.
"""

    def parse_response(self, response: str) -> dict:
        result = super().parse_response(response)
        return {
            "summary": result.get("summary", ""),
            "affected_areas": result.get("affected_areas", []),
            "changed_files_grouped": result.get("changed_files_grouped", {}),
        }
