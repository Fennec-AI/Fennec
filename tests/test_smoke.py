"""Offline smoke tests.

These run without network access, Docker, or any LLM API key — they exercise
the import graph, the LangGraph build, and a couple of stable defaults so a
fresh clone gets a green `pytest` out of the box.
"""

import importlib

import pytest


def test_role_based_graph_compiles():
    """The full agent graph wires up and compiles."""
    from src.graph.role_based_graph import compile_role_based_graph

    assert compile_role_based_graph() is not None


def test_default_model_is_current_sonnet():
    """The shipped default model is the current Claude Sonnet 4.6.

    Checked against the defaults table directly so a local .env can't skew it.
    """
    from src.config.settings import DEFAULT_MODELS, FennecConfig

    assert FennecConfig.model_fields["llm_provider"].default == "anthropic"
    assert DEFAULT_MODELS["anthropic"] == "claude-sonnet-4-6"


def test_gemini_provider_builds_offline(monkeypatch):
    """LLM_PROVIDER=gemini picks a Gemini default model and builds a client
    whose output-token cap can be raised (it's ``max_output_tokens`` there)."""
    from src.config import settings

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    settings.get_config.cache_clear()
    try:
        cfg = settings.get_config()
        assert cfg.llm_model == settings.DEFAULT_MODELS["gemini"]
        assert cfg.provider_api_key() == "test-key"

        llm = settings.create_llm(cfg.llm_model)
        assert type(llm).__name__ == "ChatGoogleGenerativeAI"
        assert settings.with_max_tokens(llm, 16384).max_output_tokens == 16384
    finally:
        settings.get_config.cache_clear()


@pytest.fixture
def fresh_config(monkeypatch):
    """Isolate LLM env vars and the cached config for one test."""
    from src.config import settings

    for var in (
        "LLM_PROVIDER", "LLM_MODEL", "LLM_FALLBACKS", "RECON_LLM_MODEL",
        "ANALYST_LLM_MODEL", "PENTESTER_LLM_MODEL", "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
        "GOOGLE_API_KEY", "NVIDIA_API_KEY", "NVIDIA_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    settings.get_config.cache_clear()
    yield settings
    settings.get_config.cache_clear()


def test_model_spec_parsing(fresh_config):
    settings = fresh_config
    assert settings.parse_model_spec("gemini:gemini-2.5-pro") == ("gemini", "gemini-2.5-pro")
    assert settings.parse_model_spec("nvidia") == ("nvidia", settings.DEFAULT_MODELS["nvidia"])
    assert settings.parse_model_spec("nvidia:meta/llama-3.3-70b-instruct") == ("nvidia", "meta/llama-3.3-70b-instruct")
    # Unknown prefixes are part of the model id (OpenRouter ":free" variants).
    assert settings.parse_model_spec("mistralai/mistral-7b:free", "openrouter") == ("openrouter", "mistralai/mistral-7b:free")


def test_nvidia_provider_builds_offline(fresh_config, monkeypatch):
    settings = fresh_config
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    cfg = settings.get_config()
    llm = settings.create_llm(cfg.llm_model)
    assert type(llm).__name__ == "ChatOpenAI"
    assert llm.model_name == settings.DEFAULT_MODELS["nvidia"]
    assert "integrate.api.nvidia.com" in str(llm.openai_api_base)


def test_multiple_providers_and_fallbacks(fresh_config, monkeypatch):
    """Several keys can be set at once; fallbacks without a key are skipped
    and per-agent overrides on another provider are checked by preflight."""
    settings = fresh_config
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("LLM_FALLBACKS", "gemini:gemini-2.5-pro, nvidia, openai")
    monkeypatch.setenv("RECON_LLM_MODEL", "nvidia:meta/llama-3.3-70b-instruct")
    cfg = settings.get_config()

    assert cfg.configured_providers() == ["anthropic", "gemini"]
    assert cfg.missing_api_keys() == ["nvidia"]

    fallbacks = settings.get_fallback_llms(16384)
    assert [type(m).__name__ for m in fallbacks] == ["ChatGoogleGenerativeAI"]
    assert fallbacks[0].max_output_tokens == 16384
    assert len(settings.fallback_middleware()) == 1


@pytest.mark.parametrize(
    "module",
    [
        "src.agents.recon",
        "src.agents.analyst",
        "src.agents.pentester",
        "src.agents.coder",
        "src.tools.hypothesis_tools",
        "src.api.server",
        "src.api.demo_seed",
    ],
)
def test_key_modules_import(module):
    """Core modules import cleanly (guards the try/except import fallbacks)."""
    assert importlib.import_module(module) is not None
