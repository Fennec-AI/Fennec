"""
Configuration settings using pydantic-settings.
"""

import logging
import os
from functools import lru_cache
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into os.environ so validators and get_default_llm() work
# regardless of how the app is launched (CLI, API, LangGraph Studio).
load_dotenv()

logger = logging.getLogger(__name__)


# Model used when LLM_MODEL is not set, per provider.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4.1",
    "openrouter": "anthropic/claude-sonnet-4.6",
    "gemini": "gemini-2.5-pro",
    "nvidia": "meta/llama-3.3-70b-instruct",
}
PROVIDERS = tuple(DEFAULT_MODELS)


class FennecConfig(BaseSettings):
    """Fennec AI configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="FENNEC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: Literal["anthropic", "openai", "openrouter", "gemini", "nvidia"] = "anthropic"
    # Empty → per-provider default from DEFAULT_MODELS (see get_llm_model).
    llm_model: str = Field(default="", validate_default=True)
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    @field_validator("llm_provider", mode="before")
    @classmethod
    def get_llm_provider(cls, v):
        # Prioritize env var without prefix
        env_val = os.environ.get("LLM_PROVIDER")
        if env_val:
            return env_val
        return v or "anthropic"

    @field_validator("llm_model", mode="before")
    @classmethod
    def get_llm_model(cls, v, info: ValidationInfo):
        # Prioritize env var without prefix
        env_val = os.environ.get("LLM_MODEL")
        if env_val:
            return env_val
        if v:
            return v
        return DEFAULT_MODELS.get(info.data.get("llm_provider"), "claude-sonnet-4-6")

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def get_openrouter_key(cls, v):
        # Prioritize env var without prefix
        env_val = os.environ.get("OPENROUTER_API_KEY")
        if env_val:
            return env_val
        return v

    # Fallback chain: comma-separated model specs tried in order when the
    # primary model errors (rate limit, outage, timeout...). Each entry is
    # "provider:model" or just "provider" (uses that provider's default model),
    # e.g. LLM_FALLBACKS=gemini,nvidia:meta/llama-3.3-70b-instruct
    llm_fallbacks: str = ""

    @field_validator("llm_fallbacks", mode="before")
    @classmethod
    def get_llm_fallbacks(cls, v):
        return os.environ.get("LLM_FALLBACKS") or v or ""

    # Per-agent model overrides (fall back to llm_model if not set).
    # They accept the same "provider:model" spec, so each agent can run on a
    # different provider than LLM_PROVIDER.
    recon_llm_model: Optional[str] = None
    analyst_llm_model: Optional[str] = None
    pentester_llm_model: Optional[str] = None

    @field_validator("recon_llm_model", mode="before")
    @classmethod
    def get_recon_model(cls, v):
        return os.environ.get("RECON_LLM_MODEL") or v or None

    @field_validator("analyst_llm_model", mode="before")
    @classmethod
    def get_analyst_model(cls, v):
        return os.environ.get("ANALYST_LLM_MODEL") or v or None

    @field_validator("pentester_llm_model", mode="before")
    @classmethod
    def get_pentester_model(cls, v):
        return os.environ.get("PENTESTER_LLM_MODEL") or v or None

    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    # Hard timeout (seconds) for LLM API calls. Prevents hangs on slow/partial responses.
    llm_timeout: int = 60
    # Provider/client-level retries for transient failures.
    llm_max_retries: int = 2

    # Durable local history for finding chat (relative to the API working directory).
    chat_db_path: str = "data/finding_chats.sqlite3"

    # API Keys - also read from standard env vars
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    # NVIDIA API catalog (build.nvidia.com); point at your own NIM to self-host.
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def get_anthropic_key(cls, v):
        return v or os.environ.get("ANTHROPIC_API_KEY")

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def get_openai_key(cls, v):
        return v or os.environ.get("OPENAI_API_KEY")

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def get_gemini_key(cls, v):
        # GOOGLE_API_KEY is the name the Google GenAI SDK itself falls back to.
        return v or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    @field_validator("nvidia_api_key", mode="before")
    @classmethod
    def get_nvidia_key(cls, v):
        return v or os.environ.get("NVIDIA_API_KEY")

    @field_validator("nvidia_base_url", mode="before")
    @classmethod
    def get_nvidia_base_url(cls, v):
        return os.environ.get("NVIDIA_BASE_URL") or v

    def provider_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """API key for ``provider`` (default: ``llm_provider``); None if unset."""
        return {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "openrouter": self.openrouter_api_key,
            "gemini": self.gemini_api_key,
            "nvidia": self.nvidia_api_key,
        }.get(provider or self.llm_provider)

    def missing_api_keys(self) -> list[str]:
        """Providers required by LLM_PROVIDER / per-agent overrides that have
        no API key. Fallbacks are optional and skipped when unconfigured."""
        specs = [self.llm_model, self.recon_llm_model, self.analyst_llm_model, self.pentester_llm_model]
        needed = {parse_model_spec(s, self.llm_provider)[0] for s in specs if s}
        return sorted(p for p in needed if not self.provider_api_key(p))

    def configured_providers(self) -> list[str]:
        """Providers that have an API key set (any number can be set at once)."""
        return [p for p in PROVIDERS if self.provider_api_key(p)]

    # Search API Keys
    tavily_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cx_key: Optional[str] = None
    searxng_url: Optional[str] = None

    # Docker Configuration
    docker_image: str = "fennec-linux" # kalilinux/kali-rolling:latest
    docker_network: str = "bridge"
    docker_memory_limit: str = "2g"
    docker_cpu_limit: float = 1.0

    # Timeouts
    command_timeout: int = 300  # 5 minutes
    search_timeout: int = 30

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Memory
    embedding_model: str = "text-embedding-3-small"
    memory_score_threshold: float = 0.2


# Assessment method presets (Turbo / Balanced / Deep)
METHOD_PRESETS = {
    "turbo": {
        "recon_model_calls": 10,
        "analyst_model_calls": 8,
        "pentester_model_calls": 15,
        "task_timeout": 1800,       # 30 minutes
        "recursion_limit": 150,
    },
    "balanced": {
        "recon_model_calls": 15,
        "analyst_model_calls": 15,
        "pentester_model_calls": 30,
        "task_timeout": 3600,       # 1 hour
        "recursion_limit": 300,
    },
    "deep": {
        "recon_model_calls": 25,
        "analyst_model_calls": 25,
        "pentester_model_calls": 60,
        "task_timeout": 7200,       # 2 hours
        "recursion_limit": 600,
    },
}


def get_method_preset(method: str) -> dict:
    """Get configuration preset for an assessment method."""
    return METHOD_PRESETS.get(method, METHOD_PRESETS["balanced"])


@lru_cache
def get_config() -> FennecConfig:
    """Get cached configuration instance."""
    return FennecConfig()


_llm_instance = None
_docker_session = None  # {"docker_client": ..., "container_id": ...}


def get_default_llm():
    """Create an LLM from config settings.

    Used as a fallback when the LLM isn't injected into RunnableConfig
    (e.g. when running from LangGraph Studio).
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = create_llm(get_config().llm_model)
    return _llm_instance


