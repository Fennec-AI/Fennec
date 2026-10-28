# Changelog

All notable changes to Fennec will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Prefer Go security tools in the Kali image's PATH so Python's unrelated `httpx` console script cannot shadow ProjectDiscovery's `httpx`.

## [0.2.0] - 2026-06-30

### Added
- Interactive terminal dashboard (`cli/interactive.py`) that mirrors the web Live Activity panel over the same SSE event stream
- `FENNEC_DEMO_SEED` demo mode with a populated dashboard for screenshots and evaluation
- Per-agent model overrides via `RECON_LLM_MODEL` / `ANALYST_LLM_MODEL` / `PENTESTER_LLM_MODEL`
- GitHub Actions CI (ruff + Python tests + frontend build), issue/PR templates, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- README badges and a Status & roadmap section; ESLint config for the frontend
- `pip install -e .[test]` extra and a `[tool.ruff]` config

### Changed
- Default model is now `claude-sonnet-4-6` (was `claude-sonnet-4-20250514`)
- Reports now default to `./reports/<timestamp>_<host>/`, matching the docs
- Search is backed by `ddgs` (the maintained successor to `duckduckgo-search`)
- Hardened recon / analyst / pentester structured-output extraction from end-to-end runs

### Removed
- Leftover hosted-SaaS funnel assets (sitemap, robots, email-confirmation page) and ~7 MB of unused marketing media baked into the frontend image
- Stale Cloud Run / `*.run.app` API URLs from the OSS build

### Fixed
- `docker compose up`: slim backend image and correct frontend port
- Broken README clone URL and in-page CLI anchor
- `pytest` no longer aborts on collection (dropped a test importing a module not shipped in OSS)

## [0.1.0] - 2026-05-14

### Added
- Multi-agent pentest loop: Recon → Analyst → Pentester → Coder, with a pure-routing Orchestrator
- CLI entrypoint (`python cli.py --target URL`)
- Programmatic interface (`agent.run_pentest(task)`)
- FastAPI server (`src/api/server.py`) exposing scan lifecycle, job state, SSE event stream, target/credential CRUD, dashboard aggregations
- React + Vite dashboard (`frontend/`) — talks to the FastAPI server over HTTP + SSE
- Kali Linux execution container (built locally via `linux/Dockerfile`)
- Provider-agnostic LLM config (Anthropic, OpenAI, OpenRouter)
- Human-In-The-Loop (HTLI) mode for operator approval gates
- Per-method presets: `turbo`, `balanced`, `deep`
- JSON + Markdown report generation under `./reports/<timestamp>_<host>/`
- Optional Tavily / Perplexity integration for enhanced recon search

[Unreleased]: https://github.com/Fennec-AI/Fennec/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Fennec-AI/Fennec/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Fennec-AI/Fennec/releases/tag/v0.1.0
