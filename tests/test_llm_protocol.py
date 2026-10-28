"""Offline model factory regressions: real SDK requests, no external API calls."""

import json
import os
from unittest.mock import Mock

import httpx
import pytest
from pydantic import ValidationError

from src.config import settings


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch):
    get_config = settings.get_config
    for name in list(os.environ):
        if name.startswith(("FENNEC_", "LLM_", "OPENAI_", "OPENROUTER_")):
            monkeypatch.delenv(name)
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    get_config.cache_clear()
    monkeypatch.setattr(settings, "_llm_instance", None)
    yield
    get_config.cache_clear()


@pytest.mark.parametrize("provider", ["openai", "openrouter"])
@pytest.mark.parametrize("factory", ["default", "override"])
@pytest.mark.parametrize("protocol", [None, False, True])
def test_factories_route_tool_calls(provider, factory, protocol, monkeypatch):
    from langchain_openai import ChatOpenAI

    config = settings.FennecConfig(
        _env_file=None,
        llm_provider=provider,
        llm_model="default-model",
        llm_use_responses_api=protocol,
        openai_api_key="offline-test-key",
        openrouter_api_key="offline-test-key",
        openrouter_base_url="https://gateway.invalid/v1",
    )
    monkeypatch.setattr(settings, "get_config", lambda: config)
    requests = []
    expected_model = "default-model" if factory == "default" else "agent-model"

    def respond(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["model"] == expected_model
        assert body["tools"]
        if protocol is True:
            assert request.url.path == "/v1/responses"
            return httpx.Response(200, json={
                "id": "resp_offline", "object": "response", "created_at": 1,
                "model": expected_model, "status": "completed",
                "output": [{"type": "function_call", "id": "fc_offline",
                            "call_id": "call_offline", "name": "readiness_probe",
                            "arguments": '{"marker":"READY"}', "status": "completed"}],
                "parallel_tool_calls": True, "tools": [], "tool_choice": "auto",
            })
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={
            "id": "chatcmpl_offline", "object": "chat.completion", "created": 1,
            "model": expected_model,
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None,
                "tool_calls": [{"id": "call_offline", "type": "function", "function": {
                    "name": "readiness_probe", "arguments": '{"marker":"READY"}',
                }}],
            }}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        async_client = httpx.AsyncClient(transport=httpx.MockTransport(respond))

        def make_model(**kwargs):
            # Use the actual SDK/serializer while replacing its HTTP transport only.
            return ChatOpenAI(**kwargs, http_client=client, http_async_client=async_client)

        monkeypatch.setattr("langchain_openai.ChatOpenAI", make_model)
        model = (settings.get_default_llm() if factory == "default"
                 else settings.create_llm("agent-model"))
        assert model.use_responses_api is protocol
        tool = {"type": "function", "function": {
            "name": "readiness_probe", "description": "Return a fixed test marker.",
            "parameters": {"type": "object", "properties": {"marker": {"type": "string"}},
                           "required": ["marker"]},
        }}
        result = model.bind_tools([tool]).invoke("Return the fixed readiness marker.")

    assert len(requests) == 1
    assert result.tool_calls[0]["name"] == "readiness_probe"
    assert result.tool_calls[0]["args"] == {"marker": "READY"}
    if provider == "openrouter":
        assert requests[0].url.host == "gateway.invalid"
        assert requests[0].headers["X-Title"] == "Fennec AI"


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False)])
def test_environment_protocol_selection(value, expected, monkeypatch):
    monkeypatch.setenv("FENNEC_LLM_USE_RESPONSES_API", value)
    assert settings.FennecConfig(_env_file=None).llm_use_responses_api is expected


def test_unset_protocol_preserves_auto_selection():
    assert settings.FennecConfig(_env_file=None).llm_use_responses_api is None


def test_invalid_protocol_is_rejected(monkeypatch):
    monkeypatch.setenv("FENNEC_LLM_USE_RESPONSES_API", "not-a-boolean")
    with pytest.raises(ValidationError):
        settings.FennecConfig(_env_file=None)


@pytest.mark.parametrize("factory", ["default", "override"])
def test_responses_option_is_not_passed_to_anthropic(factory, monkeypatch):
    config = settings.FennecConfig(_env_file=None, llm_provider="anthropic",
                                 llm_use_responses_api=True,
                                 anthropic_api_key="offline-test-key")
    monkeypatch.setattr(settings, "get_config", lambda: config)
    constructor = Mock()
    monkeypatch.setattr("langchain_anthropic.ChatAnthropic", constructor)
    if factory == "default":
        settings.get_default_llm()
    else:
        settings.create_llm("agent-model")
    assert "use_responses_api" not in constructor.call_args.kwargs