def parse_model_spec(spec: str, default_provider: Optional[str] = None) -> tuple[str, str]:
    """Split a model spec into ``(provider, model)``.

    ``"gemini:gemini-2.5-flash"`` -> ``("gemini", "gemini-2.5-flash")``;
    ``"nvidia"`` -> ``("nvidia", <its default model>)``; anything else is a
    bare model name for ``LLM_PROVIDER``. Only a known provider name counts as
    a prefix, so OpenRouter ids like ``"mistralai/mistral-7b:free"`` stay intact.
    """
    spec = spec.strip()
    if spec in PROVIDERS:
        return spec, DEFAULT_MODELS[spec]
    prefix, sep, rest = spec.partition(":")
    if sep and prefix in PROVIDERS and rest:
        return prefix, rest
    return default_provider or get_config().llm_provider, spec


def create_llm(spec: str):
    """Create a chat model from a model spec (see ``parse_model_spec``).

    Single factory for every provider; used for the default LLM, the CLI,
    per-agent overrides and the fallback chain.
    """
    config = get_config()
    provider, model = parse_model_spec(spec)
    api_key = config.provider_api_key(provider)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=config.llm_temperature,
            max_output_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
        )

    # openai, openrouter and nvidia all speak the OpenAI chat-completions API.
    from langchain_openai import ChatOpenAI
    extra: dict = {}
    if provider == "openrouter":
        extra = {
            "base_url": config.openrouter_base_url,
            "default_headers": {
                "HTTP-Referer": "https://fennec.ai",
                "X-Title": "Fennec AI",
            },
        }
    elif provider == "nvidia":
        extra = {"base_url": config.nvidia_base_url}
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
        timeout=config.llm_timeout,
        max_retries=config.llm_max_retries,
        **extra,
    )


