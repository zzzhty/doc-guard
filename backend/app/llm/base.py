import json


class BaseLLMAgent:
    model: str = "gpt-4o-mini"
    temperature: float = 0.3

    def build_prompt(self, context: dict) -> str:
        raise NotImplementedError

    def parse_response(self, response: str) -> dict:
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
