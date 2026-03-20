"""AI provider clients."""

import json
from typing import Any

import anthropic

try:
    import openai
except ImportError:
    openai = None

from commit_sage.config import get_settings, resolve_ai_provider, resolve_model


class LLMError(Exception):
    pass


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    settings = get_settings()

    try:
        provider = resolve_ai_provider(settings, require_credentials=True)
    except ValueError as e:
        raise LLMError(str(e)) from e

    if provider == "anthropic":
        return call_anthropic(system_prompt, user_prompt, model=model, settings=settings)
    if provider == "openai":
        return call_openai(system_prompt, user_prompt, model=model, settings=settings)

    raise LLMError(f"Unsupported AI provider '{provider}'.")


def call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    settings=None,
) -> str:
    """
    Call the Anthropic API and return the raw text response.
    Raises LLMError on failure.
    """
    settings = settings or get_settings()
    api_key = settings.anthropic_api_key
    if not api_key:
        raise LLMError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )

    resolved_model = resolve_model("anthropic", settings, model)

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


def call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    settings=None,
) -> str:
    """
    Call the OpenAI Responses API and return the text response.
    Raises LLMError on failure.
    """
    settings = settings or get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        raise LLMError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )

    if openai is None:
        raise LLMError(
            "OPENAI_API_KEY is set, but the 'openai' package is not installed. "
            "Install dependencies again before using the OpenAI provider."
        )

    resolved_model = resolve_model("openai", settings, model)

    client_kwargs = {"api_key": api_key}
    if settings.openai_base_url.strip():
        client_kwargs["base_url"] = settings.openai_base_url.strip()

    client = openai.OpenAI(**client_kwargs)

    try:
        response = client.responses.create(
            model=resolved_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = getattr(response, "output_text", "")
        if text:
            return text
        raise LLMError("OpenAI returned an empty response.")
    except Exception as e:
        raise LLMError(f"OpenAI API error: {e}") from e


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
