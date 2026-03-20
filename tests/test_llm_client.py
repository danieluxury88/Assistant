from types import SimpleNamespace

import pytest

from commit_sage.config import DEFAULT_MODELS, Settings, resolve_ai_provider, resolve_model
from commit_sage.llm_client import LLMError, call_llm, call_openai


def test_resolve_ai_provider_prefers_explicit_override():
    settings = Settings(
        _env_file=None,
        anthropic_api_key="anthropic-key",
        openai_api_key="openai-key",
        commit_sage_provider="openai",
    )
    assert resolve_ai_provider(settings, require_credentials=True) == "openai"


def test_resolve_ai_provider_defaults_to_anthropic_for_backwards_compat():
    settings = Settings(
        _env_file=None,
        anthropic_api_key="anthropic-key",
        openai_api_key="openai-key",
    )
    assert resolve_ai_provider(settings, require_credentials=True) == "anthropic"


def test_resolve_ai_provider_uses_openai_when_only_openai_key_is_present():
    settings = Settings(_env_file=None, openai_api_key="openai-key")
    assert resolve_ai_provider(settings, require_credentials=True) == "openai"


def test_resolve_ai_provider_requires_credentials():
    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="No supported API credentials detected"):
        resolve_ai_provider(settings, require_credentials=True)


def test_resolve_model_uses_provider_default():
    settings = Settings(_env_file=None)
    assert resolve_model("openai", settings) == DEFAULT_MODELS["openai"]


def test_call_llm_dispatches_to_openai(mocker):
    settings = Settings(_env_file=None, openai_api_key="openai-key")
    mocker.patch("commit_sage.llm_client.get_settings", return_value=settings)
    call_openai_mock = mocker.patch("commit_sage.llm_client.call_openai", return_value="{}")

    assert call_llm("system", "user") == "{}"
    call_openai_mock.assert_called_once_with("system", "user", model=None, settings=settings)


def test_call_openai_requires_sdk(mocker):
    settings = Settings(_env_file=None, openai_api_key="openai-key")
    mocker.patch("commit_sage.llm_client.openai", None)

    with pytest.raises(LLMError, match="package is not installed"):
        call_openai("system", "user", settings=settings)


def test_call_openai_uses_responses_api(mocker):
    settings = Settings(
        _env_file=None,
        openai_api_key="openai-key",
        openai_base_url="https://example.test/v1",
        commit_sage_model="gpt-5",
    )
    response = SimpleNamespace(output_text='{"commit_type":"chore","subject":"update files"}')
    create = mocker.Mock(return_value=response)
    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    openai_module = SimpleNamespace(OpenAI=mocker.Mock(return_value=client))
    mocker.patch("commit_sage.llm_client.openai", openai_module)

    assert call_openai("system prompt", "user prompt", settings=settings) == response.output_text
    openai_module.OpenAI.assert_called_once_with(
        api_key="openai-key",
        base_url="https://example.test/v1",
    )
    create.assert_called_once_with(
        model="gpt-5",
        input=[
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "user prompt"},
        ],
    )
