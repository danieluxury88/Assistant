import subprocess
from types import SimpleNamespace

import pytest

from commit_sage.config import (
    DEFAULT_MODELS,
    DEFAULT_PROFILE,
    Profile,
    Settings,
    load_profiles,
    resolve_api_key,
    resolve_model,
    resolve_profile,
)
from commit_sage.llm_client import LLMError, call_command, call_llm, call_openai

LOCAL_CONFIG = """
default_profile = "local"

[profiles.local]
provider = "openai"
base_url = "http://127.0.0.1:8081/v1"
model = "qwen3.5-9b"
api_key = "local"

[profiles.claude-sub]
provider = "command"
command = ["claude", "-p", "--model", "{model}"]
model = "haiku"
"""


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(LOCAL_CONFIG)
    return path


def make_settings(config="", **kwargs):
    return Settings(_env_file=None, commit_sage_config=str(config), **kwargs)


def test_builtin_profiles_without_config_file(tmp_path):
    default, profiles = load_profiles(make_settings(tmp_path / "missing.toml"))
    assert default == DEFAULT_PROFILE
    assert {"claude", "openai"} <= set(profiles)


def test_config_file_adds_profiles_and_sets_default(config_file):
    name, profile = resolve_profile(make_settings(config_file))
    assert name == "local"
    assert profile.base_url == "http://127.0.0.1:8081/v1"


def test_explicit_profile_beats_env_and_default(config_file):
    settings = make_settings(config_file, commit_sage_profile="openai")
    assert resolve_profile(settings)[0] == "openai"
    assert resolve_profile(settings, "claude")[0] == "claude"


def test_unknown_profile_lists_available(config_file):
    with pytest.raises(ValueError, match="Available: claude, claude-sub, local, openai"):
        resolve_profile(make_settings(config_file), "nope")


def test_command_profile_requires_command(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[profiles.broken]\nprovider = "command"\n')
    with pytest.raises(ValueError, match="has no 'command'"):
        load_profiles(make_settings(path))


def test_resolve_model_precedence():
    profile = Profile(provider="openai", model="from-profile")
    assert resolve_model(profile, make_settings(), "from-flag") == "from-flag"
    assert resolve_model(profile, make_settings(commit_sage_model="from-env")) == "from-env"
    assert resolve_model(profile, make_settings()) == "from-profile"
    assert resolve_model(Profile(provider="openai"), make_settings()) == DEFAULT_MODELS["openai"]


def test_resolve_api_key_reads_named_env_var(monkeypatch):
    monkeypatch.setenv("MY_KEY", "secret")
    assert resolve_api_key(Profile(provider="anthropic", api_key_env="MY_KEY")) == "secret"
    assert resolve_api_key(Profile(provider="openai", api_key="local")) == "local"


def test_call_llm_dispatches_by_profile(mocker, config_file):
    mocker.patch("commit_sage.llm_client.get_settings", return_value=make_settings(config_file))
    call_openai_mock = mocker.patch("commit_sage.llm_client.call_openai", return_value="{}")

    assert call_llm("system", "user") == "{}"
    kwargs = call_openai_mock.call_args.kwargs
    assert kwargs["model"] == "qwen3.5-9b"
    assert kwargs["name"] == "local"


def test_call_llm_reports_unknown_profile(mocker, config_file):
    mocker.patch("commit_sage.llm_client.get_settings", return_value=make_settings(config_file))
    with pytest.raises(LLMError, match="Unknown profile"):
        call_llm("system", "user", profile="nope")


def test_call_openai_requires_sdk(mocker):
    mocker.patch("commit_sage.llm_client.openai", None)

    with pytest.raises(LLMError, match="package is not installed"):
        call_openai("system", "user", model="m", profile=Profile(provider="openai", api_key="k"))


def test_call_openai_requires_api_key(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    profile = Profile(provider="openai", api_key_env="MISSING_KEY")
    with pytest.raises(LLMError, match="needs an API key: set MISSING_KEY"):
        call_openai("system", "user", model="m", profile=profile, name="p")


def test_call_openai_uses_responses_api(mocker):
    profile = Profile(provider="openai", api_key="openai-key", base_url="https://example.test/v1")
    response = SimpleNamespace(output_text='{"commit_type":"chore","subject":"update files"}')
    create = mocker.Mock(return_value=response)
    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    openai_module = SimpleNamespace(OpenAI=mocker.Mock(return_value=client))
    mocker.patch("commit_sage.llm_client.openai", openai_module)

    assert call_openai("system prompt", "user prompt", model="gpt-5", profile=profile) == response.output_text
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


def test_call_command_pipes_prompt_and_substitutes_model(mocker):
    run = mocker.patch(
        "commit_sage.llm_client.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, stdout='{"subject":"x"}', stderr=""),
    )
    profile = Profile(provider="command", command=["claude", "-p", "--model", "{model}"])

    assert call_command("system", "user", model="haiku", profile=profile) == '{"subject":"x"}'
    assert run.call_args.args[0] == ["claude", "-p", "--model", "haiku"]
    assert run.call_args.kwargs["input"] == "system\n\nuser"


def test_call_command_reports_failure(mocker):
    mocker.patch(
        "commit_sage.llm_client.subprocess.run",
        return_value=subprocess.CompletedProcess([], 2, stdout="", stderr="not logged in"),
    )
    profile = Profile(provider="command", command=["claude", "-p"])
    with pytest.raises(LLMError, match="exited with 2: not logged in"):
        call_command("system", "user", model=None, profile=profile, name="sub")


def test_call_command_missing_binary():
    profile = Profile(provider="command", command=["definitely-not-a-real-binary-xyz"])
    with pytest.raises(LLMError, match="command not found"):
        call_command("system", "user", model=None, profile=profile, name="sub")
