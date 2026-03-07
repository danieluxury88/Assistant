"""AI provider client — Phase 1: Anthropic API."""

import json
from typing import Any

import anthropic

from commit_sage.config import get_settings


class LLMError(Exception):
    pass


def call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """
    Call the Anthropic API and return the raw text response.
    Raises LLMError on failure.
    """
    settings = get_settings()
    api_key = settings.anthropic_api_key
    if not api_key:
        raise LLMError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )

    resolved_model = model or settings.commit_sage_model

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=resolved_model,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
    except anthropic.AuthenticationError as e:
        raise LLMError(f"Authentication failed: {e}") from e
    except anthropic.RateLimitError as e:
        raise LLMError(f"Rate limit exceeded: {e}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError(f"Connection error: {e}") from e
    except anthropic.APIError as e:
        raise LLMError(f"API error: {e}") from e


def parse_json_response(text: str) -> dict[str, Any]:
    """
    Extract and parse JSON from the AI response.
    Handles responses that may contain extra text around the JSON.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON block between first { and last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    raise LLMError(f"Could not parse JSON from AI response:\n{text}")