def get_fallback_llms(max_tokens: Optional[int] = None) -> list:
    """Chat models from ``LLM_FALLBACKS``, in order.

    Entries whose provider has no API key are skipped with a warning, so a
    half-configured chain degrades instead of crashing the run.
    """
    config = get_config()
    models = []
    for spec in filter(None, (x.strip() for x in config.llm_fallbacks.split(","))):
        provider, _ = parse_model_spec(spec)
        if not config.provider_api_key(provider):
            logger.warning("Skipping LLM fallback %r: no API key for %s", spec, provider)
            continue
        llm = create_llm(spec)
        models.append(with_max_tokens(llm, max_tokens) if max_tokens else llm)
    return models


def fallback_middleware(max_tokens: Optional[int] = None) -> list:
    """``[ModelFallbackMiddleware]`` for ``create_agent``, or ``[]`` when no
    fallbacks are configured. Splat it at the end of an agent's middleware."""
    fallbacks = get_fallback_llms(max_tokens)
    if not fallbacks:
        return []
    from langchain.agents.middleware import ModelFallbackMiddleware
    return [ModelFallbackMiddleware(*fallbacks)]


def structured_llm(llm, schema, max_tokens: int = 16384, **kwargs):
    """``llm.with_structured_output(schema, **kwargs)`` with a raised token cap,
    falling back through ``LLM_FALLBACKS`` if the primary call raises."""
    primary = with_max_tokens(llm, max_tokens).with_structured_output(schema, **kwargs)
    fallbacks = [
        fb.with_structured_output(schema, **kwargs)
        for fb in get_fallback_llms(max_tokens)
    ]
    return primary.with_fallbacks(fallbacks) if fallbacks else primary


def with_max_tokens(llm, max_tokens: int):
    """Return a copy of ``llm`` with a larger output-token cap.

    Uses ``model_copy`` (not ``.bind()``) so the value survives
    ``with_structured_output()`` / ToolStrategy re-binding tools. The field is
    ``max_tokens`` on Anthropic/OpenAI but ``max_output_tokens`` on Gemini, so
    pick whichever the model class defines. Returns ``llm`` unchanged when it
    can't be copied (older LangChain / non-pydantic models).
    """
    fields = getattr(type(llm), "model_fields", {})
    field = "max_output_tokens" if "max_output_tokens" in fields else "max_tokens"
    try:
        return llm.model_copy(update={field: max_tokens})
    except Exception:  # pragma: no cover
        return llm


async def get_default_docker() -> dict:
    """Get or create a shared Docker session (client + container).

    Used as a fallback when docker_client/container_id aren't injected
    into RunnableConfig (e.g. when running from LangGraph Studio).

    Returns dict with 'docker_client' and 'container_id'.
    """
    global _docker_session
    if _docker_session is not None:
        return _docker_session

    from ..docker.client import DockerClient, ContainerConfig
    import uuid

    config = get_config()
    client = DockerClient()
    await client.initialize()

    container_config = ContainerConfig(
        image=config.docker_image,
        name=f"fennec-studio-{uuid.uuid4().hex[:8]}",
    )
    container_id = await client.spawn_container(container_config)

    _docker_session = {
        "docker_client": client,
        "container_id": container_id,
    }
    return _docker_session
