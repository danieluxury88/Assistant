"""AI provider clients."""

import json
import subprocess
from typing import Any

import anthropic

try:
    import openai
except ImportError:
    openai = None

from commit_sage.config import Profile, get_settings, resolve_api_key, resolve_model, resolve_profile

COMMAND_TIMEOUT_SECONDS = 300


class LLMError(Exception):
    pass


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    profile: str | None = None,
) -> str:
    settings = get_settings()

    try:
        name, resolved = resolve_profile(settings, profile)
    except ValueError as e:
        raise LLMError(str(e)) from e

    resolved_model = resolve_model(resolved, settings, model)

    if resolved.provider == "anthropic":
        return call_anthropic(system_prompt, user_prompt, model=resolved_model, profile=resolved, name=name)
    if resolved.provider == "openai":
        return call_openai(system_prompt, user_prompt, model=resolved_model, profile=resolved, name=name)
    if resolved.provider == "command":
        return call_command(system_prompt, user_prompt, model=resolved_model, profile=resolved, name=name)

    raise LLMError(f"Unsupported AI provider '{resolved.provider}'.")


def _require_api_key(profile: Profile, name: str) -> str:
    api_key = resolve_api_key(profile)
    if not api_key:
        source = profile.api_key_env or "api_key"
        raise LLMError(
            f"Profile '{name}' needs an API key: set {source} "
            "in the environment or in ~/.config/commit-sage/.env."
        )
    return api_key


def call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    profile: Profile,
    name: str = "",
) -> str:
    """
    Call the Anthropic API and return the raw text response.
    Raises LLMError on failure.
    """
    client = anthropic.Anthropic(api_key=_require_api_key(profile, name))

    try:
        message = client.messages.create(
            model=model,
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
    model: str,
    profile: Profile,
    name: str = "",
) -> str:
    """
    Call an OpenAI-compatible Responses API (OpenAI, or a local server via base_url).
    Raises LLMError on failure.
    """
    if openai is None:
        raise LLMError(
            "The 'openai' package is not installed. "
            "Install dependencies again before using an OpenAI-compatible profile."
        )

    client_kwargs = {"api_key": _require_api_key(profile, name)}
    if profile.base_url:
        client_kwargs["base_url"] = profile.base_url

    client = openai.OpenAI(**client_kwargs)

    try:
        response = client.responses.create(
            model=model,
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


def call_command(
    system_prompt: str,
    user_prompt: str,
    model: str | None,
    profile: Profile,
    name: str = "",
) -> str:
    """
    Run a CLI (e.g. a subscription-based agent such as `claude -p`) with the prompt on stdin
    and return its stdout.
    Raises LLMError on failure.
    """
    argv = [arg.replace("{model}", model or "") for arg in profile.command or []]
    prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        result = subprocess.run(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as e:
        raise LLMError(f"Profile '{name}': command not found: {argv[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"Profile '{name}': command timed out after {COMMAND_TIMEOUT_SECONDS}s.") from e

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise LLMError(f"Profile '{name}': command exited with {result.returncode}: {detail}")
    if not result.stdout.strip():
        raise LLMError(f"Profile '{name}': command returned no output.")
    return result.stdout


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
